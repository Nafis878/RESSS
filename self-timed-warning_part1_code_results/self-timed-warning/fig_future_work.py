"""Fig. 9 of the manuscript: planned uses of the warning model (future work schematic). Writes paper2/img/Fig9_future_work.png."""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.6})
fig, ax = plt.subplots(figsize=(7.2, 3.9)); ax.set_xlim(0, 100); ax.set_ylim(0, 54); ax.axis('off')
BLUE, ORANGE, GREY, INK = '#1f5a96', '#c8783c', '#6b6b6b', '#222222'
def box(x, y, w, h, text, ec=INK, dashed=False, fc='white', bold=False, fs=7.6):
    p = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.25,rounding_size=1.2', ec=ec, fc=fc, lw=1.1, ls=(0, (3, 2)) if dashed else '-')
    ax.add_patch(p); ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=fs, color=INK, fontweight='bold' if bold else 'normal', wrap=True)
def arrow(x0, y0, x1, y1, c=INK):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle='-|>', lw=0.9, color=c, shrinkA=1, shrinkB=1))
# centre: the warning model
cx, cw = 36, 28
box(cx, 44.5, cw, 7, 'Sensor histories of\nthe monitored units', ec=GREY)
box(cx, 35.5, cw, 7, 'Regime normalisation and\ncausal feature encoder')
box(cx, 24.5, cw, 8, 'Horizon-focused regressor:\nhealth indicator calibrated\nin cycles to failure')
box(cx, 13.5, cw, 8, 'Debounced trigger:\none alarm per unit at time $t^*$\n(Sections 4.4, 6.3)', bold=False)
for y0, y1 in [(44.5, 42.5), (35.5, 32.5), (24.5, 21.5)]: arrow(50, y0, 50, y1)
box(cx, 1.5, cw, 8, 'Leakage-safe nested evaluation,\ncontrols and hashed protocols\n(carries over to both uses)', ec=GREY, fc='#f4f4f4')

# left: test and maintenance policies
ax.text(15.5, 52, 'Test and maintenance policies', ha='center', fontsize=8.4, fontweight='bold', color=BLUE)
L = [(41.5, 'Replacement with lead time,\npriced by cost (Section 6.6)', False),
     (31.0, 'Spare-part ordering and\nfleet grouping of visits', True),
     (20.5, 'On-demand test or inspection\nwith a baseline interval', True),
     (10.0, 'Fallback outside the training\nconditions (age, interval)', True)]
for y, t, d in L:
    box(2, y, 27, 7.5, t, ec=BLUE, dashed=d); arrow(cx, 17.5, 29.4, y + 3.75, BLUE)
# right: fault detection and diagnosis
ax.text(84.5, 52, 'Fault detection and diagnosis', ha='center', fontsize=8.4, fontweight='bold', color=ORANGE)
R = [(41.5, 'Detection delay and false alarms\nvs CUSUM, EWMA, Hotelling T²', True),
     (31.0, 'Mode-specific alarms\n(diagnosis of the fault mode)', True),
     (20.5, 'Two-stage design for abrupt\nfaults: onset detector → timing', True),
     (10.0, 'Sensor-fault flags from\nresidual-like signals', True)]
for y, t, d in R:
    box(71, y, 27, 7.5, t, ec=ORANGE, dashed=d); arrow(cx + cw, 17.5, 70.6, y + 3.75, ORANGE)
fig.tight_layout(pad=0.2); fig.savefig('paper2/img/Fig9_future_work.png', dpi=300); print('ok')
