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

# ---- Default waterfall composition (Clause 16, Section 2.2 / 6.3) ----
# Only segments with a disclosed basis for sizing are shown to scale.
# Layers I-II (defaulting member's own margins; insurance) have no public
# rupee figure (no default has occurred) and are shown as a fixed-width,
# hatched "not to scale" block, clearly labeled as such.
NOT_DISCLOSED_WIDTH = 4000   # nominal placeholder width, NOT a rupee figure
CC_BUFFER = 525              # 5% of Rs10,500cr Category-A MRC floor (Section 2.2)
SGF_PRE = 17630.93           # Core SGF, YTDOI-based Mar-2028 target (Section 4.2/5.5)
SGF_POST = 16342             # Core SGF after illustrative VIX 15->18 shock (Section 5.5)

rows = ["After illustrative\nVIX 15→18 shock\n(Section 5.5)", "Before stress\n(Section 4.2 target)"]
sgf_vals = [SGF_POST, SGF_PRE]

COL_UNDISCLOSED = "#c9c7c2"
COL_CCBUFFER = "#75736b"
COL_SGF = "#4a3aa7"
COL_SGF_ERODED = "#c7c1ea"
COL_LAYER7 = "#e34948"
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
    2, 1, figsize=(10.5, 5.6),
    gridspec_kw={"height_ratios": [4, 1.3], "hspace": 0.12},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

y = np.arange(2)
bar_h = 0.5

for yi, sgf_val, row_label in zip(y, sgf_vals, rows):
    left = 0
    # Layers I-II: not sized (undisclosed), hatched, fixed nominal width
    ax.barh(yi, NOT_DISCLOSED_WIDTH, left=left, height=bar_h, color=COL_UNDISCLOSED,
            edgecolor="white", linewidth=1, hatch="///", zorder=3)
    left += NOT_DISCLOSED_WIDTH
    # Layer III: CC buffer, 5% of MRC
    ax.barh(yi, CC_BUFFER, left=left, height=bar_h, color=COL_CCBUFFER,
            edgecolor="white", linewidth=1, zorder=3)
    left += CC_BUFFER
    # Core SGF (pre- or post-stress)
    sgf_color = COL_SGF if sgf_val == SGF_PRE else COL_SGF_ERODED
    ax.barh(yi, sgf_val, left=left, height=bar_h, color=COL_SGF, edgecolor="white",
            linewidth=1, zorder=3)
    left += sgf_val
    # Layer VII marker: capped additional member contribution = Rs0
    ax.plot([left, left], [yi - bar_h/2 - 0.05, yi + bar_h/2 + 0.05], color=COL_LAYER7,
            linewidth=3, zorder=5, solid_capstyle="round")
    label_y = yi + bar_h/2 + 0.38 if yi == y[1] else yi - bar_h/2 - 0.38
    va = "bottom" if yi == y[1] else "top"
    ax.annotate("Layer VII = \u20b90", xy=(left, yi + (bar_h/2 + 0.04 if va=="bottom" else -(bar_h/2 + 0.04))),
                xytext=(left + 250, label_y),
                fontsize=9, color=COL_LAYER7, ha="left", va=va, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=COL_LAYER7, linewidth=0.8, shrinkA=1, shrinkB=2))

ax.set_yticks(y)
ax.set_yticklabels(rows, fontsize=9.5)
ax.set_xlabel("₹ Crore (Layers I-II shown schematically, not to scale -- see note below)", fontsize=9.3)
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.set_xlim(0, 27000)
ax.grid(axis="x", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.tick_params(axis="y", length=0)

ax.text(0, 1.62, "Default waterfall, Clause 16 (Section 2.2): layers consumed in order, left to right.\nLayers I-II (defaulting member's margins; insurance) have no disclosed rupee figure -- shown hatched, fixed width, not to scale.",
        fontsize=8.2, color=TEXT_SECONDARY, ha="left", va="top", transform=ax.transData)

# ---- Footer legend ----
ax_foot.axis("off")
legend_elems = [
    Patch(facecolor=COL_UNDISCLOSED, hatch="///", edgecolor="white", label="Layers I-II: member margins + insurance (not sized; undisclosed)"),
    Patch(facecolor=COL_CCBUFFER, label="Layer III: CC buffer, 5% of MRC (≈₹525cr)"),
    Patch(facecolor=COL_SGF, label="Core SGF (₹17,631cr target; ₹16,342cr after illustrative shock)"),
    Line2D([0], [0], color=COL_LAYER7, linewidth=3, label="Layer VII: additional member contribution (₹0, structurally since 2016)"),
]
ax_foot.legend(handles=legend_elems, loc="center", ncol=2, frameon=False, fontsize=8.6)

fig.savefig(str(HERE / "Figure_65_Waterfall_Layers.png"), dpi=220, facecolor="white")
print("saved")
