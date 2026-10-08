"""Figure: 30 random 50-engine iterations on PHM08 (rep30.py), x-axis = iteration 0-30. Same style as Fig. 5."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'Liberation Sans', 'font.size': 7.5, 'pdf.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False})
BLUE, ORANGE, PINK, GREY, INK = '#2a78d6', '#eb6834', '#e87ba4', '#8a8a8a', '#1a1a1a'
R = pd.read_csv('out/rep30/rep30_results_all.csv'); it = np.arange(1, 31)
g = R.groupby('repetition'); acc = 100 * g.result.apply(lambda s: (s == 'IN').mean()).reindex(it).values
late = g.result.apply(lambda s: (s.isin(['LATE', 'MISSED'])).sum()).reindex(it).values; early = g.result.apply(lambda s: (s == 'EARLY').sum()).reindex(it).values
left = g.true_cycles_left.mean().reindex(it).values; q25 = g.true_cycles_left.quantile(.25).reindex(it).values; q75 = g.true_cycles_left.quantile(.75).reindex(it).values
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.6))
a.bar(it, acc, color=BLUE, alpha=.8, width=.75, label='in-window rate per iteration')
a.axhline(acc.mean(), color=INK, ls='--', lw=1); a.text(30.5, acc.mean() + 0.4, f'mean {acc.mean():.1f}%', ha='right', va='bottom', fontsize=6.5)
a.axhline(96, color=GREY, ls=':', lw=.9); a.text(0.5, 96.4, '48 of 50', fontsize=6.2, color=GREY)
a.set_xlim(0, 30.9); a.set_xticks(range(0, 31, 5)); a.set_ylim(70, 100); a.set_xlabel('Iteration (50 random test engines, 168 training engines)')
a.set_ylabel('First warnings in [−13, +2] (%)'); a.set_title('(a) Accuracy in each of 30 iterations (H = 20)', loc='left', fontsize=8); a.grid(alpha=.25, lw=.5, axis='y')
b.fill_between(it, q25, q75, color=BLUE, alpha=.18, lw=0, label='interquartile range over the 50 engines')
b.plot(it, left, color=BLUE, marker='o', ms=3, lw=1.2, label='mean true cycles left at the warning')
b.axhline(np.nanmean(left), color=INK, ls='--', lw=1); b.text(30.5, np.nanmean(left) + 0.3, f'mean {np.nanmean(left):.1f} cycles', ha='right', va='bottom', fontsize=6.5)
b.axhline(13, color=GREY, ls=':', lw=.9); b.text(0.5, 13.3, '13 cycles (early limit can bind above)', fontsize=6.2, color=GREY)
b.set_xlim(0, 30.9); b.set_xticks(range(0, 31, 5)); b.set_ylim(0, 30); b.set_xlabel('Iteration'); b.set_ylabel('True cycles left at the warning')
b.set_title('(b) Lead time in each iteration (H = 20)', loc='left', fontsize=8); b.legend(frameon=False, fontsize=6.3, loc='lower right'); b.grid(alpha=.25, lw=.5, axis='y')
fig.tight_layout(w_pad=1.5)
for ext, kw in (('pdf', {}), ('png', {'dpi': 1000})): fig.savefig(f'out/paper2_figs/Fig_rep30.{ext}', facecolor='white', **kw)
print(f'mean acc {acc.mean():.2f}, mean left {np.nanmean(left):.2f}')
