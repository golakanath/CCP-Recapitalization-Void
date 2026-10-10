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

# ---- Historical OI (unadjusted, all trading days retained -- Section 3.2), Jan 2020 -- Jul 2026 ----
oi = pd.read_excel(_find('OI_MDA.xlsx'))
oi.columns = [c.strip() for c in oi.columns]
oi['Month'] = pd.to_datetime(oi['Month'])

BREAK = pd.Timestamp("2024-10-01")
DECLINE_END = pd.Timestamp("2026-04-01")   # decline regime: Oct 2024 -- Apr 2026
SERIES_END = oi['Month'].max()              # recovery regime: Apr 2026 -- Jul 2026 (data end)

COL_OI = "#1baf7a"        # teal, OI identity (consistent with Figures F1/D1)
COL_DECLINE = "#e34948"   # red, stress/decline identity (consistent with VIX)
COL_RECOVERY = "#1baf7a"  # teal, recovery (same hue as OI itself, lighter tint)
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
    2, 1, figsize=(10.5, 6.8),
    gridspec_kw={"height_ratios": [5, 0.95], "hspace": 0.06},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# ---- Sub-regime shading (drawn first, below the line) ----
ax.axvspan(BREAK, DECLINE_END, color=COL_DECLINE, alpha=0.10, zorder=0, linewidth=0)
ax.axvspan(DECLINE_END, SERIES_END, color=COL_RECOVERY, alpha=0.14, zorder=0, linewidth=0)

# ---- OI series ----
ax.plot(oi["Month"], oi["OI"] / 1e5, color=COL_OI, linewidth=2,
        solid_capstyle="round", zorder=3)

# ---- PELT break marker ----
ax.axvline(BREAK, color=TEXT_PRIMARY, linewidth=1.3, linestyle=(0, (4, 2)), zorder=4)

ax.set_ylabel("Open Interest (₹ Lakh Crore)", fontsize=10.5)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=1)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_ylim(0, 32)
ax.set_xlim(oi["Month"].min(), pd.Timestamp("2026-08-15"))

ymax = ax.get_ylim()[1]

# ---- Region labels ----
ax.text(pd.Timestamp("2022-03-01"), ymax * 0.95, "Pre-break growth regime\n(≈+49% annualized)",
        fontsize=8.6, color=TEXT_SECONDARY, ha="center", va="top", style="italic")
ax.text(pd.Timestamp("2025-07-01"), ymax * 0.95, "Post-break decline\n(≈−16% annualized)",
        fontsize=8.6, color=COL_DECLINE, ha="center", va="top", style="italic")
ax.text(pd.Timestamp("2026-06-01"), ymax * 0.62, "Recovery /\nRBI front-run\n(Apr–Jun 2026)",
        fontsize=8.0, color="#128a5c", ha="center", va="top", style="italic")

ax.annotate("PELT break\nOct 2024", xy=(BREAK, oi.loc[oi["Month"] == BREAK, "OI"].values[0] / 1e5),
            xytext=(pd.Timestamp("2023-11-01"), 6.5), fontsize=8.6, color=TEXT_PRIMARY,
            ha="center", va="top",
            arrowprops=dict(arrowstyle="-", color=TEXT_PRIMARY, linewidth=0.8, shrinkA=2, shrinkB=4))

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
ax.set_xlabel("Month", fontsize=10)
ax.tick_params(axis="x", which="major", length=5)
ax.tick_params(axis="x", which="minor", length=2.5, color=GRID)

# ---- Footer: legend ----
ax_foot.axis("off")
legend_elems = [
    Line2D([0], [0], color=COL_OI, linewidth=2, label="OI, monthly MDA (Jan 2020–Jul 2026)"),
    Line2D([0], [0], color=TEXT_PRIMARY, linewidth=1.3, linestyle=(0, (4, 2)), label="PELT-detected structural break (Oct 2024)"),
    Patch(facecolor=COL_DECLINE, alpha=0.25, label="Post-break decline sub-regime (Oct 2024–Apr 2026)"),
    Patch(facecolor=COL_RECOVERY, alpha=0.30, label="Recovery sub-regime (Apr–Jul 2026)"),
]
ax_foot.legend(handles=legend_elems, loc="center", ncol=2, frameon=False, fontsize=8.8)

fig.savefig(str(HERE / "Figure_35_OI_Structural_Break.png"), dpi=220, facecolor="white")
print("saved")
