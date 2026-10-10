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
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# ---- Panel 1: NCL clearing-charge revenue as share of NSE operating income ----
# Full annual series 2007-2026 from Financials_NSE_NCL_Charges.xlsx (NSE operating income; NCL clearing charges paid).
rv = pd.read_excel(_find('Financials_NSE_NCL_Charges.xlsx'))
rev_years = rv['Year'].tolist()      # fiscal years ending March of the stated year
rev_x = [y + 0.25 for y in rev_years]  # plot at 31 March (year + 3/12)
rev_pct = (rv['Clg charges Paid'] / rv['NSE'] * 100).tolist()
ann = {2007: "10.9% (2007)", 2011: "14.2% (2011, peak)", 2018: "5.4% (2018)", 2024: "9.2% (2024)", 2026: "5.3% (2026, low)"}

# ---- Panel 2: Core SGF requirement, actual + forecast (same construction as Figure 2) ----
df = pd.read_excel(_find("SGF_corrected_07102026.xlsx", "SGF_corrected_07102026.xls"))
hist = df[['MONTHYR', 'SGF']].dropna().reset_index(drop=True)
hist['MONTHYR'] = pd.to_datetime(hist['MONTHYR'])
hist = hist[hist['MONTHYR'] >= '2020-03-01'].reset_index(drop=True)
hist['YEAR_DEC'] = hist['MONTHYR'].dt.year + (hist['MONTHYR'].dt.month - 1) / 12

K_SPOT = 0.005397
arima_qtr = [
    ("2026-09-01", 2849853), ("2026-12-01", 2912667), ("2027-03-01", 3000269),
    ("2027-06-01", 3077918), ("2027-09-01", 3159203), ("2027-12-01", 3238811),
    ("2028-03-01", 3318819),
]
fc = pd.DataFrame(arima_qtr, columns=["MONTHYR", "OI"])
fc["MONTHYR"] = pd.to_datetime(fc["MONTHYR"])
fc["SGF"] = fc["OI"] * K_SPOT
fc['YEAR_DEC'] = fc['MONTHYR'].dt.year + (fc['MONTHYR'].dt.month - 1) / 12

COL_REV = "#2a78d6"     # blue, NCL identity (consistent with Figure 1)
COL_HIST = "#4a3aa7"    # violet, SGF identity (consistent with Figures F1/F2/2)
COL_FC = "#9183d1"      # lighter violet, forecast
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
    3, 1, figsize=(10.5, 8.6),
    gridspec_kw={"height_ratios": [2.6, 3.2, 0.8], "hspace": 0.1},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")

# ---- Panel 1: revenue share ----
ax1.plot(rev_x, rev_pct, color=COL_REV, linewidth=2, zorder=3, solid_capstyle="round")
ax1.scatter(rev_x, rev_pct, color=COL_REV, s=22, zorder=4, edgecolor="white", linewidth=0.8)
key = [2007, 2011, 2018, 2024, 2026]
ax1.scatter([k + 0.25 for k in key], [rev_pct[rev_years.index(k)] for k in key], color=COL_REV, s=70, zorder=5, edgecolor="white", linewidth=1.1)
offs = {2007: (0, -1.3, "top"), 2011: (0, 0.7, "bottom"), 2018: (0, -1.3, "top"), 2024: (0, 0.7, "bottom"), 2026: (-0.2, -1.3, "top")}
for k in key:
    dx, dy, va = offs[k]
    y0 = rev_pct[rev_years.index(k)]
    ax1.annotate(ann[k], xy=(k + 0.25, y0), xytext=(k + 0.25 + dx, y0 + dy), fontsize=8.5, color=COL_REV, ha="center", va=va)
ax1.set_ylabel("NCL revenue share of\nNSE operating income (%)", fontsize=9.8)
ax1.set_ylim(0, 17)
ax1.set_xlim(2005, 2029)
ax1.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
ax1.set_facecolor("white")
for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)
ax1.tick_params(axis="x", labelbottom=False)
ax1.text(0.99, 0.97, "Annual series, fiscal years ending March 2007\u20132026 (20 observations)",
          transform=ax1.transAxes, fontsize=7.8, color=TEXT_SECONDARY, ha="right", va="top", style="italic")

# ---- Panel 2: SGF requirement (actual + forecast) ----
width = 0.17
ax2.bar(hist["YEAR_DEC"], hist["SGF"] / 1e3, width=width, color=COL_HIST, zorder=3)
ax2.bar(fc["YEAR_DEC"], fc["SGF"] / 1e3, width=width, color=COL_FC, zorder=3)
ax2.set_ylabel("Core SGF requirement\n(₹ Crore, thousands)", fontsize=9.8)
ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax2.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
ax2.set_facecolor("white")
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)
ax2.set_xlim(2005, 2029)
ax2.set_ylim(0, 20)
ax2.set_xlabel("Year", fontsize=10)
ax2.xaxis.set_major_locator(plt.MultipleLocator(5))
ax2.text(0.01, 0.95, "No comparable SGF series exists before 2020",
          transform=ax2.transAxes, fontsize=7.8, color=TEXT_SECONDARY, ha="left", va="top", style="italic")

# ---- Footer legend ----
ax_foot.axis("off")
legend_elems = [
    Line2D([0], [0], color=COL_REV, marker="o", linewidth=2, markersize=5, label="NCL revenue share (annual, 2007\u20132026)"),
    Patch(facecolor=COL_HIST, label="Core SGF requirement, actual (2020–2026)"),
    Patch(facecolor=COL_FC, label="Core SGF requirement, forecast (2026–2028)"),
]
ax_foot.legend(handles=legend_elems, loc="center", ncol=3, frameon=False, fontsize=9)

fig.savefig(str(HERE / "Figure_51_Revenue_vs_SGF.png"), dpi=220, facecolor="white")
print("saved")
