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

# ---- Historical OI (unadjusted, all trading days retained -- Section 3.2) ----
oi_hist = pd.read_excel(_find('OI_MDA.xlsx'))
oi_hist.columns = [c.strip() for c in oi_hist.columns]
oi_hist['Month'] = pd.to_datetime(oi_hist['Month'])

# ---- ARIMA(2,1,2) forecast + 95% CI, Table E1 (Annexure E), verbatim ----
arima_rows = [
    ("2026-08-01", 2792344, 2581600, 3003087),
    ("2026-09-01", 2849853, 2509885, 3189821),
    ("2026-10-01", 2854455, 2443774, 3265135),
    ("2026-11-01", 2897715, 2410800, 3384631),
    ("2026-12-01", 2912667, 2368346, 3456987),
    ("2027-01-01", 2948287, 2344539, 3552034),
    ("2027-02-01", 2968755, 2314299, 3623212),
    ("2027-03-01", 3000269, 2294815, 3705724),
    ("2027-04-01", 3023669, 2271861, 3775477),
    ("2027-05-01", 3052968, 2255215, 3850722),
    ("2027-06-01", 3077918, 2236944, 3918891),
    ("2027-07-01", 3106013, 2222458, 3989567),
    ("2027-08-01", 3131771, 2207370, 4056173),
    ("2027-09-01", 3159203, 2194626, 4123781),
    ("2027-10-01", 3185376, 2181806, 4188947),
    ("2027-11-01", 3212435, 2170497, 4254373),
    ("2027-12-01", 3238811, 2159363, 4318258),
    ("2028-01-01", 3265650, 2149247, 4382053),
    ("2028-02-01", 3292115, 2139410, 4444821),
    ("2028-03-01", 3318819, 2130291, 4507347),
]
arima = pd.DataFrame(arima_rows, columns=["Month", "OI", "Lo95", "Hi95"])
arima["Month"] = pd.to_datetime(arima["Month"])

# ---- XGBoost forecast, OI_Forecast_Results.xlsx, Future_Forecasts sheet, verbatim ----
xgb_rows = [
    ("2026-08-01", 2755216), ("2026-09-01", 2486272), ("2026-10-01", 2348126),
    ("2026-11-01", 2220336), ("2026-12-01", 2174322), ("2027-01-01", 2189090),
    ("2027-02-01", 2213859), ("2027-03-01", 2243424), ("2027-04-01", 2247746),
    ("2027-05-01", 2252116), ("2027-06-01", 2273861), ("2027-07-01", 2288423),
    ("2027-08-01", 2299751), ("2027-09-01", 2322692), ("2027-10-01", 2330953),
    ("2027-11-01", 2327783), ("2027-12-01", 2324232), ("2028-01-01", 2281622),
    ("2028-02-01", 2250758), ("2028-03-01", 2252945),
]
xgb = pd.DataFrame(xgb_rows, columns=["Month", "OI"])
xgb["Month"] = pd.to_datetime(xgb["Month"])

forecast_start = pd.Timestamp("2026-07-01")

# ---- Palette (consistent with Figure F1: OI = teal; rejected-model gray, as with Naive in Figure C2) ----
COL_OI = "#1baf7a"
COL_XGB = "#75736b"
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
    2, 1, figsize=(10, 6.8),
    gridspec_kw={"height_ratios": [5, 0.9], "hspace": 0.06},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# ---- ARIMA 95% CI ribbon ----
ax.fill_between(arima["Month"], arima["Lo95"] / 1e5, arima["Hi95"] / 1e5,
                 color=COL_OI, alpha=0.15, zorder=1, linewidth=0)

# ---- Series ----
ax.plot(oi_hist["Month"], oi_hist["OI"] / 1e5, color=COL_OI, linewidth=2,
        solid_capstyle="round", zorder=3)
ax.plot(arima["Month"], arima["OI"] / 1e5, color=COL_OI, linewidth=2, linestyle=(0, (5, 2)),
        solid_capstyle="round", zorder=3)
ax.plot(xgb["Month"], xgb["OI"] / 1e5, color=COL_XGB, linewidth=2, linestyle=(0, (1, 1.6)),
        zorder=2)

# ---- Historical / forecast divider ----
ax.axvline(forecast_start, color=TEXT_SECONDARY, linewidth=0.9, linestyle="-", alpha=0.5, zorder=2)

ax.set_ylabel("Open Interest (₹ Lakh Crore)", fontsize=10.5)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_ylim(0, 50)
ax.set_xlim(oi_hist["Month"].min(), arima["Month"].max())

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

# ---- Footer: legend ----
ax_foot.axis("off")
legend_elems = [
    Line2D([0], [0], color=COL_OI, linewidth=2, label="OI actual (Jan 2020–Jul 2026)"),
    Line2D([0], [0], color=COL_OI, linewidth=2, linestyle=(0, (5, 2)), label="ARIMA(2,1,2) forecast (95% CI shaded)"),
    Line2D([0], [0], color=COL_XGB, linewidth=2, linestyle=(0, (1, 1.6)), label="XGBoost forecast"),
]
ax_foot.legend(handles=legend_elems, loc="center", ncol=3, frameon=False, fontsize=9.3)

fig.savefig(str(HERE / "Figure_D1_OI_ARIMA_XGB.png"), dpi=220, facecolor="white")
print("saved")
