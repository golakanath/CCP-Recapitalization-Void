#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Small-sample ARDL bounds test for a levels relationship  --  Spot OI specification.

Paper:  "The CCP Recapitalization Void: Pre-Funding Systemic Risk in India's
        Equity & Equity Derivatives Market" (Annexure H).

What it does
------------
1. Reads the quarterly panel (MONTHYR, SGF, OI and, for the YTDOI version, YTDOI).
2. Builds   LSGF = ln(SGF)   and   LX = ln(OI)   directly from the raw columns.
3. Estimates the unrestricted error-correction form of the ARDL (Pesaran, Shin and
   Smith, 2001; Case III: unrestricted intercept, no trend, k = 1):

       D.LSGF_t = a + pi1 * LSGF_{t-1} + pi2 * LX_{t-1} + g * D.LX_t + e_t

4. Tests H0: pi1 = pi2 = 0 (no levels relationship) with the bounds F-statistic.
5. Gives SMALL-SAMPLE critical values for the I(0) and I(1) bounds, simulated for
   the sample size actually used (the published asymptotic bounds are too small for
   about 25 observations; Narayan, 2005, tabulates n >= 30 only).

Usage
-----
    python bounds_test_spot_oi.py                        # looks for SGF_OI_LAGSGF.xlsx next to this script
    python bounds_test_spot_oi.py path/to/data.xlsx      # or give the data file explicitly

Requires: numpy, pandas, openpyxl.  Results are also written to ./output/ (CSV).
The random seed is fixed, so the simulated critical values reproduce exactly.
"""
import os
import sys

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- settings --
DATA_FILE = "SGF_OI_LAGSGF.xlsx"      # data file (xlsx/xls/csv) in the same folder as this script
REGRESSOR = "OI"          # raw regressor column: "OI" (Spot OI) or "YTDOI"
SIM_REPS = 20000             # replications for the simulated critical values
SEED_SIM = 20261019
# -----------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "output")


# ------------------------------------------------------------------ helpers --
def find_col(df, names):
    for n in names:
        if n in df.columns:
            return n
    raise KeyError(f"None of the columns {names} found; available: {list(df.columns)}")


def read_data(path):
    if not os.path.isabs(path) and not os.path.exists(path):
        path = os.path.join(HERE, path)
    if not os.path.exists(path):
        sys.exit(f"Data file not found: {path}\n"
                 f"Put it next to this script or pass its path as an argument.")
    return pd.read_csv(path) if path.lower().endswith(".csv") else pd.read_excel(path)


def ols(y, X):
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    e = y - X @ b
    n, k = X.shape
    s2 = e @ e / (n - k)
    se = np.sqrt(np.diag(s2 * XtX_inv))
    r2 = 1.0 - (e @ e) / np.sum((y - y.mean()) ** 2)
    return b, se, e, r2


def bounds_F(y, x):
    """F for pi1 = pi2 = 0 in  dy_t = a + pi1*y_{t-1} + pi2*x_{t-1} + g*dx_t + e.
    y, x are levels of length n+1."""
    dy, dx = np.diff(y), np.diff(x)
    n = len(dy)
    Xu = np.column_stack([np.ones(n), y[:-1], x[:-1], dx])
    Xr = np.column_stack([np.ones(n), dx])
    eu = dy - Xu @ np.linalg.lstsq(Xu, dy, rcond=None)[0]
    er = dy - Xr @ np.linalg.lstsq(Xr, dy, rcond=None)[0]
    return ((er @ er - eu @ eu) / 2.0) / ((eu @ eu) / (n - 4))


def simulated_bounds(n, reps, seed):
    """Critical values of the bounds F-statistic for n usable observations.
    Null: y is a driftless random walk (no levels relationship).
    I(0) bound: regressor stationary; I(1) bound: regressor a random walk."""
    rng = np.random.default_rng(seed)
    out = {}
    for label, integrated in (("I(0)", False), ("I(1)", True)):
        f = np.empty(reps)
        for r in range(reps):
            y = np.cumsum(rng.standard_normal(n + 1))
            u = rng.standard_normal(n + 1)
            x = np.cumsum(u) if integrated else u
            f[r] = bounds_F(y, x)
        out[label] = {lvl: float(np.percentile(f, 100 - lvl)) for lvl in (10, 5, 1)}
    return out


# --------------------------------------------------------------------- main --
def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DATA_FILE
    df = read_data(path)

    sgf_col = find_col(df, ["SGF1", "SGF"])
    date_col = find_col(df, ["MONTHYR", "Month", "DATE"])
    if REGRESSOR not in df.columns:
        sys.exit(f"Column {REGRESSOR} not found in the data file.")

    # logs are rebuilt from the raw columns, never read from stored log columns
    d = pd.DataFrame({"date": pd.to_datetime(df[date_col]),
                      "LSGF": np.log(df[sgf_col].astype(float)),
                      "LX": np.log(df[REGRESSOR].astype(float))})
    stored = {"OI": "LOI", "YTDOI": "LYTDOI"}.get(REGRESSOR)
    for raw_log, mine in (("LSGF", "LSGF"), (stored, "LX")):
        if raw_log in df.columns:
            diff = np.nanmax(np.abs(df[raw_log].astype(float).values - d[mine].values))
            if diff > 1e-6:
                print(f"WARNING: stored column {raw_log} differs from ln(raw) by up to "
                      f"{diff:.6f}; the script uses ln(raw).")

    # first row (Dec 2019) only supplies the starting SGF level; X begins one quarter later
    d = d.sort_values("date").reset_index(drop=True)
    d = d[d["LX"].notna()].reset_index(drop=True)
    y = d["LSGF"].values
    x = d["LX"].values
    dy, dx = np.diff(y), np.diff(x)
    n = len(dy)

    print(f"Specification : {REGRESSOR} (log), bounds test, Case III, k = 1")
    print(f"Data file     : {path}")
    print(f"Sample        : {d['date'].iloc[1].date()} to {d['date'].iloc[-1].date()}, "
          f"usable observations n = {n}\n")

    # ---- unrestricted error-correction regression --------------------------
    X = np.column_stack([np.ones(n), y[:-1], x[:-1], dx])
    b, se, resid, r2 = ols(dy, X)
    names = ["const", "pi1  LSGF(t-1)", "pi2  LX(t-1)", "g    D.LX(t)"]
    print("Unrestricted error-correction regression  (dependent: D.LSGF)")
    print(f"{'':16s}{'coef':>10s}{'std err':>10s}{'t':>9s}")
    for nm, bi, si in zip(names, b, se):
        print(f"{nm:16s}{bi:10.4f}{si:10.4f}{bi / si:9.3f}")
    print(f"R-squared = {r2:.4f}\n")

    F = bounds_F(y, x)
    print(f"Bounds F-statistic (H0: pi1 = pi2 = 0): {F:.3f}")
    print(f"PSS t-statistic on pi1                 : {b[1] / se[1]:.3f}\n")

    # ---- simulated small-sample critical values ----------------------------
    print(f"Simulating critical values for n = {n} ({SIM_REPS} replications)...")
    cv = simulated_bounds(n, SIM_REPS, SEED_SIM)
    print(f"\n{'level':>6s}{'I(0) bound':>13s}{'I(1) bound':>13s}   decision")
    rows = []
    for lvl in (10, 5, 1):
        lo, hi = cv["I(0)"][lvl], cv["I(1)"][lvl]
        if F > hi:
            dec = "reject H0 (levels relationship)"
        elif F < lo:
            dec = "do not reject H0 (no evidence of a levels relationship)"
        else:
            dec = "inconclusive"
        print(f"{lvl:5d}%{lo:13.3f}{hi:13.3f}   {dec}")
        rows.append({"level_pct": lvl, "I0_bound": lo, "I1_bound": hi, "F": F, "decision": dec})
    print("\nWith so few observations all such tests have low power; failure to reject is "
          "not proof of no relationship.\n")

    # ---- save ---------------------------------------------------------------
    os.makedirs(OUT_DIR, exist_ok=True)
    tag = REGRESSOR.lower()
    pd.DataFrame({"term": names, "coef": b, "std_err": se, "t": b / se}).to_csv(
        os.path.join(OUT_DIR, f"bounds_{tag}_regression.csv"), index=False)
    pd.DataFrame(rows).to_csv(os.path.join(OUT_DIR, f"bounds_{tag}_critical_values.csv"), index=False)
    print(f"\nResults saved in {OUT_DIR}")


if __name__ == "__main__":
    main()
