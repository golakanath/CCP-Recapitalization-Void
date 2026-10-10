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

# ---- Historical quarterly SGF (actual), Mar 2020 -- Jun 2026 ----
df = pd.read_excel(_find("SGF_corrected_07102026.xlsx", "SGF_corrected_07102026.xls"))
hist = df[['MONTHYR', 'SGF']].dropna().reset_index(drop=True)
hist['MONTHYR'] = pd.to_datetime(hist['MONTHYR'])
hist = hist[hist['MONTHYR'] >= '2020-03-01'].reset_index(drop=True)  # drop Dec-2019 base row

# ---- Forecast quarterly SGF, Sep 2026 -- Mar 2028: k (Spot OI basis, Table 6) x ARIMA(2,1,2) OI forecast (Table E1) ----
K_SPOT = 0.005397
arima_qtr = [
    ("2026-09-01", 2849853, 2509885, 3189821),
    ("2026-12-01", 2912667, 2368346, 3456987),
    ("2027-03-01", 3000269, 2294815, 3705724),
    ("2027-06-01", 3077918, 2236944, 3918891),
    ("2027-09-01", 3159203, 2194626, 4123781),
    ("2027-12-01", 3238811, 2159363, 4318258),
    ("2028-03-01", 3318819, 2130291, 4507347),
]
fc = pd.DataFrame(arima_qtr, columns=["MONTHYR", "OI", "Lo95", "Hi95"])
fc["MONTHYR"] = pd.to_datetime(fc["MONTHYR"])
fc["SGF"] = fc["OI"] * K_SPOT
fc["Lo95_SGF"] = fc["Lo95"] * K_SPOT
fc["Hi95_SGF"] = fc["Hi95"] * K_SPOT

RESERVES = 4636.0  # NCL standalone capital & reserves, Mar 2026 -- the only disclosed figure (Section 4.2 / 5.2)

COL_HIST = "#4a3aa7"       # violet, SGF identity (consistent with Fig F1/F2)
COL_FC = "#9183d1"         # lighter violet, forecast bars
COL_RESERVES = "#e34948"   # red, cautionary/stress identity (consistent with VIX)
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
    2, 1, figsize=(11, 7.2),
    gridspec_kw={"height_ratios": [5, 1], "hspace": 0.08},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

width = 60  # days, approx one quarter width for date-based bars

ax.bar(hist["MONTHYR"], hist["SGF"] / 1e3, width=width, color=COL_HIST, zorder=3,
       label="_hist")
ax.bar(fc["MONTHYR"], fc["SGF"] / 1e3, width=width, color=COL_FC, zorder=3, label="_fc")
# forecast uncertainty whiskers (thin, since this is a derived not directly-modeled interval)
ax.errorbar(fc["MONTHYR"], fc["SGF"] / 1e3,
            yerr=[(fc["SGF"] - fc["Lo95_SGF"]) / 1e3, (fc["Hi95_SGF"] - fc["SGF"]) / 1e3],
            fmt="none", ecolor=COL_FC, elinewidth=1.1, capsize=3, zorder=4, alpha=0.8)

ax.axhline(RESERVES / 1e3, color=COL_RESERVES, linewidth=2, linestyle=(0, (6, 3)), zorder=5)

forecast_start = pd.Timestamp("2026-07-15")
ax.axvline(forecast_start, color=TEXT_SECONDARY, linewidth=0.9, linestyle="-", alpha=0.5, zorder=2)

ax.set_ylabel("₹ Crore (thousands)", fontsize=10.5)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_ylim(0, 22)
ax.set_xlim(pd.Timestamp("2019-12-01"), pd.Timestamp("2028-06-01"))

ymax = ax.get_ylim()[1]
ax.text(forecast_start, ymax * 0.97, "  Forecast →", fontsize=8.5, color=TEXT_SECONDARY,
        ha="left", va="top", style="italic")
ax.text(forecast_start, ymax * 0.97, "← Historical  ", fontsize=8.5, color=TEXT_SECONDARY,
        ha="right", va="top", style="italic")

ax.annotate(
    "NCL standalone capital & reserves: ₹4,636cr (Mar 2026,\nonly disclosed figure — held flat; no disclosed\nreplenishment mechanism, see Section 5)",
    xy=(pd.Timestamp("2021-06-01"), RESERVES / 1e3), xytext=(pd.Timestamp("2020-01-01"), 15.5),
    fontsize=8.3, color=COL_RESERVES, ha="left", va="top",
    arrowprops=dict(arrowstyle="-", color=COL_RESERVES, linewidth=0.8, shrinkA=2, shrinkB=4),
)

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
ax.set_xlabel("Quarter", fontsize=10)
ax.tick_params(axis="x", which="major", length=5)
ax.tick_params(axis="x", which="minor", length=2.5, color=GRID)

# ---- Footer: legend ----
ax_foot.axis("off")
legend_elems = [
    Patch(facecolor=COL_HIST, label="Core SGF corpus, actual (Mar 2020–Jun 2026)"),
    Patch(facecolor=COL_FC, label="Core SGF requirement, forecast (k × ARIMA OI, 95% CI whiskers)"),
    Line2D([0], [0], color=COL_RESERVES, linewidth=2, linestyle=(0, (6, 3)), label="NCL standalone capital & reserves (₹4,636cr, Mar 2026 — static reference)"),
]
ax_foot.legend(handles=legend_elems, loc="center", ncol=1, frameon=False, fontsize=9.2)

fig.savefig(str(HERE / "Figure_42_SGF_vs_Reserves.png"), dpi=220, facecolor="white")
print("saved")
print(fc[["MONTHYR","SGF"]])
