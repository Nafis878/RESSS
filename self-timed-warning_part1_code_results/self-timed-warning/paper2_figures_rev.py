"""Revision figures of the warning-model manuscript: Fig. 7 (battery), Fig. 8 (theory check), Fig. 9 (windows and cost).
Vector PDF + 1000-dpi PNG, same style as paper2_figures.py. All numbers from paper2/numbers.json or the stored result files."""
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'Liberation Sans', 'font.size': 7.5, 'pdf.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False})
N = json.load(open('paper2/numbers.json')); OUT = 'out/paper2_figs'
BLUE, ORANGE, GREEN, PINK, GREY, PURPLE, INK = '#2a78d6', '#eb6834', '#1baf7a', '#e87ba4', '#8a8a8a', '#6b4bb3', '#1a1a1a'
DSC = {'PHM08': BLUE, 'FD001': '#7fb2ea', 'FD002': GREEN, 'FD003': '#9ad7bf', 'FD004': PURPLE, 'N-CMAPSS': ORANGE, 'Battery': PINK, 'Bearing': '#8a6d3b'}
MK = {10: 'o', 15: 's', 20: 'D'}
def save(fig, name):
    fig.savefig(f'{OUT}/{name}.pdf', facecolor='white'); fig.savefig(f'{OUT}/{name}.png', dpi=1000, facecolor='white'); plt.close(fig)

# ---------- Fig 7: theory check
T = pd.DataFrame(N['theory'])
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.9))
for _, r in T.iterrows():
    a.scatter(r.centred_bound_pct, r.realised_pct, color=DSC[r.dataset], marker=MK[int(r.H)], s=22, edgecolor='white', lw=.4, zorder=3)
    if r.dataset != 'Bearing': b.scatter(r.s_star, r.shift_mean, color=DSC[r.dataset], marker=MK[int(r.H)], s=22, edgecolor='white', lw=.4, zorder=3)
lo_ = -3
a.plot([lo_, 100], [lo_, 100], color=GREY, lw=.8, ls='--'); a.set_xlim(lo_, 100.5); a.set_ylim(lo_, 100.5)
a.set_xlabel('Centred concentration P(|ε − m| ≤ 7.5) (%)'); a.set_ylabel('Realised in-window rate (%)')
a.set_title('(a) Realised rate vs. error concentration', loc='left', fontsize=8); a.grid(alpha=.25, lw=.5)
b.plot([-7.5, -2], [-7.5, -2], color=GREY, lw=.8, ls='--'); b.set_xlim(-7.5, -4.3); b.set_ylim(-7.5, -1.5)
b.set_xlabel('Optimal shift implied by the errors, s* = −5.5 − m'); b.set_ylabel('Selected shift (mean over test units)')
b.set_title('(b) Selected vs. implied shift', loc='left', fontsize=8); b.grid(alpha=.25, lw=.5)
hs = [plt.Line2D([], [], color=c, marker='o', ls='', ms=4.5, label=d) for d, c in DSC.items()] + [plt.Line2D([], [], color=INK, marker=m, ls='', ms=4, mfc='none', label=f'H = {h}') for h, m in MK.items()]
fig.legend(handles=hs, loc='lower center', ncol=6, frameon=False, fontsize=6.5, bbox_to_anchor=(0.5, -0.01))
fig.tight_layout(rect=(0, 0.12, 1, 1), w_pad=2); save(fig, 'Fig8_theory_check')

# ---------- Fig 8: tolerance windows and maintenance cost
W = N['windows']; wins = [(-10, 2), (-13, 2), (-20, 5), (-30, 10)]
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw=dict(width_ratios=[1, 1.15]))
for ds, lab in (('PHM08', 'PHM08'), ('FD001', 'FD001'), ('FD002', 'FD002'), ('FD003', 'FD003'), ('FD004', 'FD004'), ('NCMAPSS6', 'N-CMAPSS')):
    if ds not in W: continue
    a.plot(range(4), [W[ds][f'{lo}|{hi}|20']['pct'] for lo, hi in wins], color=DSC[lab], marker='o', ms=3.5, lw=1.3, label=lab)
a.set_xticks(range(4)); a.set_xticklabels([f'[{lo}, +{hi}]'.replace('-', '−') for lo, hi in wins]); a.set_xlabel('Tolerance window (cycles)')
a.set_ylabel('First warnings in the window (%)'); a.set_ylim(50, 101); a.grid(alpha=.25, lw=.5, axis='y')
a.set_title('(a) Settings re-selected for each window, H = 20', loc='left', fontsize=8); a.legend(frameon=False, fontsize=6.5, loc='lower right')
rhos = [5, 10, 20, 50]
for ds, lab, src in (('PHM08', 'PHM08', 'cost'), ('NCMAPSS6', 'N-CMAPSS', 'cost'), ('battery', 'Battery', 'battery_cost')):
    C = N[src] if src == 'battery_cost' else N['cost'].get(ds)
    if not C: continue
    b.plot(rhos, [C[f'0|{r}']['stw_rel_pf'] for r in rhos], color=DSC[lab], marker='o', ms=3.5, lw=1.4, label=f'{lab}: self-timed warning')
    b.plot(rhos, [C[f'0|{r}']['age_rel_pf'] for r in rhos], color=DSC[lab], marker='v', ms=3.5, lw=1.1, ls='--', label=f'{lab}: optimal age replacement')
b.axhline(1, color=GREY, lw=.8); b.set_xscale('log'); b.set_xticks(rhos); b.set_xticklabels(rhos); b.set_xlabel('Cost of a failure relative to a planned replacement, ρ')
b.set_ylabel('Cost rate / perfect-foresight cost rate'); b.grid(alpha=.25, lw=.5, axis='y')
b.set_title('(b) Long-run cost rate, no lead time', loc='left', fontsize=8); b.legend(frameon=False, fontsize=6, loc='upper left')
fig.tight_layout(w_pad=2); save(fig, 'Fig9_windows_cost')

# ---------- Fig 9: battery confirmation
S = pd.read_csv('battery/severson_cycle_summary.csv.gz'); R = pd.read_csv('out/battery/warning_results.csv'); k = int(R.kappa.iloc[0])
r20 = R[(R.analysis == 'cv123') & (R.method == 'warning') & (R.H == 20)].set_index('unit')
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw=dict(width_ratios=[1.2, 1]))
col = {'IN': GREEN, 'EARLY': BLUE, 'LATE': ORANGE, 'MISSED': ORANGE}
for c, row in r20.iterrows():
    g = S[(S.cell == c) & (S.cycle <= row.life_cycles)]; q = g.QDischarge.where(g.QDischarge.between(0.5, 1.2)).ffill().bfill()
    a.plot(g.cycle, q.rolling(5, min_periods=1).median(), color=GREY, lw=.35, alpha=.5, zorder=1)
    if np.isfinite(row.cycle):
        cy = int(row.cycle * k); qq = q.rolling(5, min_periods=1).median().values[min(cy, len(q)) - 1]
        a.scatter(cy, qq, color=col[row.cls], s=7, zorder=3, edgecolor='none')
a.axhline(0.88, color=INK, lw=.7, ls=':'); a.text(1900, 0.885, 'end of life (0.88 Ah)', fontsize=6.3, ha='right', va='bottom')
a.set_xlabel('Cycle'); a.set_ylabel('Discharge capacity (Ah)'); a.set_ylim(0.86, 1.1); a.set_xlim(0, 2000)
a.scatter([], [], color=GREEN, s=9, label='first warning, correct'); a.scatter([], [], color=ORANGE, s=9, label='first warning, late')
a.legend(frameon=False, fontsize=6.3, loc='lower left'); a.set_title(f'(a) 123 LFP/graphite cells, first warnings at H = 20', loc='left', fontsize=8); a.grid(alpha=.25, lw=.5, axis='y')
D = N['battery_detail']; groups = [('cv123', 'Cross-validation\n(123 cells, primary)'), ('cv119', 'Without 4 noisy\nchannels (119)'), ('lobo', 'Leave one\nbatch out (123)')]
meths = [('warning', 'Self-timed warning', PINK), ('mlp_kf', 'MLP + Kalman filter', GREY), ('age_only', 'Age only', '#cfcfcf')]
x = np.arange(len(groups)); w = .26
for i, (m, lab, c) in enumerate(meths):
    v = [D[f'{g}|{m}|20']['pct'] for g, _ in groups]; b.bar(x + (i - 1) * w, v, w, color=c, label=lab)
    for xx, vv in zip(x + (i - 1) * w, v): b.text(xx, vv + 1.2, f'{vv:.0f}', ha='center', fontsize=6)
b.set_xticks(x); b.set_xticklabels([g[1] for g in groups], fontsize=6.6); b.set_ylim(0, 110); b.set_ylabel('First warnings in the window (%)')
b.set_title('(b) In-window rate at H = 20 blocks', loc='left', fontsize=8); b.legend(frameon=False, fontsize=6.3, loc='upper right', ncol=1, bbox_to_anchor=(1, 1.0)); b.grid(alpha=.25, lw=.5, axis='y')
fig.tight_layout(w_pad=2); save(fig, 'Fig7_battery')
print('figures 7-9 written')
