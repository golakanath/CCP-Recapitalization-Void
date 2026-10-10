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

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

# ---- Data: Table 9a, Sensitivity of the Sufficiency Threshold to OI Estimation Window ----
windows = [
    "Full sample\n(Jan 2020–Jul 2026)",
    "Post-Oct-2024\nregime only",
    "Excl. Apr–Jul 2026\nfront-run months",
]
r_star = [40.28, 33.80, 20.13]
sgf_proj = [17912, 16025, 12043]
cap_gap = [8798, 7383, 4396]
notes = ["Headline recommendation\n(conservative upper bound)", "Most defensible\ncentral estimate", "Assumes front-run activity\nleaves no lasting trace"]

COL_BAR = "#4a3aa7"
COL_BAND = "#ede9f7"
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

fig, ax = plt.subplots(figsize=(10, 5.6), constrained_layout=True)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# shaded 20-40% band
ax.axvspan(20.13, 40.28, color=COL_BAND, zorder=0)

y = np.arange(3)[::-1]  # Full sample on top
ax.barh(y, r_star, height=0.5, color=COL_BAR, zorder=3)

for yi, r, gap, note in zip(y, r_star, cap_gap, notes):
    ax.text(r + 1.2, yi + 0.17, f"{r:.2f}%", va="center", ha="left", fontsize=11.5,
            color=TEXT_PRIMARY, fontweight="bold")
    ax.text(1.0, yi, f"Capital gap: ₹{gap:,}cr", va="center", ha="left", fontsize=8.6,
            color="white")
    ax.text(r + 1.2, yi - 0.2, note.replace("\n", " "), va="center", ha="left", fontsize=7.6,
            color=TEXT_SECONDARY, style="italic")

ax.set_yticks(y)
ax.set_yticklabels(windows, fontsize=10)
ax.set_xlabel("Sufficiency-Threshold Recovery Rate r* (%)", fontsize=10.5)
ax.set_xlim(0, 62)
ax.set_ylim(-1.05, 2.7)
ax.grid(axis="x", color=GRID, linewidth=0.7, zorder=1)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.tick_params(axis="y", length=0)

ax.annotate("Defensible range: ≈20–40%", xy=(30, 2.55), fontsize=9.5,
            color=TEXT_SECONDARY, ha="center", va="top", style="italic")

ax.text(0, -0.85, "Stress-model choice (Figure 4, Section 5.6) is a separate, qualitative risk —\nnot recomputed as an r* range and not included in the band above.",
        fontsize=8, color=TEXT_SECONDARY, ha="left", va="top", transform=ax.transData)

fig.savefig(str(HERE / "Figure_53_Threshold_Sensitivity.png"), dpi=220, facecolor="white")
print("saved")
