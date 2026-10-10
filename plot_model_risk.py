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
import numpy as np

# ---- Data: Table 10a, Stress-Scenario Sensitivity to Model Specification ----
specs = ["Full model\n(linear + convexity\n+ lag persistence)", "Restricted B\n(linear + lag\npersistence)", "Restricted A\n(linear,\ncontemporaneous only)"]
sgf_eroded = [1289, 1166, 662]       # Rs crore
oi_loss_pct = [7.31, 6.61, 3.75]
understatement = [None, 9, 49]       # % understatement vs. full model

COL_FULL = "#4a3aa7"     # violet -- reference/correct specification
COL_RESB = "#dba220"     # amber -- caution, modest understatement
COL_RESA = "#e34948"     # red -- danger, severe understatement
colors = [COL_FULL, COL_RESB, COL_RESA]
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

fig, ax = plt.subplots(figsize=(8.6, 6.4), constrained_layout=True)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

x = np.arange(3)
width = 0.56
bars = ax.bar(x, sgf_eroded, width, color=colors, zorder=3, edgecolor="white", linewidth=0.5)

for i, (b, val, oi) in enumerate(zip(bars, sgf_eroded, oi_loss_pct)):
    ax.text(b.get_x() + b.get_width() / 2, val + 25, f"₹{val:,}cr", ha="center", va="bottom",
            fontsize=11, color=TEXT_PRIMARY, fontweight="bold")
    ax.text(b.get_x() + b.get_width() / 2, val / 2, f"{oi:.2f}%\nOI loss", ha="center", va="center",
            fontsize=8.8, color="white", fontweight="bold")

# understatement annotations between bars
for i in [1, 2]:
    y_full = sgf_eroded[0]
    y_this = sgf_eroded[i]
    ax.annotate(
        "", xy=(x[i], y_this + 60), xytext=(x[i], y_full + 60),
        arrowprops=dict(arrowstyle="<->", color=TEXT_SECONDARY, linewidth=1.0),
    )
    ax.text(x[i] + 0.32, (y_full + y_this) / 2 + 60, f"{understatement[i]}%\nunderstated",
            fontsize=8.8, color=TEXT_SECONDARY, ha="left", va="center", style="italic")

ax.axhline(sgf_eroded[0], color=COL_FULL, linewidth=0.8, linestyle=(0, (4, 3)), alpha=0.5, zorder=1)

ax.set_xticks(x)
ax.set_xticklabels(specs, fontsize=9.3)
ax.set_ylabel("SGF Eroded Under VIX 15→18 Shock (₹ Crore)", fontsize=10.5)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_ylim(0, 1550)

ax.text(0.5, -0.30, "Same illustrative shock (Section 5.5), same Table 10 coefficients — only the terms retained in the stress model differ",
        transform=ax.transAxes, fontsize=8.3, color=TEXT_SECONDARY, ha="center", va="top", style="italic")

fig.savefig(str(HERE / "Figure_56_Model_Risk.png"), dpi=220, facecolor="white")
print("saved")
