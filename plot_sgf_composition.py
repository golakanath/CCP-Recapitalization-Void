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
from matplotlib.patches import Patch
import numpy as np

# ---- Data: Table 7, Core SGF Contributor Breakdown (two reconciled snapshots only) ----
dates = ["Sep 30, 2021", "Jun 30, 2026"]
total = [2126.28, 9068.99]          # Rs crore
ncl_pct = [41.9, 55.7]
nse_pct = [57.2, 41.4]
# The remainder (0.8%, 2.9%) is contributions by other parties in the audited note
# (BSE, MSE and others), not clearing members: the paper states that members
# contributed nothing directly at either date (Section 4.1).
other_pct = [100 - ncl_pct[i] - nse_pct[i] for i in range(2)]
cm_pct = [0.0, 0.0]

ncl_cr = [total[i] * ncl_pct[i] / 100 for i in range(2)]
nse_cr = [total[i] * nse_pct[i] / 100 for i in range(2)]
other_cr = [total[i] * other_pct[i] / 100 for i in range(2)]

COL_NCL = "#2a78d6"     # blue
COL_NSE = "#eb6834"     # orange
COL_OTHER = "#c9c6bf"   # light neutral (small, non-substantive residual)
COL_CM = "#75736b"      # gray -- negligible/absent, consistent with Naive/XGBoost "rejected" convention
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
    2, 1, figsize=(7.4, 6.6),
    gridspec_kw={"height_ratios": [6, 0.9], "hspace": 0.1},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

x = np.array([0, 1])
width = 0.46

b1 = ax.bar(x, ncl_cr, width, color=COL_NCL, zorder=3, label="NCL")
b2 = ax.bar(x, nse_cr, width, bottom=ncl_cr, color=COL_NSE, zorder=3, label="NSE (Parent)")
bottom2 = [ncl_cr[i] + nse_cr[i] for i in range(2)]
b3 = ax.bar(x, other_cr, width, bottom=bottom2, color=COL_OTHER, zorder=3, label="BSE, MSE, others")

# in-bar percentage labels
for i in range(2):
    ax.text(x[i], ncl_cr[i] / 2, f"{ncl_pct[i]:.1f}%", ha="center", va="center",
            fontsize=9.5, color="white", fontweight="bold")
    ax.text(x[i], ncl_cr[i] + nse_cr[i] / 2, f"{nse_pct[i]:.1f}%", ha="center", va="center",
            fontsize=9.5, color="white", fontweight="bold")

# explicit zero-contribution annotation for Clearing Members
for i in range(2):
    ax.annotate(
        "CM: 0.0%\n(no direct\ncontribution)",
        xy=((x[i], total[i]) if i == 0 else (x[i] - 0.23, total[i] * 0.97)), xytext=((x[i] + 0.34, total[i] * 1.13) if i == 0 else (x[i] - 0.62, total[i] * 0.86)),
        fontsize=8.3, color=COL_CM, ha="center", va="bottom",
        arrowprops=dict(arrowstyle="-", color=COL_CM, linewidth=0.8, shrinkA=2, shrinkB=4),
    )

# total labels above bars
for i in range(2):
    ax.text(x[i], total[i] + total[i] * 0.02, f"₹{total[i]:,.0f} cr", ha="center", va="bottom",
            fontsize=9.5, color=TEXT_PRIMARY, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(dates, fontsize=10.5)
ax.set_ylabel("Core SGF contributions (₹ Crore)", fontsize=10.5)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_ylim(0, max(total) * 1.32)
ax.set_xlim(-0.5, 1.5)

# ---- Footer: legend ----
ax_foot.axis("off")
legend_elems = [
    Patch(facecolor=COL_NCL, label="NCL"),
    Patch(facecolor=COL_NSE, label="NSE (Parent)"),
    Patch(facecolor=COL_OTHER, label="BSE, MSE, others"),
    Patch(facecolor=COL_CM, label="Clearing Members (0.0% at both dates)"),
]
ax_foot.legend(handles=legend_elems, loc="center", ncol=2, frameon=False, fontsize=9)

fig.savefig(str(HERE / "Figure_41_SGF_Composition.png"), dpi=220, facecolor="white")
print("saved")
