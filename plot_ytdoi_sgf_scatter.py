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

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.lines import Line2D

# ---- Data: quarterly ARDL panel (Mar 2020 -- Jun 2026, N=26 usable quarters) ----
df = pd.read_excel(_find("SGF_corrected_07102026.xlsx", "SGF_corrected_07102026.xls"))
df = df[['MONTHYR', 'SGF', 'YTDOI']].dropna().reset_index(drop=True)

x = df['YTDOI'].values / 1e5   # lakh crore
y = df['SGF'].values           # crore

# ---- OLS fit (with intercept; descriptive only, not the paper's k-calibration method) ----
slope, intercept = np.polyfit(x, y, 1)
r = np.corrcoef(x, y)[0, 1]
r2 = r ** 2
x_line = np.array([x.min() * 0.95, x.max() * 1.05])
y_line = slope * x_line + intercept

# ---- Palette ----
COL_PT = "#4a3aa7"    # violet (SGF identity, consistent with Figure F1)
COL_FIT = "#52514e"   # neutral gray fitted line
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
    2, 1, figsize=(8.6, 7.2),
    gridspec_kw={"height_ratios": [6, 0.6], "hspace": 0.08},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

ax.plot(x_line, y_line, color=COL_FIT, linewidth=1.8, linestyle=(0, (5, 2)), zorder=2)
ax.scatter(x, y, color=COL_PT, s=55, zorder=3, edgecolor="white", linewidth=0.8, alpha=0.9)

ax.set_xlabel("YTDOI (₹ Lakh Crore, fiscal-year-to-date cumulative average)", fontsize=10)
ax.set_ylabel("Core SGF Corpus (₹ Crore, quarter-end)", fontsize=10.5)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_xlim(0, x.max() * 1.08)
ax.set_ylim(0, y.max() * 1.1)

ax.text(
    0.03, 0.95, f"N = 26 quarters (Mar 2020–Jun 2026)\nPearson r = {r:.3f}  (r² = {r2:.3f})",
    transform=ax.transAxes, fontsize=9, color=TEXT_SECONDARY, ha="left", va="top"
)

# ---- Footer: legend ----
ax_foot.axis("off")
legend_elems = [
    Line2D([0], [0], color=COL_PT, linewidth=0, marker="o", markersize=7, label="Quarterly observation"),
    Line2D([0], [0], color=COL_FIT, linewidth=1.8, linestyle=(0, (5, 2)), label="OLS fitted line (descriptive)"),
]
ax_foot.legend(handles=legend_elems, loc="center", ncol=2, frameon=False, fontsize=9.3)

fig.savefig(str(HERE / "Figure_F2_YTDOI_SGF_Scatter.png"), dpi=220, facecolor="white")
print("saved")
print(f"slope={slope:.6f} intercept={intercept:.2f} r={r:.4f} r2={r2:.4f}")
