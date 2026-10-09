# =========================================================
# ARDL(1,1) regressions of Table 8 -- Python equivalent of
# ardl_ytdoi.sas and ardl_spotoi.sas (SAS PROC AUTOREG)
#
#   LSGF_t = a + b * LOI_t (or LYTDOI_t) + c * LSGF_{t-1} + e_t
#
# PROC AUTOREG with no NLAG= option is ordinary least squares, so
# METHOD=ML changes nothing; the estimates are plain OLS.
# Verified against the SAS output (N = 26, Mar-2020 to Jun-2026):
#   LYTDOI model: b = 0.0792, c = 0.9108, R2 = 0.9888, AIC = -70.037
#   LOI    model: b = 0.0734, c = 0.9250, R2 = 0.9886, AIC = -69.618
#
# Input : paper_regression_data.sas7bdat (the file used by the SAS
#         programs) or, failing that, Paper_Regression_Data.xlsx,
#         looked for in the script folder, data/raw/ and the cwd.
#         Passing a path as the first argument overrides the search.
#         No SAS licence is needed to read the .sas7bdat file.
# Needs only numpy, pandas, scipy and openpyxl (no SAS, no statsmodels).
# Output: printed tables, plus ARDL_Python_Results.xlsx next to the input.
# Usage : python ardl_python.py   [optional path to the data file]
# =========================================================
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# ---------- 1. Locate and load data ----------
def find_input():
    args = [a for a in sys.argv[1:] if a.lower().endswith((".sas7bdat", ".xlsx", ".xls"))]
    if args:
        return Path(args[0])
    try:
        here = Path(__file__).resolve().parent
    except NameError:                       # running inside Jupyter
        here = Path.cwd()
    wanted = ("paper_regression_data.sas7bdat", "paper_regression_data.xlsx")
    for name in wanted:
        for folder in (here, here / "data" / "raw", Path.cwd(), Path.cwd() / "data" / "raw"):
            if folder.is_dir():
                for f in folder.iterdir():
                    if f.name.lower() == name:
                        return f
    raise FileNotFoundError("Paper_Regression_Data not found; pass its path as an argument.")


input_path = find_input()
output_path = input_path.parent / "ARDL_Python_Results.xlsx"

if input_path.suffix.lower() == ".sas7bdat":
    df = pd.read_sas(input_path, encoding="latin1")
else:
    df = pd.read_excel(input_path)
print("Data loaded from", input_path, "- shape:", df.shape)

# The Dec-2019 row only initialises the lag and has no LSGF; the
# regression sample is the 26 quarters Mar-2020 to Jun-2026.
# LAGLSGF is the supplied lagged-SGF column (as in the SAS programs).
cols = ["LSGF", "LAGLSGF", "LOI", "LYTDOI"]
for c in cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")
d = df.dropna(subset=cols).copy()
assert len(d) == 26, f"Expected N=26 quarterly observations, got {len(d)}"


# ---------- 2. ARDL(1,1) estimation ----------
def godfrey(X, e, order):
    """Godfrey (Breusch-Godfrey) LM test of order p, the form PROC AUTOREG
    reports: regress the OLS residuals on X and p lagged residuals (missing
    initial lags set to zero); LM = n * (uncentred R2) ~ chi2(p)."""
    n = len(e)
    L = np.column_stack([np.concatenate([np.zeros(i), e[:-i]]) for i in range(1, order + 1)])
    Z = np.column_stack([X, L])
    g = np.linalg.lstsq(Z, e, rcond=None)[0]
    u = e - Z @ g
    lm = n * (1 - (u @ u) / (e @ e))
    return lm, stats.chi2.sf(lm, order)


def run_ardl(regressor, label):
    y = d["LSGF"].to_numpy(float)
    X = np.column_stack([np.ones(len(d)), d[regressor].to_numpy(float), d["LAGLSGF"].to_numpy(float)])
    n, k = X.shape
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    sse = float(e @ e)
    dfe = n - k
    mse = sse / dfe
    se = np.sqrt(np.diag(mse * np.linalg.inv(X.T @ X)))
    t = b / se
    p = 2 * stats.t.sf(np.abs(t), dfe)
    r2 = 1 - sse / float(((y - y.mean()) ** 2).sum())
    # SAS PROC AUTOREG fit statistics (Gaussian ML log-likelihood,
    # counting the k regression parameters only)
    aic = n * np.log(2 * np.pi * sse / n) + n + 2 * k
    sbc = n * np.log(2 * np.pi * sse / n) + n + k * np.log(n)
    dw = float(np.sum(np.diff(e) ** 2) / sse)

    print("\n" + "=" * 70)
    print(f"ARDL(1,1): LSGF on {regressor} and LAGLSGF  [{label}]   N = {n}")
    print("=" * 70)
    tbl = pd.DataFrame({"Variable": ["Intercept", regressor, "LAGLSGF"],
                        "Estimate": b, "Std Error": se, "t Value": t, "Pr > |t|": p})
    print(tbl.round(4).to_string(index=False))
    print(f"\nR-square = {r2:.4f}   SSE = {sse:.8f}   Root MSE = {np.sqrt(mse):.5f}")
    print(f"AIC = {aic:.3f}   SBC = {sbc:.3f}   Durbin-Watson = {dw:.4f}")

    gf = []
    for j in range(1, 5):
        lm, pv = godfrey(X, e, j)
        gf.append({"Alternative": f"AR({j})", "LM": round(lm, 4), "Pr > LM": round(pv, 4)})
    gf = pd.DataFrame(gf)
    print("\nGodfrey's serial correlation test")
    print(gf.to_string(index=False))

    summ = pd.DataFrame({"Statistic": ["N", "R-square", "SSE", "Root MSE", "AIC", "SBC", "Durbin-Watson"],
                         "Value": [n, r2, sse, np.sqrt(mse), aic, sbc, dw]})
    return tbl, summ, gf


out = {}
out["YTDOI"] = run_ardl("LYTDOI", "preferred (YTDOI)")
out["SpotOI"] = run_ardl("LOI", "alternative (Spot OI)")

# ---------- 3. Export ----------
with pd.ExcelWriter(output_path, engine="openpyxl") as w:
    for key, (tbl, summ, gf) in out.items():
        tbl.to_excel(w, sheet_name=f"{key}_Coefs", index=False)
        summ.to_excel(w, sheet_name=f"{key}_Fit", index=False)
        gf.to_excel(w, sheet_name=f"{key}_Godfrey", index=False)
print(f"\nResults written to: {output_path}")
