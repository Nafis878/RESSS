"""Figures for the revision: Fig. R1 timing vs estimate; Fig. R2 cost-primary comparison (lead 0 and 10)."""
import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
R = json.load(open('paper2/numbers.json'))['rev2']
NAME = {'PHM08': 'PHM08', 'FD001': 'FD001', 'FD002': 'FD002', 'FD003': 'FD003', 'FD004': 'FD004', 'NCMAPSS6': 'N-CMAPSS', 'Battery': 'Battery'}
DS = R['datasets']
plt.rcParams.update({'font.size': 9, 'font.family': 'DejaVu Sans', 'axes.spines.top': False, 'axes.spines.right': False})
C = {'STW': '#1f5a96', 'STW_const': '#7fa7cf', 'HI_threshold': '#c8783c', 'STW_cost': '#1f5a96', 'HI_cost': '#c8783c', 'STW_window': '#7fa7cf', 'age': '#8c8c8c'}

# ---------------- Fig R1
fig, ax = plt.subplots(figsize=(7.2, 3.0)); x = np.arange(len(DS)); w = 0.26
for j, (m, lab) in enumerate([('STW', 'STW (model estimate)'), ('STW_const', 'STW timing, constant estimate'), ('HI_threshold', 'Health-indicator threshold alarm')]):
    v = [R['window'][d]['20'][m] for d in DS]
    p = np.array([o['pct'] for o in v]); lo = p - np.array([o['ci'][0] for o in v]); hi = np.array([o['ci'][1] for o in v]) - p
    ax.bar(x + (j - 1) * w, p, w, color=C[m], label=lab, yerr=[lo, hi], error_kw=dict(lw=0.7, capsize=1.5, ecolor='#333'))
ax.set_xticks(x); ax.set_xticklabels([NAME[d] for d in DS]); ax.set_ylabel('First warnings in window (%)'); ax.set_ylim(0, 105)
ax.legend(frameon=False, ncol=3, loc='upper center', bbox_to_anchor=(0.5, 1.16), fontsize=8)
fig.tight_layout(); fig.savefig('paper2/img/FigR1_timing_vs_estimate.png', dpi=300); fig.savefig('out/rev/FigR1_timing_vs_estimate.pdf')

# ---------------- Fig R2
rhos = [5, 10, 20, 50]
fig, axs = plt.subplots(2, len(DS), figsize=(7.4, 3.9), sharex=True)
for r_i, lead in enumerate([0, 10]):
    for c_i, d in enumerate(DS):
        ax = axs[r_i, c_i]
        for m, lab, ls in [('STW_cost', 'STW, cost-tuned', '-'), ('STW_window', 'STW, window-tuned', '--'), ('HI_cost', 'HI threshold, cost-tuned', '-'), ('age', 'Optimal age replacement', ':')]:
            ax.plot(rhos, [R['cost'][d][f'{lead}|{rho}'][m]['ratio'] for rho in rhos], ls, color=C[m], marker='o', ms=2.5, lw=1.2, label=lab)
        ax.set_xscale('log'); ax.minorticks_off(); ax.set_xticks(rhos); ax.set_xticklabels(rhos, fontsize=7); ax.axhline(1, color='#bbb', lw=0.6)
        ax.tick_params(labelsize=7)
        if r_i == 0: ax.set_title(NAME[d], fontsize=8)
        if c_i == 0: ax.set_ylabel(f'Cost rate / perfect\nforesight (ℓ = {lead})', fontsize=8)
        if r_i == 1: ax.set_xlabel('ρ', fontsize=8)
h, l = axs[0, 0].get_legend_handles_labels(); fig.legend(h, l, ncol=4, frameon=False, loc='upper center', fontsize=7.5)
fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig('paper2/img/FigR2_cost_primary.png', dpi=300); fig.savefig('out/rev/FigR2_cost_primary.pdf')
print('figures written')
