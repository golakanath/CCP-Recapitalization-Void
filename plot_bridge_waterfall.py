from pathlib import Path
try:
    HERE = Path(__file__).resolve().parent
except NameError:                       # running inside Jupyter
    HERE = Path.cwd()

def _find(*names):
    """Locate an input file (case-insensitive) in this folder, the repository
    root (one level up) or the current folder; the first name found wins."""
    for name in names:
        for folder in (HERE, HERE.parent, Path.cwd(), Path.cwd().parent):
            if folder.is_dir():
                for f in folder.iterdir():
                    if f.name.lower() == name.lower():
                        return str(f)
    raise FileNotFoundError(f"{names[0]} not found; place it in the repository root or next to this script.")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np

# ---- Disclosed anchor points only ----
START = 4636.0          # NCL standalone capital & reserves, Mar 2026 (Section 5.2/4.2)
GAP_75 = 8798.0          # Capital gap closed at 75% target under r* (Table 9a, Spot-OI basis)
END_75 = START + GAP_75  # = 13,434cr, the 75% target reserve level, Mar 2028
BLACKSWAN_CEILING = 17912.0  # Full (100%-basis) SGF 2028 projection, Spot-OI basis (Table 6) --
                              # stands in for the full Black Swan-scale requirement; NOT itself
                              # labeled "Black Swan requirement" in the paper, used as the closest
                              # disclosed proxy for the full-coverage ceiling.

# ---- Illustrative-only intra-period path: straight-line accrual across 8 quarters (FY27-FY28) ----
# The paper does NOT disclose the FY27/FY28 split; this is a modeling assumption for visualization,
# not a reported trajectory, and is labeled as such throughout.
quarters = ["Mar\n2026", "Jun\n2026", "Sep\n2026", "Dec\n2026", "Mar\n2027", "Jun\n2027", "Sep\n2027", "Dec\n2027", "Mar\n2028"]
n_steps = 8
step = GAP_75 / n_steps
levels = [START + i * step for i in range(n_steps + 1)]

COL_BAR = "#4a3aa7"
COL_STEP = "#9183d1"
COL_CEIL = "#e34948"
COL_TARGET = "#2a78d6"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e2dd"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10.5,
    "axes.edgecolor": GRID,
    "axes.linewidth": 0.8,
    "text.color": TEXT_PRIMARY,
    "axes.labelcolor": TEXT_SECONDARY,
    "xtick.color": TEXT_SECONDARY,
    "ytick.color": TEXT_SECONDARY,
})

fig, (ax, ax_foot) = plt.subplots(
    2, 1, figsize=(10.5, 7.2),
    gridspec_kw={"height_ratios": [6, 1.1], "hspace": 0.1},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

x = np.arange(len(quarters))

# shaded exposure band: illustrative reserves path to Black Swan ceiling
ax.fill_between(x, levels, BLACKSWAN_CEILING, color=COL_CEIL, alpha=0.08, zorder=1)

# floating waterfall bars
width = 0.55
for i in range(n_steps):
    bottom = levels[i]
    top = levels[i + 1]
    color = COL_BAR if i in (0,) else COL_STEP
    ax.bar(x[i + 1], top - bottom, width, bottom=bottom, color=COL_STEP, zorder=3,
           edgecolor="white", linewidth=0.6)
# start bar (full height) and end bar emphasized
ax.bar(x[0], START, width, bottom=0, color=COL_BAR, zorder=3)
ax.bar(x[-1], END_75, width, bottom=0, color=COL_BAR, zorder=4, alpha=0)  # invisible full-height end marker for outline
ax.plot([x[-1] - width/2, x[-1] + width/2], [END_75, END_75], color=COL_BAR, linewidth=2.2, zorder=5)

# connecting step lines
for i in range(n_steps):
    ax.plot([x[i] + width/2, x[i+1] - width/2], [levels[i+1], levels[i+1]], color=TEXT_SECONDARY,
            linewidth=0.7, linestyle=(0, (2, 2)), zorder=2)

# reference lines
ax.axhline(BLACKSWAN_CEILING, color=COL_CEIL, linewidth=1.8, linestyle=(0, (6, 3)), zorder=5)
ax.axhline(END_75, color=COL_TARGET, linewidth=1.2, linestyle=(0, (1, 1.5)), zorder=2, alpha=0.7)

ax.text(x[-1] + 0.15, BLACKSWAN_CEILING, "Full (100%-basis) SGF requirement: ₹17,912cr\n(proxy for Black Swan-scale ceiling)",
        fontsize=8.2, color=COL_CEIL, va="center", ha="left")
ax.text(x[0] - 0.45, END_75 + 250, "75% sufficiency target: ₹13,434cr (Mar 2028)",
        fontsize=8.2, color=COL_TARGET, va="bottom", ha="left")

ax.text(x[0], START + 350, f"₹{START:,.0f}cr", ha="center", va="bottom", fontsize=10, fontweight="bold", color=TEXT_PRIMARY)
ax.text(x[-1], END_75 + 350, f"₹{END_75:,.0f}cr", ha="center", va="bottom", fontsize=10, fontweight="bold", color=TEXT_PRIMARY)

ax.annotate(
    "Ramp-up risk window: reserves remain below both\nthe 75% target and the full ceiling throughout\nthe accumulation period, not only before Mar 2026",
    xy=(x[3], levels[3] + (BLACKSWAN_CEILING - levels[3]) * 0.4), xytext=(x[1], 15500),
    fontsize=8.5, color=TEXT_SECONDARY, ha="left",
    arrowprops=dict(arrowstyle="-", color=TEXT_SECONDARY, linewidth=0.8, shrinkA=2, shrinkB=4),
)

ax.set_xticks(x)
ax.set_xticklabels(quarters, fontsize=9)
ax.set_ylabel("₹ Crore", fontsize=10.5)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_ylim(0, 20500)
ax.set_xlim(-0.6, len(quarters) - 0.4)

ax.text(0.01, 0.03, "Intra-period path (Mar 2026 → Mar 2028) is an illustrative straight-line\naccrual assumption — the paper does not disclose the actual FY27/FY28 split.",
        transform=ax.transAxes, fontsize=8, color=TEXT_SECONDARY, ha="left", va="bottom", style="italic")

# ---- Footer legend ----
ax_foot.axis("off")
legend_elems = [
    Patch(facecolor=COL_BAR, label="Disclosed anchor points (Mar 2026 start, Mar 2028 target)"),
    Patch(facecolor=COL_STEP, label="Illustrative quarterly accrual (straight-line assumption)"),
    Line2D([0], [0], color=COL_TARGET, linewidth=1.2, linestyle=(0, (1, 1.5)), label="75% sufficiency target (₹13,434cr)"),
    Line2D([0], [0], color=COL_CEIL, linewidth=1.8, linestyle=(0, (6, 3)), label="Full SGF requirement (₹17,912cr, ceiling proxy)"),
]
ax_foot.legend(handles=legend_elems, loc="center", ncol=2, frameon=False, fontsize=8.8)

fig.savefig(str(HERE / "Figure_63_Bridge_Waterfall.png"), dpi=220, facecolor="white")
print("saved")
