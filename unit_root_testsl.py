# =========================================================
# Unit Root Tests (Level & 1st Diff) & Johansen Cointegration
# Annexure H
# Variables: LOI, LSGF, LFO, LCM, LVIX, LYTDOI
# Cointegration pairs: (LOI, LSGF) & (LSGF, LYTDOI)
#
# Validated benchmark (Annexure H, corrected SGF data, N=26):
#   LOI=I(0), LSGF=I(1), LFO=I(0), LCM=I(2)/ambiguous (not used
#   in any model), LVIX=I(0), LYTDOI=I(1).
#   Johansen(LOI,LSGF): rejects r<=0 (17.331>15.494), fails to
#     reject r<=1 (1.881<3.842) -> r=1, but methodologically
#     mismatched given LOI is I(0) while LSGF is I(1).
#   Johansen(LSGF,LYTDOI): rejects r<=0 (21.235>15.494) AND
#     r<=1 (4.509>3.842) -- the second rejection is interpreted
#     as small-sample size distortion (Cheung & Lai 1993;
#     Reimers 1992), conclusion r=1. This is the paper's primary
#     cointegration pairing, since LSGF and LYTDOI share the
#     same I(1) integration order.
#
# Input : Unit.xlsx (Sheet1), 26 quarterly rows, Mar-2020 to Jun-2026,
#         columns MONTHYR, LSGF, LFO, LOI, LCM, LVIX, LYTDOI
#         (all already log-transformed).
# Output: Unit_Test_Results.xlsx (sheets ADF_Tests, Johansen_LOI_LSGF,
#         Johansen_LSGF_LYTDOI), written next to the input file.
# Usage : python unit_root_tests.py            (finds Unit.xlsx automatically)
#         python unit_root_tests.py path/to/Unit.xlsx
# =========================================================
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.vector_ar.vecm import coint_johansen

# ---------- 1. Locate and load data ----------
def find_input():
    """Use the path given on the command line, else look for Unit.xlsx
    (case-insensitive) in the script folder, its data/raw subfolder, and
    the current working directory. Works as a script and in Jupyter."""
    args = [a for a in sys.argv[1:] if a.lower().endswith(".xlsx")]
    if args:
        return Path(args[0])
    try:
        here = Path(__file__).resolve().parent
    except NameError:                      # running inside Jupyter
        here = Path.cwd()
    for folder in (here, here / "data" / "raw", Path.cwd(), Path.cwd() / "data" / "raw"):
        if folder.is_dir():
            for f in folder.iterdir():
                if f.name.lower() == "unit.xlsx":
                    return f
    raise FileNotFoundError("Unit.xlsx not found; pass its path as an argument.")

input_path = Path(r"c:/data/Unit.xlsx")
output_path = Path(r"c:/data/Unit_Test_Results.xlsx")

df = pd.read_excel(input_path, sheet_name="Sheet1")
print("Raw data loaded from", input_path, "- shape:", df.shape)

# Keep the N=26 estimation sample (Mar-2020 to Jun-2026). A Dec-2019 row,
# if present in a master file, only initialises the ARDL lag and is dropped.
df["MONTHYR"] = pd.to_datetime(df["MONTHYR"])
df = df[df["MONTHYR"] >= "2020-03-01"].reset_index(drop=True)
print("Estimation sample (Mar-2020 to Jun-2026) - shape:", df.shape)

# ---------- 2. Data cleaning ----------
# All six series are read as-is from the input file (already in logs).
vars_to_test = ["LOI", "LSGF", "LFO", "LCM", "LVIX", "LYTDOI"]

for col in vars_to_test:
    df[col] = df[col].replace(["*", "#NUM!", ""], np.nan)
    df[col] = pd.to_numeric(df[col], errors="coerce")

df_clean = df.dropna(subset=vars_to_test).copy()
print("Cleaned data shape (after dropping missing values):", df_clean.shape)
assert len(df_clean) == 26, "Expected N=26 quarterly observations"

# ---------- 3. Augmented Dickey-Fuller (ADF) test ----------
def run_adf(series):
    # constant-only regression, lag length chosen by AIC (statsmodels default maxlag)
    adf_test = adfuller(series, autolag="AIC")
    return {
        "Test Statistic": round(adf_test[0], 4),
        "p-value": round(adf_test[1], 4),
        "Critical Value (5%)": round(adf_test[4]["5%"], 4),
        "Stationary (5% sig.)": "Yes" if adf_test[1] < 0.05 else "No",
    }

adf_results = []

for col in vars_to_test:
    level_res = run_adf(df_clean[col])
    diff_series = df_clean[col].diff().dropna()
    diff_res = run_adf(diff_series)

    if level_res["Stationary (5% sig.)"] == "Yes":
        integration_order = "I(0)"
    elif diff_res["Stationary (5% sig.)"] == "Yes":
        integration_order = "I(1)"
    else:
        integration_order = "I(2) or higher"

    adf_results.append({
        "Variable": col,
        "Level Stat": level_res["Test Statistic"],
        "Level p-value": level_res["p-value"],
        "Level Stationary": level_res["Stationary (5% sig.)"],
        "1st Diff Stat": diff_res["Test Statistic"],
        "1st Diff p-value": diff_res["p-value"],
        "1st Diff Stationary": diff_res["Stationary (5% sig.)"],
        "Integration Order": integration_order,
    })

adf_df = pd.DataFrame(adf_results)

print("\n" + "=" * 80)
print("ADF Unit Root Test Results (Levels vs 1st Differences)")
print("=" * 80)
print(adf_df.to_string(index=False))

# ---------- 4. Johansen cointegration test (trace) ----------
def run_johansen(data, pair_name):
    # det_order = 0: constant term in the cointegrating relation
    # k_ar_diff = 1: one lagged difference, i.e. 2 lags in levels
    #               (the "2 lags" stated in Annexure H)
    johansen_test = coint_johansen(data, det_order=0, k_ar_diff=1)

    trace_stats = johansen_test.lr1
    crit_vals = johansen_test.cvt          # columns: 90%, 95%, 99%

    results = []
    for r in range(len(data.columns)):
        results.append({
            "Variables Tested": pair_name,
            "Null Hypothesis": f"r <= {r} (Cointegration rank <= {r})",
            "Trace Statistic": round(trace_stats[r], 4),
            "Critical Value (90%)": round(crit_vals[r, 0], 4),
            "Critical Value (95%)": round(crit_vals[r, 1], 4),
            "Critical Value (99%)": round(crit_vals[r, 2], 4),
            "Reject Null (95% sig.)": "Yes" if trace_stats[r] > crit_vals[r, 1] else "No",
        })
    return pd.DataFrame(results)

# Test 1: LOI and LSGF -- secondary / mismatched pairing (LOI is I(0),
# LSGF is I(1)); reported for transparency, not as primary evidence.
print("\n" + "=" * 80)
print("Johansen Cointegration Test (Trace Test) - LOI & LSGF")
print("=" * 80)
johansen_LOI_LSGF = run_johansen(df_clean[["LOI", "LSGF"]], "LOI & LSGF")
print(johansen_LOI_LSGF.to_string(index=False))

# Test 2: LSGF and LYTDOI -- the paper's primary pairing (both I(1)).
print("\n" + "=" * 80)
print("Johansen Cointegration Test (Trace Test) - LSGF & LYTDOI")
print("=" * 80)
johansen_LSGF_LYTDOI = run_johansen(df_clean[["LSGF", "LYTDOI"]], "LSGF & LYTDOI")
print(johansen_LSGF_LYTDOI.to_string(index=False))

# ---------- 5. Export results to Excel ----------
with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    adf_df.to_excel(writer, sheet_name="ADF_Tests", index=False)
    johansen_LOI_LSGF.to_excel(writer, sheet_name="Johansen_LOI_LSGF", index=False)
    johansen_LSGF_LYTDOI.to_excel(writer, sheet_name="Johansen_LSGF_LYTDOI", index=False)

print(f"\nResults successfully written to: {output_path}")
