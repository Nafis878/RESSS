"""Figures of the revised manuscript that use the audit reruns (vector PDF + 300-dpi PNG in out/paper3_figs/).
Fig2_decomposition   fixed-time versus self-timed contrast, separated into horizon, calibration and alarm choice (PHM08)
Fig7_battery_v3      battery: first warnings with training-only block length; within-batch versus held-out-batch rates
FigR3_cost_audit     cost of window-tuned, cost-tuned (plain and regularised) and age policies by dataset
Fig8_shift_A1        assumption A1: realised in-window rate and alarm time as the shift moves away from the selected one
"""
import json, os, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'Liberation Sans', 'font.size': 7.5, 'pdf.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False})
import sys
A = 'results/audit' if '--frozen' in sys.argv else 'out/audit'
N = json.load(open('paper3/numbers.json')); R3 = N.get('rev3', {}); OUT = 'out/paper3_figs'; os.makedirs(OUT, exist_ok=True)
def F_(name):
    for c in (f'{A}/{name}', f'{A}/{name}.gz'):
        if os.path.exists(c): return c
    return None
BLUE, ORANGE, GREEN, PINK, GREY, PURPLE, INK = '#2a78d6', '#eb6834', '#1baf7a', '#e87ba4', '#8a8a8a', '#6b4bb3', '#1a1a1a'
NAME = {'PHM08': 'PHM08', 'FD001': 'FD001', 'FD002': 'FD002', 'FD003': 'FD003', 'FD004': 'FD004', 'NCMAPSS6': 'N-CMAPSS', 'Battery': 'Battery'}


def save(fig, name):
    fig.savefig(f'{OUT}/{name}.pdf', facecolor='white'); fig.savefig(f'{OUT}/{name}.png', dpi=300, facecolor='white'); plt.close(fig)


# ---------------------------------------------------------------- Fig. 2
F = R3['fixed_time']
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw=dict(width_ratios=[1, 1.25]))
fr = [0.3, 0.5, 0.7, 0.9]
for m, lab, c, mk in (('gbm', 'Gradient-boosted trees', BLUE, 'o'), ('lstm', 'LSTM', ORANGE, 's'), ('cnn', 'CNN', GREEN, 'D')):
    a.plot([100 * f for f in fr], [F['fixed'][f'{m}|{f}']['raw_pct'] for f in fr], color=c, marker=mk, ms=3, lw=1, ls='--', alpha=.8)
    a.plot([100 * f for f in fr], [F['fixed'][f'{m}|{f}']['cal_pct'] for f in fr], color=c, marker=mk, ms=3.5, lw=1.4, label=lab)
a.axhline(F['self|20']['pct'], color=INK, ls=':', lw=1); a.text(29, F['self|20']['pct'] + 2, f"self-timed first warning, H = 20: {F['self|20']['pct']}%", fontsize=6.5)
a.plot([], [], color=GREY, ls='--', lw=1, label='raw estimate'); a.plot([], [], color=GREY, lw=1.4, label='shift tuned on calibration engines')
a.set_xticks([30, 50, 70, 90]); a.set_xticklabels([f"{int(100 * f)}%\n({int(F['fixed'][f'gbm|{f}']['median_rul'])})" for f in fr])
a.set_xlabel('Prediction time, % of life (median true cycles left)'); a.set_ylabel('Predictions in [−13, +2] (%)'); a.set_ylim(0, 100)
a.set_title('(a) Fixed-time models, PHM08 (218 engines)', loc='left', fontsize=8); a.legend(frameon=False, fontsize=6, loc='upper left', bbox_to_anchor=(0.0, 0.87)); a.grid(alpha=.25, lw=.5, axis='y')
half = N['half']
items = [('Best of eleven fixed-time models at half of life\n(stacked hybrid, shift tuned)', half['hybrid']['pct'], None, GREY),
         ('Gradient-boosted trees at half of life\n(shift tuned on calibration engines)', F['fixed']['gbm|0.5']['cal_pct'], F['fixed']['gbm|0.5']['cal_ci'], GREY),
         ('Gradient-boosted trees at 90% of life, raw', F['fixed']['gbm|0.9']['raw_pct'], None, BLUE),
         ('Gradient-boosted trees at 90% of life\n(shift tuned on calibration engines)', F['fixed']['gbm|0.9']['cal_pct'], F['fixed']['gbm|0.9']['cal_ci'], BLUE),
         ('Warning-model estimate when 20 true cycles\nare left (oracle-timed, not deployable)', F['oracle|20']['pct'], F['oracle|20']['ci'], PURPLE),
         ('Self-timed first warning, H = 20', F['self|20']['pct'], F['self|20']['ci'], PINK)]
for i, (lab, v, ci, c) in enumerate(items[::-1]):
    b.barh(i, v, color=c, height=.62)
    if ci: b.errorbar(v, i, xerr=[[v - ci[0]], [ci[1] - v]], color=INK, lw=.8, capsize=2)
    b.text(min(v, 96) + (ci[1] - v if ci else 0) + 1.2, i, f'{v:.1f}%', va='center', fontsize=6.4)
b.set_yticks(range(len(items))); b.set_yticklabels([x[0] for x in items[::-1]], fontsize=6.2); b.set_xlim(0, 108)
b.set_xlabel('In window [−13, +2] (%), 95% CI'); b.set_title('(b) Horizon, calibration and alarm choice, PHM08', loc='left', fontsize=8); b.grid(alpha=.25, lw=.5, axis='x')
fig.tight_layout(w_pad=1.5); save(fig, 'Fig2_decomposition')

# ---------------------------------------------------------------- Fig. 7 (battery, training-only block length)
if F_('battery_corrected.csv') and 'battery' in R3:
    S = pd.read_csv('battery/severson_cycle_summary.csv.gz'); C = pd.read_csv(F_('battery_corrected.csv'))
    r20 = C[(C.analysis == 'cv123') & (C.method == 'warning') & (C.H == 20)].set_index('unit')
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw=dict(width_ratios=[1.15, 1]))
    col = {'IN': GREEN, 'EARLY': BLUE, 'LATE': ORANGE, 'MISSED': ORANGE}
    for c, row in r20.iterrows():
        g = S[(S.cell == c) & (S.cycle <= row.life_cycles)]; q = g.QDischarge.where(g.QDischarge.between(0.5, 1.2)).ffill()
        qs = q.rolling(5, min_periods=1).median()
        a.plot(g.cycle, qs, color=GREY, lw=.35, alpha=.5, zorder=1)
        if np.isfinite(row.cycle):
            cy = int(row.cycle * row.kappa); a.scatter(cy, qs.values[min(cy, len(qs)) - 1], color=col[row.cls], s=7, zorder=3, edgecolor='none')
    a.axhline(0.88, color=INK, lw=.7, ls=':'); a.text(1900, 0.885, 'end of life (0.88 Ah)', fontsize=6.3, ha='right', va='bottom')
    a.set_xlabel('Cycle'); a.set_ylabel('Discharge capacity (Ah)'); a.set_ylim(0.86, 1.1); a.set_xlim(0, 2000)
    for k_, lab in (('IN', 'correct'), ('EARLY', 'too early'), ('LATE', 'late')):
        if (r20.cls == k_).any(): a.scatter([], [], color=col[k_], s=9, label=f'first warning, {lab}')
    a.legend(frameon=False, fontsize=6.3, loc='lower left'); a.set_title(f'(a) {len(r20)} cells, first warnings at H = 20 blocks (CV)', loc='left', fontsize=8); a.grid(alpha=.25, lw=.5, axis='y')
    D = R3['battery']['summary']; BB = R3.get('battery_baselines', {})
    groups = [('cv123', 'Cross-validation\nby cell'), ('lobo', 'Leave one\nbatch out')]
    meths = [('warning', 'Recipe (self-timed)', PINK, D), ('mlp_kf', 'MLP + Kalman filter', GREY, D), ('age_only', 'Age only', '#cfcfcf', D)]
    bl = [k.split('|')[1] for k in BB if k.startswith('cv123|')]
    for m, lab, c in (('capacity_threshold', 'Capacity threshold', BLUE), ('capacity_trend', 'Capacity trend', '#9cc3ef')):
        if m in bl: meths.append((m, lab, c, None))
    x = np.arange(len(groups)); w = .8 / len(meths)
    for i, (m, lab, c, src) in enumerate(meths):
        v = [(D[f'{g}|{m}|20']['pct'] if src is not None else BB[f'{g}|{m}']['pct']) for g, _ in groups]
        xs = x + (i - (len(meths) - 1) / 2) * w; b.bar(xs, v, w, color=c, label=lab)
        for xx, vv in zip(xs, v): b.text(xx, vv + 1.2, f'{vv:.0f}', ha='center', fontsize=5.8)
    b.set_xticks(x); b.set_xticklabels([g[1] for g in groups], fontsize=6.8); b.set_ylim(0, 135); b.set_yticks(range(0, 101, 20)); b.set_ylabel('First warnings in the window (%)')
    b.set_title('(b) In-window rate at H = 20 blocks', loc='left', fontsize=8); b.legend(frameon=False, fontsize=6, loc='upper center', ncol=3, columnspacing=1.0, handlelength=1.2); b.grid(alpha=.25, lw=.5, axis='y')
    fig.tight_layout(w_pad=2); save(fig, 'Fig7_battery_v3')

# ---------------------------------------------------------------- cost figure
if R3.get('cost'):
    ds = [d for d in NAME if d in R3['cost']]
    pols = [('STW_window', 'STW, window-tuned (H by cost)', PINK, 'o'), ('STW_cost', 'STW, cost-tuned', BLUE, 's'), ('STW_cost_1se', 'STW, cost-tuned, 1-SE rule', '#9cc3ef', 's'),
            ('Q10_cost', '10% quantile alarm, cost-tuned', GREEN, 'D'), ('HI_cost', 'Health-indicator alarm, cost-tuned', ORANGE, '^'), ('age', 'Age replacement', GREY, 'v')]
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
    for ax, (lc, rho) in zip(axs, ((0, 10), (10, 50))):
        for j, (p, lab, c, mk) in enumerate(pols):
            ys = []
            for d in ds:
                key = f"{lc if d != 'Battery' else lc * 3}|{rho}"; cc = R3['cost'][d].get(key)
                ys.append(cc[p]['ratio'] if cc and p in cc else np.nan)
            xs = np.arange(len(ds)) + (j - 2.5) * .11; ys = np.array(ys, float); TOP = 2.75
            ax.scatter(xs, np.minimum(ys, TOP - 0.05), color=c, marker=mk, s=12, label=lab, zorder=3)
            for xx, yy in zip(xs, ys):
                if yy > TOP - 0.05: ax.annotate(f'{yy:.2f}', (xx, TOP - 0.05), xytext=(-14, -10), textcoords='offset points', fontsize=5.5, color=c)
        ax.set_ylim(0.95, 2.75)
        ax.axhline(1, color=INK, lw=.6); ax.set_xticks(range(len(ds))); ax.set_xticklabels([NAME[d] for d in ds], fontsize=6.6, rotation=30)
        ax.set_title(f"({'a' if lc == 0 else 'b'}) lead time {'0' if lc == 0 else '10 cycles (30 for the battery)'}, ρ = {rho}", loc='left', fontsize=8); ax.grid(alpha=.25, lw=.5, axis='y')
    axs[0].set_ylabel('Cost rate / perfect-foresight cost rate'); axs[0].legend(frameon=False, fontsize=5.8, loc='upper left')
    fig.tight_layout(w_pad=1.2); save(fig, 'FigR3_cost_audit')

# ---------------------------------------------------------------- shift study
if R3.get('shift'):
    sh = R3['shift']; ds = [d for d in NAME if d in sh]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.7))
    cols = dict(zip(NAME, [PINK, BLUE, '#0f6e8c', '#79b6f0', PURPLE, ORANGE, GREEN]))
    for d in ds:
        o = sh[d]; a.plot(o['offsets'], o['realised'], color=cols[d], lw=1.3, label=NAME[d]); a.plot(o['offsets'], o['a1_prediction'], color=cols[d], lw=.9, ls='--')
        b.plot(o['offsets'], np.array(o['median_rul_at_alarm']) - o['median_rul_at_alarm'][len(o['offsets']) // 2], color=cols[d], lw=1.3, label=NAME[d])
    a.plot([], [], color=GREY, lw=1.3, label='realised'); a.plot([], [], color=GREY, lw=.9, ls='--', label='predicted under A1')
    a.set_xlabel('Shift relative to the selected shift (cycles; blocks for the battery)'); a.set_ylabel('Test first warnings in window (%)')
    a.set_title('(a) Realised rate and the A1 prediction, H = 20', loc='left', fontsize=8); a.legend(frameon=False, fontsize=5.8, ncol=2, loc='lower center'); a.grid(alpha=.25, lw=.5, axis='y')
    b.plot([-4, 4], [4, -4], color=GREY, lw=.7, ls=':'); b.text(0.6, 2.4, 'dotted: alarm one cycle later\nper unit of shift', fontsize=6, color=GREY)
    b.set_xlabel('Shift relative to the selected shift'); b.set_ylabel('Change in median true life left at alarm')
    b.set_title('(b) The shift moves the alarm', loc='left', fontsize=8); b.grid(alpha=.25, lw=.5, axis='y')
    fig.tight_layout(w_pad=1.5); save(fig, 'Fig8_shift_A1')
print('audit figures written')
