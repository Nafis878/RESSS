"""Figures of the third revision (vector PDF + 300-dpi PNG in out/paper5_figs/), from paper5/numbers.json and the kam outputs.
FigR3_cost_audit5   cost of window-tuned, cost-tuned and age policies by dataset (battery: fully nested, convention C)
Fig9_battery_cost5  battery cost under cross-validation and with a batch held out, fully nested (convention C)
Fig10_metric_M      comparison with the metric M of Kamariotis et al.: (a) M on FD001 (five-fold) by cost ratio,
                    (b) their Fig. 9a on our data (FD001 fold 1, c_p/c_c = 0.01), (c) test sets with a failure, FD001-FD004
Usage: python fig_rev5.py [--frozen]
"""
import os, sys, json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'Liberation Sans', 'font.size': 7.5, 'pdf.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False})
K_ = 'results/kam' if '--frozen' in sys.argv else 'out/kam'
N = json.load(open('paper5/numbers.json')); R3, R5 = N['rev3'], N['rev5']; OUT = 'out/paper5_figs'; os.makedirs(OUT, exist_ok=True)
BLUE, ORANGE, GREEN, PINK, GREY, PURPLE, INK, LBLUE = '#2a78d6', '#eb6834', '#1baf7a', '#e87ba4', '#8a8a8a', '#6b4bb3', '#1a1a1a', '#9cc3ef'
NAME = {'PHM08': 'PHM08', 'FD001': 'FD001', 'FD002': 'FD002', 'FD003': 'FD003', 'FD004': 'FD004', 'NCMAPSS6': 'N-CMAPSS', 'Battery': 'Battery'}
BN = R5['battery_cost_nested']


def save(fig, name):
    fig.savefig(f'{OUT}/{name}.pdf', facecolor='white'); fig.savefig(f'{OUT}/{name}.png', dpi=300, facecolor='white'); plt.close(fig)


def F_(name):
    for c in (f'{K_}/{name}', f'{K_}/{name}.gz', f'results/kam/{name}', f'results/kam/{name}.gz'):
        if os.path.exists(c): return c
    return None


# ---------------------------------------------------------------- cost figure (as fig_audit.py, battery from the fully nested run)
ds = list(NAME)
pols = [('STW_window', 'STW, window-tuned (H by cost)', PINK, 'o'), ('STW_cost', 'STW, cost-tuned', BLUE, 's'), ('STW_cost_1se', 'STW, cost-tuned, 1-SE rule', LBLUE, 's'),
        ('Q10_cost', '10% quantile alarm, cost-tuned', GREEN, 'D'), ('HI_cost', 'Health-indicator alarm, cost-tuned', ORANGE, '^'), ('age', 'Age replacement', GREY, 'v')]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
for ax, (lc, rho) in zip(axs, ((0, 10), (10, 50))):
    for j, (p, lab, c, mk) in enumerate(pols):
        ys = []
        for d in ds:
            cc = R3['cost'][d].get(f'{lc}|{rho}') if d != 'Battery' else BN['cv123']['cells'].get(f'{lc * 3}|{rho}')
            ys.append(cc[p]['ratio'] if cc and p in cc else np.nan)
        xs = np.arange(len(ds)) + (j - 2.5) * .11; ys = np.array(ys, float); TOP = 2.75
        ax.scatter(xs, np.minimum(ys, TOP - 0.05), color=c, marker=mk, s=12, label=lab, zorder=3)
        for xx, yy in zip(xs, ys):
            if yy > TOP - 0.05: ax.annotate(f'{yy:.2f}', (xx, TOP - 0.05), xytext=(-14, -10), textcoords='offset points', fontsize=5.5, color=c)
    ax.set_ylim(0.95, 2.75); ax.axhline(1, color=INK, lw=.6); ax.set_xticks(range(len(ds))); ax.set_xticklabels([NAME[d] for d in ds], fontsize=6.6, rotation=30)
    ax.set_title(f"({'a' if lc == 0 else 'b'}) lead time {'0' if lc == 0 else '10 cycles (30 for the battery)'}, ρ = {rho}", loc='left', fontsize=8); ax.grid(alpha=.25, lw=.5, axis='y')
axs[0].set_ylabel('Cost rate / perfect-foresight cost rate'); axs[0].legend(frameon=False, fontsize=5.8, loc='upper left')
fig.tight_layout(w_pad=1.2); save(fig, 'FigR3_cost_audit5')

# ---------------------------------------------------------------- battery cost, fully nested
leads = [0, 15, 30, 45]
bp = [('STW_window', 'Recipe, window-tuned', PINK, 'o', '-'), ('STW_cost_1se', 'Recipe, cost-tuned (1-SE)', PURPLE, 's', '-'),
      ('trend_window', 'Capacity trend, window-tuned', BLUE, 'o', '--'), ('trend_cost_1se', 'Capacity trend, cost-tuned (1-SE)', LBLUE, 's', '--'),
      ('capacity_cost_1se', 'Capacity threshold, cost-tuned (1-SE)', GREEN, 'D', ':'), ('age', 'Age replacement', GREY, 'v', ':')]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)
for ax, an, ttl in zip(axs, ('cv123', 'lobo'), ('(a) Cross-validation by cell', '(b) One batch held out')):
    for p, lab, col, mk, ls in bp:
        ax.plot(leads, [BN[an]['cells'][f'{l}|50'][p]['ratio'] for l in leads], color=col, marker=mk, ms=3.5, ls=ls, lw=1.3, label=lab)
    ax.set_yscale('log'); ax.set_xticks(leads); ax.set_xlabel('Lead time ℓ (cycles)'); ax.axhline(1, color=INK, lw=.6)
    ax.set_title(f'{ttl}, ρ = 50', loc='left', fontsize=8); ax.grid(alpha=.25, lw=.5, axis='y', which='both')
axs[0].set_ylabel('Cost rate / perfect-foresight cost rate (log)'); axs[0].legend(frameon=False, loc='upper right', bbox_to_anchor=(1.0, 0.97), fontsize=5.6, ncol=2)
axs[0].set_yticks([1, 1.5, 2, 3, 5, 10, 20, 40]); axs[0].set_yticklabels(['1', '1.5', '2', '3', '5', '10', '20', '40'])
fig.tight_layout(w_pad=1.2); save(fig, 'Fig9_battery_cost5')

# ---------------------------------------------------------------- comparison with M
K1 = R5['kam']['fd001']['table']; QS = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8]
mp = [('P1_res_opt_mid', 'Their policy 1, P-res (optimised)', BLUE, 'o', '-'), ('P1_cls_opt_mid', 'Their policy 1, P-cls (optimised)', LBLUE, 's', '-'),
      ('P3_res60', 'Their policy 3, P-res', GREEN, 'D', '-'), ('STW_window', 'STW, window-tuned (mapped)', PINK, 'o', '--'),
      ('STW_cost_1se', 'STW, cost-tuned, 1-SE (mapped)', PURPLE, 's', '--'), ('STW_cost', 'STW, cost-tuned, plain (mapped)', ORANGE, '^', '--')]
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.7), gridspec_kw=dict(width_ratios=[1.1, 1.1, 1.0]))
a = axs[0]; dsl = ['fd001', 'fd002', 'fd003', 'fd004']
bp5 = [('P1_res_opt_mid', 'Their policy 1, P-res', BLUE), ('P1_cls_opt_mid', 'Their policy 1, P-cls', LBLUE), ('P3_res60', 'Their policy 3', GREEN),
       ('STW_window', 'STW, window-tuned (mapped)', PINK), ('STW_cost_1se', 'STW, cost-tuned 1-SE (mapped)', PURPLE)]
xw = .8 / len(bp5)
for i_, (p, lab, c) in enumerate(bp5):
    xs = np.arange(4) + (i_ - (len(bp5) - 1) / 2) * xw
    v = np.array([R5['kam'][d]['table'][f'0.1|{p}']['M'] for d in dsl]); lo = np.array([R5['kam'][d]['table'][f'0.1|{p}']['boot'][0] for d in dsl]); hi = np.array([R5['kam'][d]['table'][f'0.1|{p}']['boot'][1] for d in dsl])
    a.bar(xs, v, xw, color=c, label=lab); a.errorbar(xs, v, yerr=[v - lo, np.minimum(hi, 34) - v], fmt='none', ecolor=INK, lw=.6, capsize=1.2)
a.set_xticks(range(4)); a.set_xticklabels([d.upper() for d in dsl]); a.set_ylim(0, 44); a.set_yticks(range(0, 35, 5)); a.set_ylabel('M (%) at $c_p/c_c$ = 0.1')
a.set_title('(a) Five-fold, ΔT = 10', loc='left', fontsize=8); a.legend(frameon=False, fontsize=4.9, loc='upper center', bbox_to_anchor=(0.56, 1.0), ncol=2, columnspacing=0.8, handlelength=1.2); a.grid(alpha=.25, lw=.5, axis='y')
b = axs[1]; CU = pd.read_csv(F_('fragility_curve.csv')); CU = CU[CU.model == 'cls'].sort_values('p')
b.plot(CU.p, CU.M_train, color=INK, lw=1.2, label=f'training units (n = {int(CU.n_train.iloc[0])})')
b.plot(CU.p, CU.M_test, color=ORANGE, lw=1.0, ls='--', label=f'test units (n = {int(CU.n_test.iloc[0])})')
pm, px, pf = CU.p_mid.iloc[0], CU.p_max.iloc[0], CU.p_fail_train.iloc[0]
for v, lab, ls in ((pm, 'optimised, middle of the tie', ':'), (px, 'optimised, largest tied', '-.')):
    b.axvline(v, color=GREY, lw=.8, ls=ls, label=lab)
b.set_xscale('log'); b.set_yscale('log'); b.set_xlabel(r'$p_{\mathrm{thres}}$'); b.set_ylabel('M (%), log scale')
b.set_title(r'(b) Policy 1, P-cls, FD001 fold 1, $c_p/c_c$ = 0.01', loc='left', fontsize=8); b.legend(frameon=False, fontsize=5.0, loc='upper left'); b.grid(alpha=.25, lw=.5, which='both', axis='y')
c = axs[2]; TAL = R5['fragility']['tally']
tp = [('P1_cls_opt_mid', 'P1 P-cls opt'), ('P1_cls_q', r'P1 P-cls $p = c_p/c_c$'), ('P1_res_opt_mid', 'P1 P-res opt'), ('P1_res_q', r'P1 P-res $p = c_p/c_c$'),
      ('STW_cost', 'STW cost, plain'), ('STW_cost_1se', 'STW cost, 1-SE'), ('STW_window', 'STW window')]
dss = ['fd001', 'fd002', 'fd003', 'fd004']; cols = [PINK, BLUE, GREEN, ORANGE]; y = np.arange(len(tp)); h = .8 / len(dss)
for i, (d, col) in enumerate(zip(dss, cols)):
    v = [TAL.get(f'{d}|cv|{p}', {}).get('fail_small', np.nan) for p, _ in tp]
    c.barh(y + (i - 1.5) * h, v, h, color=col, label=d.upper())
c.set_yticks(y); c.set_yticklabels([l for _, l in tp], fontsize=6); c.invert_yaxis(); c.set_xlabel('Cells with ≥ 1 test failure (of 20)')
c.set_title(r'(c) Failures, $c_p/c_c$ ≤ 0.1', loc='left', fontsize=8); c.legend(frameon=False, fontsize=5.5, loc='lower right'); c.grid(alpha=.25, lw=.5, axis='x')
fig.tight_layout(w_pad=0.8); save(fig, 'Fig10_metric_M')
print('figures written to', OUT)
