"""TCN and TCN + conditional GAN augmentation (pure JAX / optax) for the [-13, +2] window at half of life.

Same engine-level folds / fit-calibration split as the main study.
  TCN      : causal dilated 1-D convolutions (dilations 1,2,4,8, kernel 3, 32 channels, residual), input = last 40 cycles of
             15 regime-normalised sensors + age channel; outputs 5 monotone quantiles of RUL (pinball loss).
  cGAN     : generator G(noise, RUL, age) -> 40-cycle sensor window; discriminator D(window, RUL, age). Trained on FIT engines only.
  TCN+GAN  : TCN trained on real FIT windows + synthetic windows (50 % extra), labels = conditioning RUL.
  TSTR     : TCN trained on synthetic windows only (checks whether the GAN learned anything real).
Validation (model selection by epoch) uses CALIBRATION engines. Predictions are written for the calibration rows (16 life stages)
and the test rows (half of life) of out/window/base_preds_PHM08.csv so they can enter the stacked hybrid.
"""
import os, sys, time, numpy as np, pandas as pd, jax, jax.numpy as jnp, optax
from safe_common import load_dataset, outer_folds, fit_cal_split
from feats import regime_stats, zmat
W, QS = 40, jnp.array([0.05, 0.25, 0.5, 0.75, 0.95]); SC = 100.0
DS = sys.argv[1] if len(sys.argv) > 1 else 'PHM08'

# ------------------------------------------------------------------ building blocks
def conv(x, w, b, dil=1, causal=True):
    """x: (B, T, C_in), w: (K, C_in, C_out)"""
    K = w.shape[0]; pad = (dil * (K - 1), 0) if causal else ((dil * (K - 1)) // 2, dil * (K - 1) - (dil * (K - 1)) // 2)
    y = jax.lax.conv_general_dilated(x, w, (1,), [pad], rhs_dilation=(dil,), dimension_numbers=('NWC', 'WIO', 'NWC'))
    return y + b

def glorot(k, shape):
    fan = np.prod(shape[:-1]); return jax.random.normal(k, shape) * np.sqrt(2.0 / (fan + shape[-1]))

def init_tcn(k, cin, ch=32, dils=(1, 2, 4, 8)):
    ks = jax.random.split(k, 2 * len(dils) + 4); p = {'in_w': glorot(ks[0], (1, cin, ch)), 'in_b': jnp.zeros(ch), 'blocks': []}
    for i, d in enumerate(dils):
        p['blocks'].append({'w1': glorot(ks[2 * i + 1], (3, ch, ch)), 'b1': jnp.zeros(ch), 'w2': glorot(ks[2 * i + 2], (3, ch, ch)), 'b2': jnp.zeros(ch)})
    p['h_w'] = glorot(ks[-3], (ch, 64)); p['h_b'] = jnp.zeros(64); p['o_w'] = glorot(ks[-2], (64, 5)) * 0.1; p['o_b'] = jnp.array([0.9, -1, -1, -1, -1.0])
    return p

def tcn(p, x, dils=(1, 2, 4, 8)):
    h = conv(x, p['in_w'], p['in_b'])
    for blk, d in zip(p['blocks'], dils):
        r = jax.nn.relu(conv(h, blk['w1'], blk['b1'], d)); r = conv(r, blk['w2'], blk['b2'], d); h = jax.nn.relu(h + r)
    z = jax.nn.gelu(h[:, -1] @ p['h_w'] + p['h_b']); o = z @ p['o_w'] + p['o_b']
    return jnp.concatenate([o[:, :1], o[:, :1] + jnp.cumsum(jax.nn.softplus(o[:, 1:]), 1)], 1)     # monotone quantiles (RUL / 100)

def pinball(p, x, y):
    e = y[:, None] - tcn(p, x); return jnp.mean(jnp.maximum(QS * e, (QS - 1) * e))

def init_G(k, cs, nz=16, ch=32):
    ks = jax.random.split(k, 4)
    return {'d_w': glorot(ks[0], (nz + 2, W * ch)), 'd_b': jnp.zeros(W * ch), 'c1_w': glorot(ks[1], (5, ch, ch)), 'c1_b': jnp.zeros(ch),
            'c2_w': glorot(ks[2], (5, ch, ch)), 'c2_b': jnp.zeros(ch), 'o_w': glorot(ks[3], (1, ch, cs)), 'o_b': jnp.zeros(cs)}

def G(p, z, c):
    h = jax.nn.leaky_relu(jnp.concatenate([z, c], 1) @ p['d_w'] + p['d_b'], 0.2).reshape(len(z), W, -1)
    h = jax.nn.leaky_relu(conv(h, p['c1_w'], p['c1_b'], 1, False), 0.2); h = jax.nn.leaky_relu(conv(h, p['c2_w'], p['c2_b'], 1, False), 0.2)
    return conv(h, p['o_w'], p['o_b'], 1, False)

def init_D(k, cs, ch=32):
    ks = jax.random.split(k, 4)
    return {'c1_w': glorot(ks[0], (5, cs + 2, ch)), 'c1_b': jnp.zeros(ch), 'c2_w': glorot(ks[1], (5, ch, ch)), 'c2_b': jnp.zeros(ch),
            'c3_w': glorot(ks[2], (5, ch, ch)), 'c3_b': jnp.zeros(ch), 'o_w': glorot(ks[3], (2 * ch, 1)), 'o_b': jnp.zeros(1)}

def Dn(p, x, c):
    h = jnp.concatenate([x, jnp.broadcast_to(c[:, None, :], (len(x), W, 2))], 2)
    for i in (1, 2, 3): h = jax.nn.leaky_relu(conv(h, p[f'c{i}_w'], p[f'c{i}_b'], 2 ** (i - 1), False), 0.2)
    return (jnp.concatenate([h.mean(1), h[:, -1]], 1) @ p['o_w'] + p['o_b'])[:, 0]

# ------------------------------------------------------------------ training
def train_gan(Xs, C, key, steps=3000, bs=128):
    cs = Xs.shape[2]; kg, kd, key = jax.random.split(key, 3); pg, pd_ = init_G(kg, cs), init_D(kd, cs)
    og, od = optax.adam(2e-4, 0.5), optax.adam(2e-4, 0.5); sg, sd = og.init(pg), od.init(pd_)
    bce = lambda l, t: jnp.mean(optax.sigmoid_binary_cross_entropy(l, t))
    @jax.jit
    def step(pg, pd_, sg, sd, x, c, z):
        def ld(pd_):
            fake = G(pg, z, c); return bce(Dn(pd_, x, c), jnp.ones(len(x))) + bce(Dn(pd_, fake, c), jnp.zeros(len(x)))
        l1, g = jax.value_and_grad(ld)(pd_); u, sd = od.update(g, sd, pd_); pd_ = optax.apply_updates(pd_, u)
        def lg(pg):
            return bce(Dn(pd_, G(pg, z, c), c), jnp.ones(len(x)))
        l2, g = jax.value_and_grad(lg)(pg); u, sg = og.update(g, sg, pg); pg = optax.apply_updates(pg, u)
        return pg, pd_, sg, sd, l1, l2
    rng = np.random.default_rng(0)
    for s in range(steps):
        i = rng.integers(0, len(Xs), bs); key, kz = jax.random.split(key)
        pg, pd_, sg, sd, l1, l2 = step(pg, pd_, sg, sd, Xs[i], C[i], jax.random.normal(kz, (bs, 16)))
    return pg, float(l1), float(l2)

def train_tcn(X, y, Xv, yv, key, epochs=25, bs=256):
    p = init_tcn(key, X.shape[2]); opt = optax.adam(1e-3); s = opt.init(p)
    @jax.jit
    def step(p, s, x, t):
        l, g = jax.value_and_grad(pinball)(p, x, t); u, s = opt.update(g, s, p); return optax.apply_updates(p, u), s, l
    vloss = jax.jit(pinball); best, bp = np.inf, p; rng = np.random.default_rng(1)
    for ep in range(epochs):
        o = rng.permutation(len(X))
        for j in range(0, len(o) - bs + 1, bs): p, s, _ = step(p, s, X[o[j:j + bs]], y[o[j:j + bs]])
        v = float(np.mean([vloss(p, Xv[j:j + 2048], yv[j:j + 2048]) for j in range(0, len(Xv), 2048)]))
        if v < best: best, bp = v, p
    return bp, best

def windows(S):
    P = np.vstack([np.repeat(S[:1], W - 1, 0), S]); return np.lib.stride_tricks.sliding_window_view(P, (W, S.shape[1]))[:, 0]

def main(ds):
    tr, _, _ = load_dataset(ds); units = np.sort(tr.unit.unique()); B = pd.read_csv(f'out/window/base_preds_{ds}.csv'); outs = []
    for fold, test_u in enumerate(outer_folds(units), 1):
        t0 = time.time(); fit_u, cal_u = fit_cal_split(np.setdiff1d(units, test_u)); st, keep = regime_stats(tr[tr.unit.isin(fit_u)])
        G_ = {u: g for u, g in tr.groupby('unit')}
        E = {}
        for u, g in G_.items():
            S = np.clip(np.nan_to_num(zmat(g, st, keep)), -6, 6).astype('float32'); age = (g.cycle.values / SC).astype('float32')
            E[u] = (windows(S), age, (g.rul.values / SC).astype('float32'))
        def add_age(Xw, a): return np.concatenate([Xw, np.broadcast_to(a[:, None, None], (len(a), W, 1))], 2).astype('float32')
        def mk(us, stride):
            Xw = np.concatenate([E[u][0][::stride] for u in us]); a = np.concatenate([E[u][1][::stride] for u in us]); y = np.concatenate([E[u][2][::stride] for u in us])
            return Xw, a, y
        Xw, a, y = mk(fit_u, 2); Xvw, av, yv = mk(cal_u, 5); Xv = add_age(Xvw, av)
        key = jax.random.PRNGKey(fold)
        # 1) TCN on real data
        p_real, v_real = train_tcn(add_age(Xw, a), y, Xv, yv, key)
        # 2) conditional GAN on FIT windows, conditioned on (RUL, age)
        C = np.column_stack([y, a]).astype('float32'); pg, l_d, l_g = train_gan(jnp.array(Xw), jnp.array(C), key)
        n_syn = len(Xw) // 2; ci = np.random.default_rng(fold).integers(0, len(C), n_syn); Cs = C[ci]
        Xs = np.array(G(pg, jax.random.normal(jax.random.PRNGKey(99 + fold), (n_syn, 16)), jnp.array(Cs)))
        # 3) TCN on real + synthetic, 4) TCN on synthetic only (TSTR)
        p_aug, v_aug = train_tcn(np.concatenate([add_age(Xw, a), add_age(Xs, Cs[:, 1])]), np.concatenate([y, Cs[:, 0]]), Xv, yv, key)
        p_syn, v_syn = train_tcn(add_age(Xs, Cs[:, 1]), Cs[:, 0], Xv, yv, key)
        R = B[B.fold == fold][['fold', 'unit', 'role', 'stage', 't', 'y']].copy()
        Xr = add_age(np.stack([E[u][0][t - 1] for u, t in zip(R.unit, R.t)]), np.array([E[u][1][t - 1] for u, t in zip(R.unit, R.t)]))
        for name, pp in (('tcn', p_real), ('tcngan', p_aug), ('tstr', p_syn)):
            Q = np.array(tcn(pp, jnp.array(Xr))) * SC; R[f'{name}_q05'], R[f'{name}_q50'], R[f'{name}_q95'] = Q[:, 0], Q[:, 2], Q[:, 4]
        outs.append(R); pd.concat(outs).to_csv(f'out/window/tcn_preds_{ds}.csv', index=False)
        real_m, syn_m = Xw.mean((0, 1)), Xs.mean((0, 1)); real_s, syn_s = Xw.std((0, 1)), Xs.std((0, 1))
        print(f'fold {fold} ({time.time()-t0:.0f}s): val pinball real {v_real:.4f} aug {v_aug:.4f} syn-only {v_syn:.4f}; '
              f'GAN losses D {l_d:.2f} G {l_g:.2f}; |mean diff| {np.abs(real_m-syn_m).mean():.3f} std ratio {np.mean(syn_s/real_s):.2f}', flush=True)

if __name__ == '__main__':
    main(DS)
