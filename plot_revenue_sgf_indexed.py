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

# Actual data only. Common base: March 2020 = 100 for both series.
rv = pd.read_excel(_find('Financials_NSE_NCL_Charges.xlsx')).set_index('Year')
inc = rv.loc[2020:2026, 'Clg charges Paid']                      # NSE clearing & settlement charges paid to NCL, Rs crore
inc_dates = [pd.Timestamp(f"{y}-03-31") for y in inc.index]       # fiscal years ending March
inc_idx = (inc / inc.loc[2020] * 100).tolist()

df = pd.read_excel(_find("SGF_corrected_07102026.xlsx", "SGF_corrected_07102026.xls"))
h = df[['MONTHYR', 'SGF']].dropna().reset_index(drop=True)
h['MONTHYR'] = pd.to_datetime(h['MONTHYR'])
h = h[h['MONTHYR'] >= '2020-03-01'].reset_index(drop=True)
h['IDX'] = h['SGF'] / h['SGF'].iloc[0] * 100
print("income idx:", [round(x) for x in inc_idx]); print("SGF idx Mar26/Jun26:", round(h.loc[h.MONTHYR=='2026-03-01','IDX'].iloc[0]), round(h.IDX.iloc[-1]))

COL_INC, COL_SGF, TS, GRID = "#2a78d6", "#4a3aa7", "#52514e", "#e4e2dd"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5, "axes.edgecolor": GRID, "axes.linewidth": 0.8,
                     "text.color": "#0b0b0b", "axes.labelcolor": TS, "xtick.color": TS, "ytick.color": TS})
fig, (ax, axf) = plt.subplots(2, 1, figsize=(10.5, 6.2), gridspec_kw={"height_ratios": [5.2, 0.8], "hspace": 0.08}, constrained_layout=True)
fig.patch.set_facecolor("white"); ax.set_facecolor("white")
ax.axhline(100, color=TS, linewidth=0.8, alpha=0.4, zorder=1)
ax.plot(h["MONTHYR"], h["IDX"], color=COL_SGF, linewidth=2, zorder=3)
ax.plot(inc_dates, inc_idx, color=COL_INC, linewidth=2, marker="o", markersize=5.5, markeredgecolor="white", zorder=4)
ax.set_ylim(0, 850)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.set_ylabel("Index, March 2020 = 100", fontsize=10.2)
ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
for s in ["top", "right"]: ax.spines[s].set_visible(False)
ax.set_xlim(pd.Timestamp("2019-09-01"), pd.Timestamp("2026-12-01"))
ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_xlabel("Year (income: fiscal year ending March; SGF: quarter-end)", fontsize=9.6)

def lab(x, y, t, c, dy=18, ha="center", va="bottom", dx=0):
    ax.annotate(t, xy=(x, y), xytext=(x + pd.Timedelta(days=dx), y + dy), fontsize=8.5, color=c, ha=ha, va=va)
for i, y in enumerate(inc.index):
    if y in (2020, 2024, 2025, 2026):
        if y != 2026:
            lab(inc_dates[i], inc_idx[i], f"{inc_idx[i]:,.0f}", COL_INC, dy=24)
        else:
            lab(inc_dates[i], inc_idx[i], f"{inc_idx[i]:,.0f}\n(FY2026)", COL_INC, dy=0, ha="right", va="center", dx=-22)
lab(h.MONTHYR.iloc[-1], h.IDX.iloc[-1], f"{h.IDX.iloc[-1]:,.0f}\n(Jun 2026)", COL_SGF, dy=-30, va="top", ha="left", dx=15)
ax.text(inc_dates[0], 760, "Base: NCL income ₹178.66 crore (FY2020);\nCore SGF ₹3,149.13 crore (Mar 2020)", fontsize=8.3, color=TS, style="italic", va="top", ha="left", transform=ax.transData)

axf.axis("off")
axf.legend(handles=[
    Line2D([0], [0], color=COL_INC, marker="o", linewidth=2, markersize=5.5, label="NCL clearing income (annual, FY2020–FY2026)"),
    Line2D([0], [0], color=COL_SGF, linewidth=2, label="Core SGF requirement (quarterly, Mar 2020–Jun 2026)"),
], loc="center", ncol=2, frameon=False, fontsize=9.2)
fig.savefig(str(HERE / "Figure_52_Revenue_SGF_Indexed.png"), dpi=220, facecolor="white")
print("saved")
