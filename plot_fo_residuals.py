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

df = pd.read_excel(_find('FO_Residuals_Dated.xlsx'), sheet_name='Sheet1')
df = df[['Date', 'residual']].dropna().reset_index(drop=True)
df['Date'] = pd.to_datetime(df['Date'])

# Four largest-magnitude residuals (verified against text: Dec 2022, Jan 2026, Dec 2023, Mar 2025)
top4 = df.reindex(df['residual'].abs().sort_values(ascending=False).index).head(4).sort_values('Date')

# Four modeled event dates (Table C1), near-zero residuals
events = {
    "2024-11-01": "Partial_Transition", "2024-12-01": "Full_Shock",
    "2026-04-01": "RBI_FrontRun", "2026-05-01": "RBI_FrontRun",
}

COL_FO = "#eb6834"
COL_EVENT = "#1baf7a"
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
    2, 1, figsize=(10.5, 5.6),
    gridspec_kw={"height_ratios": [6, 0.8], "hspace": 0.1},
    constrained_layout=True,
)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

ax.axhline(0, color=TEXT_SECONDARY, linewidth=0.9, linestyle=(0, (4, 3)), zorder=2)
ax.plot(df["Date"], df["residual"], color=COL_FO, linewidth=1.8, zorder=3)
ax.scatter(df["Date"], df["residual"], color=COL_FO, s=16, zorder=4)

# mark modeled event dates
for d in events:
    dt = pd.Timestamp(d)
    row = df[df["Date"] == dt]
    if not row.empty:
        ax.scatter(row["Date"], row["residual"], color=COL_EVENT, s=70, zorder=5,
                   edgecolor="white", linewidth=1.0, marker="D")

# annotate the four largest-magnitude residuals
for _, r in top4.iterrows():
    va = "bottom" if r["residual"] > 0 else "top"
    offset = 0.018 if r["residual"] > 0 else -0.018
    ax.annotate(f"{r['Date'].strftime('%b %Y')}: {r['residual']:+.3f}",
                xy=(r["Date"], r["residual"]), xytext=(r["Date"], r["residual"] + offset),
                fontsize=8, color=TEXT_PRIMARY, ha="center", va=va)

ax.set_ylabel("ARIMAX Residual (Log Scale)", fontsize=10.5)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.2f}"))
ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_ylim(-0.26, 0.26)
ax.set_xlim(pd.Timestamp("2021-11-01"), pd.Timestamp("2026-09-01"))

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
ax.set_xlabel("Month", fontsize=10)
ax.tick_params(axis="x", which="major", length=5)
ax.tick_params(axis="x", which="minor", length=2.5, color=GRID)

ax_foot.axis("off")
legend_elems = [
    Line2D([0], [0], color=COL_FO, linewidth=1.8, marker="o", markersize=4, label="Monthly ARIMAX residual (first 24 obs. trimmed)"),
    Line2D([0], [0], color=COL_EVENT, linewidth=0, marker="D", markersize=8, markeredgecolor="white", label="Modeled event date (Table C1, near-zero residual)"),
]
ax_foot.legend(handles=legend_elems, loc="center", ncol=2, frameon=False, fontsize=9)

fig.savefig(str(HERE / "Figure_C1_ARIMAX_Residuals.png"), dpi=220, facecolor="white")
print("saved")
