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
from matplotlib.patches import Patch

# ---- Historical FO (outlier-adjusted, same series as Figure A1 / Section 3.4) ----
fo_hist = pd.read_excel(_find('FO_OUTLIER_RMVD.xlsx'))
fo_hist['Month'] = pd.to_datetime(fo_hist['Month'])

# ---- ARIMAX forecast path, Table E1 (Annexure E), verbatim ----
fc_rows = [
    ("2026-08-01", 45262651, 37594105, 54495448),
    ("2026-09-01", 46464083, 35747819, 60392805),
    ("2026-10-01", 47678482, 34597771, 65704741),
    ("2026-11-01", 48905503, 33787575, 70787804),
    ("2026-12-01", 50144798, 33183381, 75775904),
    ("2027-01-01", 51396010, 32718477, 80735722),
    ("2027-02-01", 52658781, 32354293, 85705696),
    ("2027-03-01", 53932743, 32066344, 90710087),
    ("2027-04-01", 55217529, 31838046, 95765157),
    ("2027-05-01", 56512763, 31657617, 100882276),
    ("2027-06-01", 57818070, 31516367, 106069625),
    ("2027-07-01", 59133068, 31407700, 111333201),
    ("2027-08-01", 60457376, 31326485, 116677447),
    ("2027-09-01", 61790608, 31268652, 122105654),
    ("2027-10-01", 63132378, 31230917, 127620242),
    ("2027-11-01", 64482298, 31210589, 133222948),
    ("2027-12-01", 65839978, 31205440, 138914970),
    ("2028-01-01", 67205029, 31213599, 144697059),
    ("2028-02-01", 68577062, 31233485, 150569602),
    ("2028-03-01", 69955687, 31263747, 156532678),
]
fc = pd.DataFrame(fc_rows, columns=["Month", "FO", "Lo95", "Hi95"])
fc["Month"] = pd.to_datetime(fc["Month"])

# ---- Naive baseline (Table 3b's worst-performing model: repeat last actual value) ----
last_actual = fo_hist["FO"].iloc[-1]
naive = pd.DataFrame({
    "Month": pd.date_range("2026-08-01", periods=20, freq="MS"),
    "FO": [last_actual] * 20,
})

# ---- Intervention periods (Section 3.4 dummy definitions, verbatim) ----
partial_transition = (pd.Timestamp("2024-11-01"), pd.Timestamp("2024-12-01"))
full_shock = (pd.Timestamp("2024-12-01"), pd.Timestamp("2028-03-31"))
rbi_frontrun = (pd.Timestamp("2026-04-01"), pd.Timestamp("2026-07-01"))
forecast_start = pd.Timestamp("2026-07-01")

# ---- Palette ----
COL_FO = "#eb6834"        # orange (same as Figure A1, same series identity)
COL_NAIVE = "#75736b"     # neutral gray
COL_BAND_PT = "#2a78d6"   # blue (Partial Transition)
COL_BAND_FS = "#4a3aa7"   # violet (Full Shock)
COL_BAND_RF = "#1baf7a"   # aqua (RBI Front-Run)
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
    2, 1, figsize=(10, 7.3),
    gridspec_kw={"height_ratios": [5, 1.05], "hspace": 0.06},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# ---- Shaded intervention bands (drawn first, behind everything) ----
ax.axvspan(*partial_transition, color=COL_BAND_PT, alpha=0.20, zorder=0, linewidth=0)
ax.axvspan(*full_shock, color=COL_BAND_FS, alpha=0.08, zorder=0, linewidth=0)
ax.axvspan(*rbi_frontrun, color=COL_BAND_RF, alpha=0.20, zorder=0, linewidth=0)

# ---- Forecast CI ribbon ----
ax.fill_between(fc["Month"], fc["Lo95"] / 1e5, fc["Hi95"] / 1e5,
                 color=COL_FO, alpha=0.15, zorder=1, linewidth=0)

# ---- Series ----
ax.plot(fo_hist["Month"], fo_hist["FO"] / 1e5, color=COL_FO, linewidth=2,
        solid_capstyle="round", zorder=3, label="_hist")
ax.plot(fc["Month"], fc["FO"] / 1e5, color=COL_FO, linewidth=2, linestyle=(0, (5, 2)),
        solid_capstyle="round", zorder=3, label="_fc")
ax.plot(naive["Month"], naive["FO"] / 1e5, color=COL_NAIVE, linewidth=1.6,
        linestyle=(0, (1, 1.6)), zorder=2, label="_naive")

# ---- Historical / forecast divider ----
ax.axvline(forecast_start, color=TEXT_SECONDARY, linewidth=0.9, linestyle="-", alpha=0.5, zorder=2)
ax.text(forecast_start, ax.get_ylim()[1] if False else None, "", visible=False)  # placeholder, ylim set below

ax.set_ylabel("FO Monthly Daily Average (₹ Lakh Crore)", fontsize=10.5)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_ylim(0, 800)
ax.set_xlim(fo_hist["Month"].min(), fc["Month"].max())

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
    Line2D([0], [0], color=COL_FO, linewidth=2, label="FO actual (Jan 2020–Jul 2026)"),
    Line2D([0], [0], color=COL_FO, linewidth=2, linestyle=(0, (5, 2)), label="FO ARIMAX forecast (95% CI shaded)"),
    Line2D([0], [0], color=COL_NAIVE, linewidth=1.6, linestyle=(0, (1, 1.6)), label="Naive forecast (repeat last value)"),
    Patch(facecolor=COL_BAND_PT, alpha=0.35, label="Partial Transition (Nov 2024)"),
    Patch(facecolor=COL_BAND_FS, alpha=0.22, label="Full Shock (Dec 2024–onward)"),
    Patch(facecolor=COL_BAND_RF, alpha=0.35, label="RBI Front-Run (Apr–Jun 2026)"),
]
ax_foot.legend(handles=legend_elems, loc="center", ncol=3, frameon=False, fontsize=9)

fig.savefig(str(HERE / "Figure_C2_FO_Forecast.png"), dpi=220, facecolor="white")
print("saved")
