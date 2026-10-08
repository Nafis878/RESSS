"""Figures of the second revision (vector PDF + 300-dpi PNG in out/paper4_figs/), from paper4/numbers.json and the audit outputs.
Fig2_matched          fixed-time versus self-timed on PHM08 under matched training data and cross-fitted calibration
Fig8_battery_physical battery, common physical task, fully nested: rates by evaluation, kappa sensitivity, notice
Fig9_battery_cost     battery cost under cross-validation and with a batch held out, including the capacity trend
Usage: python fig_audit2.py [--frozen]
"""
import os, sys, json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'Liberation Sans', 'font.size': 7.5, 'pdf.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False})
A = 'results/audit' if '--frozen' in sys.argv else 'out/audit'
N = json.load(open('paper4/numbers.json')); R3, R4 = N['rev3'], N['rev4']; OUT = 'out/paper4_figs'; os.makedirs(OUT, exist_ok=True)
BLUE, ORANGE, GREEN, PINK, GREY, PURPLE, INK, LBLUE = '#2a78d6', '#eb6834', '#1baf7a', '#e87ba4', '#8a8a8a', '#6b4bb3', '#1a1a1a', '#9cc3ef'


def F_(name):
    for c in (f'{A}/{name}', f'{A}/{name}.gz'):
        if os.path.exists(c): return c
    return None


def save(fig, name):
    fig.savefig(f'{OUT}/{name}.pdf', facecolor='white'); fig.savefig(f'{OUT}/{name}.png', dpi=300, facecolor='white'); plt.close(fig)


# ---------------------------------------------------------------- Fig. 2
F = R3['fixed_time']; V = R4['fixed_matched']['variants']
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw=dict(width_ratios=[1, 1.3]))
fr = [0.3, 0.5, 0.7, 0.9]
for m, lab, c, mk in (('gbm', 'Gradient-boosted trees', BLUE, 'o'), ('lstm', 'LSTM', ORANGE, 's'), ('cnn', 'CNN', GREEN, 'D')):
    a.plot([100 * f for f in fr], [F['fixed'][f'{m}|{f}']['raw_pct'] for f in fr], color=c, marker=mk, ms=3, lw=1, ls='--', alpha=.8)
    a.plot([100 * f for f in fr], [F['fixed'][f'{m}|{f}']['cal_pct'] for f in fr], color=c, marker=mk, ms=3.5, lw=1.4, label=lab)
a.plot([], [], color=GREY, ls='--', lw=1, label='raw estimate'); a.plot([], [], color=GREY, lw=1.4, label='shift tuned on calibration engines')
a.set_xticks([30, 50, 70, 90]); a.set_xticklabels([f"{int(100 * f)}%\n({int(F['fixed'][f'gbm|{f}']['median_rul'])})" for f in fr])
a.set_xlabel('Prediction time, % of life (median true cycles left)'); a.set_ylabel('Predictions in [−13, +2] (%)'); a.set_ylim(0, 100)
a.set_title('(a) Fixed-time models, fit 75% / calibrate 25%', loc='left', fontsize=8); a.legend(frameon=False, fontsize=6, loc='upper left'); a.grid(alpha=.25, lw=.5, axis='y')
items = [('Fixed-time GBM at 50% of life', 'fixed_f50', BLUE, None), ('Fixed-time GBM at 90% of life', 'fixed_f90', BLUE, None),
         ('Fixed-time GBM, 20 true cycles left (oracle time)', 'fixed_r20', BLUE, '//'), ('Fixed-time GBM with the self-timed trigger', 'fixed_trigger', BLUE, '..'),
         ("Recipe's regressor at 90% of life", 'recipe_f90', PINK, None), ("Recipe's regressor, 20 true cycles left (oracle time)", 'recipe_r20', PINK, '//'),
         ('Recipe, self-timed first warning (H = 20)', 'recipe_self', PINK, '..')]
for i, (lab, k, c, h) in enumerate(items[::-1]):
    v = V[k]; b.barh(i, v['pct'], color=c, height=.62, hatch=h, edgecolor='white' if h else None, lw=0)
    b.errorbar(v['pct'], i, xerr=[[v['pct'] - v['ci'][0]], [v['ci'][1] - v['pct']]], color=INK, lw=.8, capsize=2)
    b.text(v['ci'][1] + 1.2, i, f"{v['pct']:.1f}%", va='center', fontsize=6.3)
b.set_yticks(range(len(items))); b.set_yticklabels([x[0] for x in items[::-1]], fontsize=6.2); b.set_xlim(0, 110)
b.set_xlabel('In window [−13, +2] (%), 95% CI'); b.set_title('(b) Matched data, cross-fitted calibration (PHM08)', loc='left', fontsize=8); b.grid(alpha=.25, lw=.5, axis='x')
fig.tight_layout(w_pad=1.2); save(fig, 'Fig2_matched')

# ---------------------------------------------------------------- Fig. 8 battery, physical task
BP = R4['battery_physical']
parts = [pd.read_csv(f) for f in (F_('battery_physical.csv'), F_('battery_physical_cv.csv'), F_('battery_physical_lobo.csv')) if f]
Bp = pd.concat(parts).drop_duplicates(subset=['analysis', 'split', 'variant', 'method', 'kappa', 'unit'])
fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.2, 2.7), gridspec_kw=dict(width_ratios=[1.25, 1, 1.05]))
groups = [('cv123', None, 'CV by cell'), ('lobo', 'lobo1', 'Batch 1\nheld out'), ('lobo', 'lobo2', 'Batch 2\nheld out'), ('lobo', 'lobo3', 'Batch 3\nheld out')]
series = [('rule_nested|recipe', 'Recipe, κ by rule (nested)', PINK), ('cv_selected|recipe', 'Recipe, κ by inner CV', '#f2b8cf'), ('rule_kappa|capacity_trend', 'Capacity trend', BLUE)]
x = np.arange(len(groups)); w = .26
for i, (key, lab, col) in enumerate(series):
    v = [BP[f'{an}|{key}' + (f'|{sp}' if sp else '')]['pct'] for an, sp, _ in groups]
    xs = x + (i - 1) * w; a.bar(xs, v, w, color=col, label=lab)
    for xx, vv in zip(xs, v): a.text(xx, vv + 1.5, f'{vv:.0f}', ha='center', fontsize=5.6)
a.set_xticks(x); a.set_xticklabels([g[2] for g in groups], fontsize=6.4); a.set_ylim(0, 128); a.set_yticks(range(0, 101, 20)); a.set_ylabel('First warnings in [−39, +6] cycles (%)')
a.set_title('(a) In-window rate, H = 60 cycles', loc='left', fontsize=8); a.legend(frameon=False, fontsize=5.8, loc='upper center', ncol=2); a.grid(alpha=.25, lw=.5, axis='y')
ks = [2, 3, 4, 5, 6]
for an, m, lab, col, ls in (('cv123', 'recipe', 'Recipe, CV by cell', PINK, '-'), ('lobo', 'recipe', 'Recipe, batch held out', PINK, '--'),
                            ('cv123', 'capacity_trend', 'Trend, CV by cell', BLUE, '-'), ('lobo', 'capacity_trend', 'Trend, batch held out', BLUE, '--')):
    b.plot(ks, [BP[f'{an}|fixed_kappa|{m}|{k}']['pct'] for k in ks], color=col, ls=ls, marker='o', ms=3, lw=1.2, label=lab)
b.set_xticks(ks); b.set_xlabel('Block length κ (cycles), fixed for inner and outer models'); b.set_ylim(50, 102); b.set_ylabel('In window (%)')
b.set_title('(b) Sensitivity to κ', loc='left', fontsize=8); b.legend(frameon=False, fontsize=5.8, loc='lower right'); b.grid(alpha=.25, lw=.5, axis='y')
rule = BP['rule_kappa']; NN = np.arange(0, 121, 5)
rec = Bp[(Bp.variant == 'rule_nested') & (Bp.method == 'recipe')]
tre = pd.concat([Bp[(Bp.variant == 'fixed_kappa') & (Bp.method == 'capacity_trend') & (Bp.split == sp) & (Bp.kappa == k)] for sp, k in rule.items()])
for D, lab, col in ((rec, 'Recipe', PINK), (tre, 'Capacity trend', BLUE)):
    for an, ls in (('cv123', '-'), ('lobo', '--')):
        g = D[D.analysis == an]; c.plot(NN, [100 * ((g.cls == 'IN') & (g.r_cycles >= n)).mean() for n in NN], color=col, ls=ls, lw=1.3, label=f"{lab}, {'CV' if an == 'cv123' else 'batch held out'}")
c.set_xlabel('Minimum notice N (cycles)'); c.set_ylabel('Correct first warnings with ≥ N cycles left (%)'); c.set_ylim(0, 102)
c.set_title('(c) Correct and with enough notice', loc='left', fontsize=8); c.legend(frameon=False, fontsize=5.6, loc='lower left'); c.grid(alpha=.25, lw=.5, axis='y')
fig.tight_layout(w_pad=1.0); save(fig, 'Fig8_battery_physical')

# ---------------------------------------------------------------- Fig. 9 battery cost, CV and held-out batch
C2 = R4['battery_cost2']; leads = [0, 15, 30, 45]
pols = [('STW_window', 'Recipe, window-tuned', PINK, 'o', '-'), ('STW_cost_1se', 'Recipe, cost-tuned (1-SE)', PURPLE, 's', '-'),
        ('trend_window', 'Capacity trend, window-tuned', BLUE, 'o', '--'), ('trend_cost_1se', 'Capacity trend, cost-tuned (1-SE)', LBLUE, 's', '--'),
        ('capacity_cost_1se', 'Capacity threshold, cost-tuned (1-SE)', GREEN, 'D', ':'), ('age', 'Age replacement', GREY, 'v', ':')]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)
for ax, an, ttl in zip(axs, ('cv123', 'lobo'), ('(a) Cross-validation by cell', '(b) One batch held out')):
    for p, lab, col, mk, ls in pols:
        ax.plot(leads, [C2[an]['cells'][f'{l}|50'][p]['ratio'] for l in leads], color=col, marker=mk, ms=3.5, ls=ls, lw=1.3, label=lab)
    ax.set_yscale('log'); ax.set_xticks(leads); ax.set_xlabel('Lead time ℓ (cycles)'); ax.axhline(1, color=INK, lw=.6)
    ax.set_title(f'{ttl}, ρ = 50', loc='left', fontsize=8); ax.grid(alpha=.25, lw=.5, axis='y', which='both')
axs[0].set_ylabel('Cost rate / perfect-foresight cost rate (log)'); axs[1].legend(frameon=False, loc='center right', bbox_to_anchor=(1.0, 0.75), fontsize=5.6)
axs[0].set_yticks([1, 1.5, 2, 3, 5, 10, 20, 40]); axs[0].set_yticklabels(['1', '1.5', '2', '3', '5', '10', '20', '40'])
fig.tight_layout(w_pad=1.2); save(fig, 'Fig9_battery_cost')
print('second-revision figures written')
