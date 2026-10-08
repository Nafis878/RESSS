"""Fig. 1 of the warning-model paper: architecture of the self-timed end-of-life warning model (STW).
Vector PDF + 1000-dpi PNG, double-column width (7.2 in)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
plt.rcParams.update({'font.family': 'Liberation Sans', 'mathtext.fontset': 'dejavusans', 'pdf.fonttype': 42, 'font.size': 7})
INK, MUTED = '#1a1a1a', '#555555'
S_DATA = dict(fc='#F2F2F2', ec='#7a7a7a'); S_ENC = dict(fc='#E8F1FB', ec='#2a78d6'); S_DEC = dict(fc='#FDEEE7', ec='#d9531e')
S_OUT = dict(fc='#E7F5E7', ec='#1b8a1b'); S_OFF = dict(fc='#F3EEFA', ec='#6b4bb3')
Wd, Hd = 7.2, 4.1
fig = plt.figure(figsize=(Wd, Hd)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, Wd); ax.set_ylim(0, Hd); ax.axis('off')

def box(x, y, w, h, st, title, lines, tsize=7.3, bsize=6.3, ls='-'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.05', lw=0.9, linestyle=ls, **st))
    ax.text(x + w / 2, y + h - 0.07, title, ha='center', va='top', fontsize=tsize, weight='bold', color=INK, linespacing=1.15)
    nt = title.count('\n') + 1
    ax.text(x + w / 2, y + h - 0.1 - 0.13 * nt - 0.03, lines, ha='center', va='top', fontsize=bsize, color=INK, linespacing=1.32)
    return (x, y, w, h)

def arr(p, q, color=INK, ls='-', rad=0.0, lw=0.9, label=None, lxy=None, lsize=6.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=7, lw=lw, color=color, linestyle=ls, shrinkA=0, shrinkB=0,
                                 connectionstyle=f'arc3,rad={rad}'))
    if label: ax.text(*lxy, label, fontsize=lsize, color=color, ha='center', va='center', style='italic')

# ---- lane frames
ax.add_patch(FancyBboxPatch((0.06, 1.72), Wd - 0.12, 2.32, boxstyle='round,pad=0,rounding_size=0.08', fc='none', ec='#b5b5b5', lw=0.7))
ax.text(0.16, 3.98, 'Online inference: executed at every flight cycle $t$ of an engine in service', fontsize=7.6, weight='bold', va='top', color=INK)
ax.add_patch(FancyBboxPatch((0.06, 0.06), Wd - 0.12, 1.58, boxstyle='round,pad=0,rounding_size=0.08', fc='none', ec='#b5b5b5', lw=0.7))
ax.text(0.16, 1.58, 'Offline design: training engines only (nested cross-validation)', fontsize=7.6, weight='bold', va='top', color=INK)

# ---- online pipeline (row 1)
y1, h1 = 2.62, 1.12
b1 = box(0.16, y1, 1.02, h1, S_DATA, 'Sensor stream', '$\\mathbf{x}_t$: temperature,\npressure, speed, flow\nsensors (15 in PHM08,\n6 in N-CMAPSS)\n$\\mathbf{a}_t$: operating regime')
b2 = box(1.33, y1, 1.08, h1, S_DATA, 'Condition\nnormalisation', '$z_{t,j}=\\frac{x_{t,j}-\\mu_{j}(a_t)}{\\sigma_{j}(a_t)}$\n\n$\\mu,\\sigma$ per regime,\nfrom training\nengines')
b3 = box(2.56, y1, 1.30, h1, S_ENC, 'Causal feature\nencoder $\\phi_t$', 'baseline $\\mathbf{b}$ = mean of\nfirst 20 cycles\nEWM$_{10}$, EWM$_{30}$ of $\\mathbf{z}-\\mathbf{b}$\nslopes over 15 and\n40 cycles; age $t$')
b4 = box(4.01, y1, 1.30, h1, S_ENC, 'Horizon-focused\nregressor', 'gradient-boosted trees,\nabsolute-error loss\ntarget $\\min(\\mathrm{RUL}_t, c)$\n$c\\in\\{40,60,90\\}$:\nprecise near failure only')
b5 = box(5.46, y1, 1.58, h1, S_DEC, 'Window-centred\ndebounced trigger', '$\\tilde y_t=\\mathrm{EWM}_{m}(\\hat y)_t+s$\n\nWARN at the first $t$ with\n$\\tilde y_\\tau\\leq H$ for $\\tau=t{-}k{+}1..t$\n($H$ = warning level)')
for a, b in ((b1, b2), (b2, b3), (b3, b4), (b4, b5)):
    arr((a[0] + a[2] + 0.01, y1 + h1 / 2), (b[0] - 0.01, y1 + h1 / 2))
ax.text((b4[0] + b4[2] + b5[0]) / 2, y1 + h1 / 2 + 0.1, '$\\hat y_t$', fontsize=7, ha='center', color=INK)
ax.text((b3[0] + b3[2] + b4[0]) / 2, y1 + h1 / 2 + 0.1, '$\\phi_t$', fontsize=7, ha='center', color=INK)

# ---- outputs (row 2 of the online lane)
yo = 1.84
o1 = box(5.46, yo, 1.58, 0.52, S_OUT, 'Warning issued at $t^*$', 'report $\\tilde y_{t^*}$ cycles left', bsize=6.3)
o2 = box(2.75, yo, 2.2, 0.52, dict(fc='white', ec='#9a9a9a'), 'Silent: keep monitoring', 'condition not met at cycle $t$', bsize=6.3)
arr((b5[0] + b5[2] * 0.72, y1 - 0.01), (b5[0] + b5[2] * 0.72, yo + 0.53), color='#1b8a1b', label='yes', lxy=(b5[0] + b5[2] * 0.72 + 0.14, y1 - 0.09))
arr((b5[0] + 0.2, y1 - 0.01), (o2[0] + o2[2] - 0.01, yo + 0.36), color=MUTED, rad=-0.25, label='no', lxy=(5.28, 2.47))
arr((o2[0] + 0.01, yo + 0.3), (b1[0] + 0.5, y1 - 0.01), color=MUTED, rad=0.0, ls=(0, (3, 2)), label='next cycle $t+1$', lxy=(1.95, 2.52))

# ---- window scale inset (inside online lane, left bottom area)
# (placed in the offline lane's scoring box instead, see below)

# ---- offline lane
yb, hb = 0.18, 1.08
c1 = box(0.16, yb, 1.55, hb, S_OFF, 'Outer split', 'test engines held out\n(5-fold CV, or 50 random\ntest engines x 20)\nnever used for fitting,\nnormalisation or tuning', ls='--')
c2 = box(1.86, yb, 1.62, hb, S_OFF, 'Inner 5-fold CV on\ntraining engines', 'out-of-fold predictions\nfor every cycle, for each\ncap $c$ (models refit\nper inner fold)', ls='--')
c3 = box(3.63, yb, 1.72, hb, S_OFF, 'Grid search of the\ndecision settings', '$\\theta=(c, m, k, s)$\n$m\\in\\{1,3,6\\}$, $k\\in\\{1,2,3,5\\}$\n$s\\in[-12,8]$ step 0.5\n$c\\geq H+20$; maximise #\nfirst warnings with\n$e\\in[-13,+2]$')
ax.patches[-1].set_linestyle('--')
c4 = box(5.50, yb, 1.54, hb, S_OFF, 'Refit and score', 'refit regressor with $c^*$\non all training engines;\nfreeze $\\theta^*$; score test\nengines once with\n$e=\\tilde y_{t^*}-\\mathrm{RUL}_{t^*}$', ls='--')
for a, b in ((c1, c2), (c2, c3), (c3, c4)):
    arr((a[0] + a[2] + 0.01, yb + hb / 2), (b[0] - 0.01, yb + hb / 2), color='#6b4bb3')
# settings feed the online model
arr((c4[0] + c4[2] * 0.5, yb + hb + 0.01), (b5[0] + b5[2] * 0.3, yo - 0.01), color='#6b4bb3', ls=(0, (3, 2)), label='$\\theta^*$', lxy=(c4[0] + c4[2] * 0.5 + 0.13, 1.55))

# ---- window scale (small, inside grid-search box region top) drawn at bottom-right of online lane? keep compact in offline lane
sx0, sx1, sy = 0.33, 2.45, 1.98
def sx(v): return sx0 + (v + 20) / 27 * (sx1 - sx0)
ax.plot([sx0, sx1], [sy, sy], color=MUTED, lw=0.7)
ax.add_patch(Rectangle((sx(-13), sy - 0.05), sx(2) - sx(-13), 0.1, color='#9fd39f', lw=0))
for v in (-20, -13, -5.5, 0, 2, 7):
    ax.plot([sx(v)] * 2, [sy - 0.06, sy + 0.06], color=INK if v in (-13, 2) else MUTED, lw=0.7)
    ax.text(sx(v), sy - 0.15, f'{v:+g}' if v else '0', ha='center', fontsize=5.6, color=INK)
ax.text(sx(-5.5), sy + 0.09, 'correct', ha='center', fontsize=5.8, color='#1b8a1b', weight='bold')
ax.text(sx(-17), sy + 0.09, 'too early', ha='center', fontsize=5.8, color=MUTED); ax.text(sx(4.8), sy + 0.09, 'too late', ha='center', fontsize=5.8, color='#b3261e')
ax.text(sx0 - 0.08, sy - 0.02, '$e$', fontsize=6.6, ha='right', va='center', color=INK)
for ext in ('pdf', 'png'):
    fig.savefig(f'out/paper2_figs/Fig1_STW_architecture.{ext}', dpi=1000 if ext == 'png' else None, facecolor='white')
print('ok')
