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

# ---- Data: quarterly ARDL panel (Mar 2020 -- Jun 2026, N=26 usable quarters) ----
df = pd.read_excel(_find("SGF_corrected_07102026.xlsx", "SGF_corrected_07102026.xls"))
df = df[['MONTHYR', 'SGF', 'OI', 'VIX']].dropna().reset_index(drop=True)
df['MONTHYR'] = pd.to_datetime(df['MONTHYR'])

assert (df['SGF'].diff().dropna() > 0).all()   # corrected series: strictly increasing in every quarter

# ---- Palette ----
COL_OI = "#1baf7a"       # aqua
COL_SGF = "#4a3aa7"      # violet
COL_VIX = "#e34948"      # red
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

fig, (ax1, ax2, ax3, ax_foot) = plt.subplots(
    4, 1, figsize=(10, 10.2),
    gridspec_kw={"height_ratios": [2.6, 2.6, 2.2, 0.7], "hspace": 0.12},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")

# ---- Panel 1: OI ----
ax1.plot(df['MONTHYR'], df['OI'] / 1e5, color=COL_OI, linewidth=2, marker="o", markersize=4,
         solid_capstyle="round", zorder=3)
ax1.set_ylabel("Open Interest\n(₹ Lakh Crore, quarter-end)", fontsize=10)
ax1.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax1.set_facecolor("white")
ax1.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)
ax1.set_ylim(bottom=0)
ax1.tick_params(axis="x", labelbottom=False)

# ---- Panel 2: SGF (step drawstyle to emphasize discrete quarterly ratchet) ----
ax2.plot(df['MONTHYR'], df['SGF'], color=COL_SGF, linewidth=2, drawstyle="steps-post",
         zorder=3)
ax2.plot(df['MONTHYR'], df['SGF'], color=COL_SGF, linewidth=0, marker="o", markersize=4, zorder=4)
ax2.set_ylabel("Core SGF Corpus\n(₹ Crore, quarter-end)", fontsize=10)
ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax2.set_facecolor("white")
ax2.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)
ax2.set_ylim(bottom=0)
ax2.tick_params(axis="x", labelbottom=False)

# ---- Panel 3: VIX ----
ax3.plot(df['MONTHYR'], df['VIX'], color=COL_VIX, linewidth=2, marker="o", markersize=4,
         solid_capstyle="round", zorder=3)
ax3.set_ylabel("India VIX\n(quarterly average)", fontsize=10)
ax3.set_facecolor("white")
ax3.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax3.spines[spine].set_visible(False)
ax3.set_ylim(bottom=0)

ax3.xaxis.set_major_locator(mdates.YearLocator())
ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax3.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
ax3.set_xlabel("Quarter", fontsize=10)
ax3.tick_params(axis="x", which="major", length=5)
ax3.tick_params(axis="x", which="minor", length=2.5, color=GRID)

# ---- Footer: legend ----
ax_foot.axis("off")
legend_elems = [
    Line2D([0], [0], color=COL_OI, linewidth=2, marker="o", markersize=4, label="Open Interest (quarter-end)"),
    Line2D([0], [0], color=COL_SGF, linewidth=2, label="Core SGF corpus (step = quarterly ratchet)"),
    Line2D([0], [0], color=COL_VIX, linewidth=2, marker="o", markersize=4, label="India VIX (quarterly average)"),
]
ax_foot.legend(handles=legend_elems, loc="center", ncol=3, frameon=False, fontsize=9.3)

fig.savefig(str(HERE / "Figure_G1_OI_SGF_VIX.png"), dpi=220, facecolor="white")
print("saved")
