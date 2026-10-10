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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from matplotlib.lines import Line2D

# ---- Data ----
cm = pd.read_excel(_find('CM_OUTLIER_RMVD.xlsx'))
fo = pd.read_excel(_find('FO_OUTLIER_RMVD.xlsx'))
cm['Month'] = pd.to_datetime(cm['Month'])
fo['Month'] = pd.to_datetime(fo['Month'])

# ---- Excluded dates (Table 2) ----
muhurat_dates = pd.to_datetime([
    "2020-11-14", "2021-11-04", "2022-10-24", "2023-11-12",
    "2024-11-01", "2025-10-21",
])
bcp_dates = pd.to_datetime(["2024-03-02", "2024-05-18"])

# ---- Palette (validated: skill default categorical slots 1 & 2) ----
COL_CM = "#2a78d6"     # blue
COL_FO = "#eb6834"     # orange
COL_MUHURAT = "#75736b"   # neutral gray, dashed
COL_BCP = "#75736b"       # same neutral gray, dotted (distinguished by linestyle)
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

fig, (ax1, ax2, ax_foot) = plt.subplots(
    3, 1, figsize=(10, 7.9),
    gridspec_kw={"height_ratios": [3, 3, 1.1], "hspace": 0.18},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")

# ---- Panel 1: CM ----
ax1.plot(cm['Month'], cm['CM'], color=COL_CM, linewidth=2, solid_capstyle="round", zorder=3)
ax1.set_ylabel("CM Monthly Daily\nAverage (₹ Crore)", fontsize=10)
ax1.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax1.set_facecolor("white")
ax1.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)
ax1.set_ylim(bottom=0)
ax1.set_xlim(cm['Month'].min(), cm['Month'].max())
ax1.tick_params(axis="x", labelbottom=False)

# ---- Panel 2: FO (separate axis, same scale family avoided per dual-axis rule) ----
ax2.plot(fo['Month'], fo['FO'] / 1e5, color=COL_FO, linewidth=2, solid_capstyle="round", zorder=3)
ax2.set_ylabel("FO Monthly Daily\nAverage (₹ Lakh Crore)", fontsize=10)
ax2.set_facecolor("white")
ax2.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)
ax2.set_ylim(bottom=0)
ax2.set_xlim(fo['Month'].min(), fo['Month'].max())

# ---- Excluded-date markers on both panels ----
for ax in (ax1, ax2):
    for d in muhurat_dates:
        ax.axvline(d, color=COL_MUHURAT, linewidth=1.1, linestyle=(0, (4, 2)), alpha=0.75, zorder=2)
    for d in bcp_dates:
        ax.axvline(d, color=COL_BCP, linewidth=1.1, linestyle=(0, (1, 1.3)), alpha=0.9, zorder=2)

# ---- X axis formatting ----
ax2.xaxis.set_major_locator(mdates.YearLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax2.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
ax2.set_xlabel("Month", fontsize=10)
ax2.tick_params(axis="x", which="major", length=5)
ax2.tick_params(axis="x", which="minor", length=2.5, color=GRID)

# ---- Footer panel: legend + source note (kept inside the layout engine) ----
ax_foot.axis("off")
legend_elems = [
    Line2D([0], [0], color=COL_CM, linewidth=2, label="CM Monthly Daily Average"),
    Line2D([0], [0], color=COL_FO, linewidth=2, label="FO Monthly Daily Average"),
    Line2D([0], [0], color=COL_MUHURAT, linewidth=1.3, linestyle=(0, (4, 2)),
           label="Excluded: Muhurat session (6 dates)"),
    Line2D([0], [0], color=COL_BCP, linewidth=1.3, linestyle=(0, (1, 1.3)),
           label="Excluded: BCP/DR test (2 dates)"),
]
ax_foot.legend(
    handles=legend_elems, loc="center", ncol=2, frameon=False,
    fontsize=9.5
)

fig.savefig(str(HERE / "Figure_A1_CM_FO_MDA.png"), dpi=220, facecolor="white")
print("saved")
