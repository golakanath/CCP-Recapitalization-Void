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
hist = hist[hist['MONTHYR'] >= '2020-03-01'].reset_index(drop=True)

# ---- ARIMA(2,1,2) OI forecast + 95% CI, Table E1 (Annexure E), verbatim; k = Spot OI basis (Table 6) ----
K_SPOT = 0.005397
arima_rows = [
    ("2026-08-01", 2792344, 2581600, 3003087), ("2026-09-01", 2849853, 2509885, 3189821),
    ("2026-10-01", 2854455, 2443774, 3265135), ("2026-11-01", 2897715, 2410800, 3384631),
    ("2026-12-01", 2912667, 2368346, 3456987), ("2027-01-01", 2948287, 2344539, 3552034),
    ("2027-02-01", 2968755, 2314299, 3623212), ("2027-03-01", 3000269, 2294815, 3705724),
    ("2027-04-01", 3023669, 2271861, 3775477), ("2027-05-01", 3052968, 2255215, 3850722),
    ("2027-06-01", 3077918, 2236944, 3918891), ("2027-07-01", 3106013, 2222458, 3989567),
    ("2027-08-01", 3131771, 2207370, 4056173), ("2027-09-01", 3159203, 2194626, 4123781),
    ("2027-10-01", 3185376, 2181806, 4188947), ("2027-11-01", 3212435, 2170497, 4254373),
    ("2027-12-01", 3238811, 2159363, 4318258), ("2028-01-01", 3265650, 2149247, 4382053),
    ("2028-02-01", 3292115, 2139410, 4444821), ("2028-03-01", 3318819, 2130291, 4507347),
]
fc = pd.DataFrame(arima_rows, columns=["MONTHYR", "OI", "Lo95", "Hi95"])
fc["MONTHYR"] = pd.to_datetime(fc["MONTHYR"])
fc["SGF"] = fc["OI"] * K_SPOT
fc["Lo95_SGF"] = fc["Lo95"] * K_SPOT
fc["Hi95_SGF"] = fc["Hi95"] * K_SPOT

COL_HIST = "#4a3aa7"
COL_FC = "#4a3aa7"
COL_FAN = "#4a3aa7"
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
    2, 1, figsize=(10.5, 6.6),
    gridspec_kw={"height_ratios": [6, 0.8], "hspace": 0.08},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# fan: widening 95% CI, using progressively lighter alpha bands for a visual gradient
n = len(fc)
for i in range(n):
    pass
ax.fill_between(fc["MONTHYR"], fc["Lo95_SGF"] / 1e3, fc["Hi95_SGF"] / 1e3,
                 color=COL_FAN, alpha=0.16, zorder=1, linewidth=0, label="_fan95")
# an inner, narrower illustrative band at ~half-width for a visual "fan" gradient (still from the same 95% CI, just a lighter-alpha inner wedge, not a separately estimated interval)
mid_lo = fc["SGF"] - (fc["SGF"] - fc["Lo95_SGF"]) * 0.5
mid_hi = fc["SGF"] + (fc["Hi95_SGF"] - fc["SGF"]) * 0.5
ax.fill_between(fc["MONTHYR"], mid_lo / 1e3, mid_hi / 1e3, color=COL_FAN, alpha=0.16, zorder=1, linewidth=0)

ax.plot(hist["MONTHYR"], hist["SGF"] / 1e3, color=COL_HIST, linewidth=2.2, zorder=3)
ax.plot(fc["MONTHYR"], fc["SGF"] / 1e3, color=COL_FC, linewidth=2.2, linestyle=(0, (5, 2)), zorder=3)

forecast_start = pd.Timestamp("2026-07-15")
ax.axvline(forecast_start, color=TEXT_SECONDARY, linewidth=0.9, linestyle="-", alpha=0.5, zorder=2)

final = fc.iloc[-1]
ax.annotate(
    f"Mar 2028: ₹{final['SGF']/1e3:,.1f}k cr central\n95% CI: ₹{final['Lo95_SGF']/1e3:,.1f}k–{final['Hi95_SGF']/1e3:,.1f}k cr",
    xy=(final["MONTHYR"], final["Hi95_SGF"] / 1e3), xytext=(pd.Timestamp("2024-06-01"), 23),
    fontsize=9, color=TEXT_PRIMARY, ha="left",
    arrowprops=dict(arrowstyle="-", color=TEXT_SECONDARY, linewidth=0.8, shrinkA=2, shrinkB=4),
)

ax.set_ylabel("Core SGF Requirement (₹ Crore, thousands)", fontsize=10.5)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_ylim(0, 26)
ax.set_xlim(hist["MONTHYR"].min(), fc["MONTHYR"].max())

ymax = ax.get_ylim()[1]
ax.text(forecast_start, ymax * 0.97, "  Forecast →", fontsize=8.5, color=TEXT_SECONDARY,
        ha="left", va="top", style="italic")
ax.text(forecast_start, ymax * 0.97, "← Historical  ", fontsize=8.5, color=TEXT_SECONDARY,
        ha="right", va="top", style="italic")

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
ax.set_xlabel("Month", fontsize=10)
ax.tick_params(axis="x", which="major", length=5)
ax.tick_params(axis="x", which="minor", length=2.5, color=GRID)

ax.text(0.01, 0.03, "This uncertainty is not propagated into a rate-based solvency curve in this paper (Section 7) —\nthe fan shows the forecast's own width, not a recommendation sensitivity.",
        transform=ax.transAxes, fontsize=7.8, color=TEXT_SECONDARY, ha="left", va="bottom", style="italic")

ax_foot.axis("off")
legend_elems = [
    Line2D([0], [0], color=COL_HIST, linewidth=2.2, label="Core SGF, actual (Mar 2020–Jun 2026)"),
    Line2D([0], [0], color=COL_FC, linewidth=2.2, linestyle=(0, (5, 2)), label="Central forecast (k × ARIMA OI point estimate)"),
    Patch(facecolor=COL_FAN, alpha=0.28, label="Widening 95% confidence interval"),
]
ax_foot.legend(handles=legend_elems, loc="center", ncol=3, frameon=False, fontsize=9)

fig.savefig(str(HERE / "Figure_71_SGF_Fan.png"), dpi=220, facecolor="white")
print("saved")
print(final)
