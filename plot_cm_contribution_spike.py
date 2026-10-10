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
from matplotlib.patches import Patch

# ---- Monthly Core SGF member-contribution series, Jan 2020 -- Jul 2026 (Section 6.2 narrative) ----
# NCL's monthly disclosures report Rs0.00 in every segment for the entire sample period except
# May 2025 (Rs115.98cr, FO segment only), reverting to Rs0.00 by Jul 2025. No other month has a
# disclosed non-zero member contribution; this is a complete, documented series, not a sample.
months = pd.date_range("2020-01-01", "2026-07-01", freq="MS")
values = pd.Series(0.0, index=months)
values[pd.Timestamp("2025-05-01")] = 115.98

COL_ZERO = "#9c9a94"      # neutral gray -- the near-universal zero baseline
COL_SPIKE = "#e34948"     # red -- the single disclosed anomaly
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

fig, ax = plt.subplots(figsize=(10.5, 5.4), constrained_layout=True)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

colors = [COL_SPIKE if v > 0 else COL_ZERO for v in values]
ax.bar(values.index, values.values, width=22, color=colors, zorder=3)

ax.annotate(
    "May 2025: ₹115.98cr\n(FO segment only)\nReverted to ₹0.00 by Jul 2025",
    xy=(pd.Timestamp("2025-05-01"), 115.98), xytext=(pd.Timestamp("2023-01-01"), 95),
    fontsize=9.5, color=COL_SPIKE, ha="left", va="center", fontweight="bold",
    arrowprops=dict(arrowstyle="-", color=COL_SPIKE, linewidth=1.0, shrinkA=2, shrinkB=6),
)

ax.set_ylabel("Core SGF Member Contribution (₹ Crore)", fontsize=10.5)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_ylim(0, 135)
ax.set_xlim(pd.Timestamp("2019-10-15"), pd.Timestamp("2026-09-15"))

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
ax.set_xlabel("Month", fontsize=10)
ax.tick_params(axis="x", which="major", length=5)
ax.tick_params(axis="x", which="minor", length=2.5, color=GRID)

ax.text(0.01, 0.97, "Zero in every other disclosed month, Jan 2020–Jul 2026 (complete series, per NCL's monthly disclosures)",
        transform=ax.transAxes, fontsize=8.3, color=TEXT_SECONDARY, ha="left", va="top", style="italic")

legend_elems = [
    Patch(facecolor=COL_ZERO, label="₹0.00 (structurally zero since 2016, Section 2.2)"),
    Patch(facecolor=COL_SPIKE, label="Non-zero disclosed month (May 2025 only)"),
]
ax.legend(handles=legend_elems, loc="upper left", bbox_to_anchor=(0.01, 0.88), frameon=False, fontsize=9)

fig.savefig(str(HERE / "Figure_64_CM_Contribution_Spike.png"), dpi=220, facecolor="white")
print("saved")
