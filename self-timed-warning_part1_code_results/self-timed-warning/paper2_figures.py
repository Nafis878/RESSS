"""Figures 2-6 of the warning-model manuscript (Fig. 1 = fig_stw_architecture.py). Vector PDF + 1000-dpi PNG."""
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import eol_window2 as W
from safe_common import load_dataset, outer_folds
from feats import regime_stats, zmat, causal_feats
plt.rcParams.update({'font.family': 'Liberation Sans', 'font.size': 7.5, 'pdf.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False})
N = json.load(open('paper2/numbers.json')); OUT = 'out/paper2_figs'
BLUE, ORANGE, GREEN, PINK, GREY, PURPLE, INK = '#2a78d6', '#eb6834', '#1baf7a', '#e87ba4', '#8a8a8a', '#6b4bb3', '#1a1a1a'
def save(fig, name):
    fig.savefig(f'{OUT}/{name}.pdf', facecolor='white'); fig.savefig(f'{OUT}/{name}.png', dpi=1000, facecolor='white'); plt.close(fig)
def grid(ax): ax.grid(alpha=.25, lw=.5, axis='y')

# ---------- Fig 2: fixed-time prediction vs self-timed warning (PHM08)
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.7), gridspec_kw=dict(width_ratios=[1, 1.35]))
ff = N['fixed_fraction']; fr = [30, 50, 70, 90]
for m, lab, c, mk in (('gbm', 'Gradient-boosted trees', BLUE, 'o'), ('lstm', 'LSTM', ORANGE, 's'), ('cnn', 'CNN', GREEN, 'D'), ('age', 'Age only', PINK, 'v')):
    a.plot(fr, [ff[m][str(f / 100)] for f in fr], color=c, marker=mk, ms=3.5, lw=1.3, label=lab)
w20 = N['cv']['PHM08']['20']; a.axhline(w20['pct'], color=INK, ls='--', lw=1)
a.text(31, w20['pct'] - 6, f"self-timed warning (H = 20): {w20['pct']}%", fontsize=7, color=INK)
a.set_xticks(fr); a.set_xlabel('Life observed when the prediction is made (%)'); a.set_ylabel('Predictions with error in [-13, +2] (%)'); a.set_ylim(0, 100)
a.set_title('(a) Fixed-time prediction, PHM08 (218 engines)', loc='left', fontsize=8); a.legend(frameon=False, fontsize=6.5, loc='center left', bbox_to_anchor=(0, 0.6)); grid(a)
H = N['half']; items = [('Age only', H['single']['age']), ('IOHMM', H['single']['iohmm']), ('Similarity', H['single']['sim']), ('Gradient-boosted trees', H['single']['gbm']),
                        ('TCN', H['tcn']), ('TCN + GAN augmentation', H['tcn_gan']), ('Hybrid Transformer', H['single']['tf_q50']), ('CNN', H['single']['cnn']),
                        ('Physics-informed Bayesian', H['single']['bayes_q50']), ('LSTM', H['single']['lstm']), ('Stacked hybrid (10 base models)', H['hybrid'])]
items = sorted(items, key=lambda x: x[1]['pct'])
b.barh(range(len(items)), [x[1]['pct'] for x in items], color=[PURPLE if 'Stacked' in x[0] else BLUE for x in items], height=0.62)
for i, (n_, v) in enumerate(items): b.text(v['pct'] + 1, i, f"{v['pct']}%", va='center', fontsize=6.5)
b.set_yticks(range(len(items))); b.set_yticklabels([x[0] for x in items], fontsize=6.8); b.set_xlim(0, 100)
b.axvline(w20['pct'], color=INK, ls='--', lw=1); b.set_xlabel('Predictions with error in [-13, +2] at half of life (%)')
b.set_title('(b) Eleven reference models at half of life, PHM08', loc='left', fontsize=8); b.grid(alpha=.25, lw=.5, axis='x')
fig.tight_layout(w_pad=1.5); save(fig, 'Fig2_fixed_time_ceiling')

# ---------- Fig 3: real engines (PHM08), settings of their own fold at H = 20
A = pd.read_csv('out/window/first_warning_v2_PHM08.csv'); A20 = A[A.H == 20]
picks = [('IN', 1), ('EARLY', int(A20[A20.cls == 'EARLY'].sort_values('unit').unit.iloc[0])), ('LATE', int(A20[A20.cls == 'LATE'].sort_values('unit').unit.iloc[0]))]
tr, _, _ = load_dataset('PHM08'); units = np.sort(tr.unit.unique()); folds = outer_folds(units)
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.35), sharey=True)
for ax, (cls, u) in zip(axs, picks):
    row = A20[A20.unit == u].iloc[0]; k_ = int(row.fold); test_u = folds[k_ - 1]; train_u = np.setdiff1d(units, test_u)
    st, keep = regime_stats(tr[tr.unit.isin(train_u)])
    X = np.vstack([causal_feats(zmat(g, st, keep)) for _, g in tr[tr.unit.isin(train_u)].groupby('unit')]); y = np.concatenate([g.rul.values for _, g in tr[tr.unit.isin(train_u)].groupby('unit')])
    m = W.gbm(X, y, int(row.cap)); g = tr[tr.unit == u]; p = W.smooth(m.predict(causal_feats(zmat(g, st, keep)))[:-1], int(row.span)) + row['shift']
    yt = g.rul.values[:-1]; cyc = g.cycle.values[:-1]; wp, wy, wc = W.warn(p, yt, 20, int(row.k))
    assert abs(wp - row.pred) < 1e-6 and wy == row.y, (u, wp, row.pred)
    ax.plot(cyc, yt, color=INK, lw=1.2, label='True cycles left'); ax.plot(cyc, np.clip(p, 0, None), color=BLUE, lw=1.2, label='Calibrated prediction')
    ax.axhline(20, color=ORANGE, ls='--', lw=0.9); ax.fill_between([wc - 0.5, wc + 0.5], 0, 60, color='#dddddd')
    ax.plot([wc], [wp], 'o', color=GREEN if cls == 'IN' else '#b3261e', ms=5, zorder=5)
    ax.text(0.03, 0.95, f"engine {u}: warning at cycle {int(wc)}\npredicted {wp:.1f}, true {wy:.0f}, error {wp - wy:+.1f}\n-> {'inside window' if cls == 'IN' else ('too early' if cls == 'EARLY' else 'too late')}",
            transform=ax.transAxes, va='top', fontsize=6.4, color=GREEN if cls == 'IN' else '#b3261e', bbox=dict(fc='white', ec='none', alpha=0.9, pad=1.5))
    ax.set_xlim(max(0, cyc[-1] - 90), cyc[-1] + 2); ax.set_ylim(0, 60); ax.set_xlabel('Flight cycle'); grid(ax)
axs[0].set_ylabel('Cycles left'); axs[0].legend(frameon=False, fontsize=6.3, loc='lower left')
fig.tight_layout(w_pad=0.8); save(fig, 'Fig3_example_engines')

# ---------- Fig 4: in-window rate vs warning level
fig, ax = plt.subplots(figsize=(3.5, 2.6))
sty = {'PHM08': (INK, 'o'), 'FD001': (BLUE, 's'), 'FD002': (ORANGE, '^'), 'FD003': (GREEN, 'D'), 'FD004': (PINK, 'v')}
for ds, (c, mk) in sty.items():
    Hs = sorted(int(h) for h in N['cv'][ds] if h.isdigit()); ax.plot(Hs, [N['cv'][ds][str(h)]['pct'] for h in Hs], color=c, marker=mk, ms=3.5, lw=1.2, label=ds)
nc = [s for s in N['ncm']['summary'] if s['split'].startswith('cv') and s['method'] == 'warning']; nc = sorted(nc, key=lambda s: s['H'])
ax.errorbar([s['H'] for s in nc], [s['pct'] for s in nc], yerr=[[s['pct'] - s['ci'][0] for s in nc], [s['ci'][1] - s['pct'] for s in nc]], color=PURPLE, marker='P', ms=4,
            lw=1.2, capsize=2, label='N-CMAPSS (pre-specified)')
ax.set_xlabel('Warning level H (predicted cycles left)'); ax.set_ylabel('First warnings with error in [-13, +2] (%)'); ax.set_ylim(40, 100); ax.set_xticks([10, 15, 20, 30, 40]); grid(ax)
ax.legend(frameon=False, fontsize=6.2, loc='lower right'); fig.tight_layout(); save(fig, 'Fig4_level_tradeoff')

# ---------- Fig 5: error and lead-time distributions at H = 20
NC = pd.read_csv('out/ncm/warning_results.csv'); NC = NC[NC.primary & (NC.method == 'warning') & (NC.H == 20)].dropna(subset=['pred'])
P = A20.dropna(subset=['pred'])
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.4))
bins = np.arange(-30, 16, 1.5)
a.axvspan(-13, 2, color='#e3f2e3', zorder=0)
a.hist(P.pred - P.y, bins=bins, color=BLUE, alpha=.75, label=f'PHM08 (n = {len(P)})', density=True)
a.hist(NC.pred - NC.y, bins=bins, histtype='step', color=PURPLE, lw=1.3, label=f'N-CMAPSS (n = {len(NC)} warnings)', density=True)
a.set_xlabel('Error at the warning, predicted - true cycles left'); a.set_ylabel('Density'); a.legend(frameon=False, fontsize=6.5); a.set_title('(a) Error at the first warning (H = 20)', loc='left', fontsize=8)
b.hist(P.y, bins=np.arange(0, 60, 2.5), color=BLUE, alpha=.75, density=True, label='PHM08'); b.hist(NC.y, bins=np.arange(0, 60, 2.5), histtype='step', color=PURPLE, lw=1.3, density=True, label='N-CMAPSS')
b.axvline(13, color=GREY, ls=':', lw=1); b.annotate('left of this line the early\nlimit practically cannot bind', xy=(13, b.get_ylim()[1] * 0.75), xytext=(33, b.get_ylim()[1] * 0.62), fontsize=6.2, color=GREY, arrowprops=dict(arrowstyle='-|>', color=GREY, lw=0.7))
b.set_xlabel('True cycles left when the warning is issued'); b.set_title('(b) Lead time of the first warning (H = 20)', loc='left', fontsize=8); b.legend(frameon=False, fontsize=6.5, loc='upper right', bbox_to_anchor=(1, 1))
fig.tight_layout(w_pad=1.5); save(fig, 'Fig5_error_leadtime')

# ---------- Fig 6: head-to-head (PHM08) and component ablation
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.0), gridspec_kw=dict(width_ratios=[1, 1.25]))
meths = [('ours', 'Self-timed warning (ours)', BLUE), ('mlp_kf', 'MLP + Kalman (Peel-style)', ORANGE), ('rnn', 'LSTM (Heimes-style)', GREEN),
         ('similarity', 'Similarity (Wang-style)', PINK), ('cnn', 'CNN', GREY)]
src = {m: N['h2h'] for m, _, _ in meths}
if 'dl' in N:
    meths += [('lstm15', 'LSTM, same inputs as ours', '#8fd3b8'), ('cnn15', 'CNN, same inputs as ours', '#c9c9c9'), ('tf15', 'Transformer, same inputs as ours', PURPLE)]
    src.update({m: N['dl'] for m in ('lstm15', 'cnn15', 'tf15')})
x = np.arange(2); wdt = 0.8 / len(meths)
for i, (m, lab, c) in enumerate(meths):
    v = [src[m][f'{m}|{H}'] for H in (10, 20)]
    a.bar(x + (i - (len(meths) - 1) / 2) * wdt, [s['pct'] for s in v], wdt, color=c, label=lab, yerr=[[s['pct'] - s['ci'][0] for s in v], [s['ci'][1] - s['pct'] for s in v]], capsize=1.2, error_kw=dict(lw=0.5))
a.set_xticks(x); a.set_xticklabels(['H = 10', 'H = 20']); a.set_ylim(0, 100); a.set_ylabel('First warnings in [-13, +2] (%)'); grid(a)
a.set_title('(a) Identical protocol, PHM08 (218 engines)', loc='left', fontsize=8); a.legend(frameon=False, fontsize=6, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2)
if 'ablation' in N:
    AB = N['ablation']; names = [('full', 'Full model'), ('cap125', 'Target cap 125 (conventional)'), ('uncapped', 'No target cap'), ('no_shift', 'No window centring (s = 0)'),
                                 ('no_debounce', 'No debounce (k = 1)'), ('no_smoothing', 'No smoothing (m = 1)'), ('untuned_rule', 'Untuned decision rule'),
                                 ('sensors7', '7 temperature/speed sensors'), ('sensors_no_age', 'Sensors without age'), ('age_only', 'Age only (no sensors)')]
    vals = [AB[f'{k}|H20']['pct'] for k, _ in names]
    b.barh(range(len(names))[::-1], vals, color=[BLUE if k == 'full' else '#9dbfe8' for k, _ in names], height=0.62)
    for i, v in zip(range(len(names))[::-1], vals): b.text(v + 0.8, i, f'{v}%', va='center', fontsize=6.5)
    b.set_yticks(range(len(names))[::-1]); b.set_yticklabels([n for _, n in names], fontsize=6.6); b.set_xlim(0, 100)
    b.set_xlabel('First warnings in [-13, +2] (%), H = 20'); b.grid(alpha=.25, lw=.5, axis='x'); b.set_title('(b) Component ablation, PHM08', loc='left', fontsize=8)
fig.tight_layout(w_pad=1.2); save(fig, 'Fig6_comparison_ablation')
print('figures written')
