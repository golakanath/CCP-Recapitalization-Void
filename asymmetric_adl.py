# =========================================================
# Asymmetric Distributed-Lag (ADL) Model of OI's Response to
# Volatility Shocks -- Table 10 / Section 5.4
# =========================================================
# DOI = alpha + b1*DCM + b2*DVX + b3*DVXSQ + b4*DVXPOS
#             + b5*DVX_Lag1 + b6*DOI_Lag1 + eps
#
# Validated benchmark (Table 10), N=77 (Jan 2020-Jul 2026):
#   Intercept = 0.0199 (p=0.018)  -- baseline DOI growth
#   DCM       = 0.2116 (p<0.001)  -- spot momentum drives OI
#   DVX       = -0.2098 (p=0.009) -- linear liquidation effect
#   DVXSQ     = -0.1896 (p=0.052) -- convexity, borderline significant
#   DVXPOS    = 0.0964 (p=0.605)  -- no directional asymmetry detected
#   DVX_Lag1  = -0.1270 (p=0.002) -- lingering risk aversion
#   DOI_Lag1  = 0.1832 (p<0.001)  -- AR(1) persistence
#   R-squared = 0.6129
#
# Coefficients and R-squared independently re-verified via closed-form
# OLS (beta = (X'X)^-1 X'y) during this project's repository review,
# exact match to 4 decimal places against this script's own output.
#
# NOTE: Section 5.6 (Model Risk) applies this model's coefficients to
# compare a correctly-specified stress scenario (using DVX, DVXSQ, and
# lag terms) against progressively simpler restricted alternatives that
# drop convexity and/or lag dynamics, showing the latter understate
# implied SGF erosion by roughly half under an illustrative VIX shock.
# =========================================================
import pandas as pd
import numpy as np
import statsmodels.api as sm

# ---------- 1. Load Data ----------
import os
from pathlib import Path
try:
    HERE = Path(__file__).resolve().parent
except NameError:                       # running inside Jupyter
    HERE = Path.cwd()

def _find(name):
    """Locate an input file (case-insensitive) in the script folder,
    data/raw, data/processed or the current folder."""
    for folder in (HERE, HERE / "data" / "raw", HERE / "data" / "processed", Path.cwd()):
        if folder.is_dir():
            for f in folder.iterdir():
                if f.name.lower() == name.lower():
                    return str(f)
    raise FileNotFoundError(f"{name} not found; place it next to this script.")

file_path = _find("vixreg1.xlsx")
sheet_name = "RESULTS (2)"

df = pd.read_excel(file_path, sheet_name=sheet_name)
print("Raw data shape:", df.shape)

# ---------- 2. Data Cleaning ----------
# The dataset contains '*' for missing values.
variables = ['DOI', 'DCM', 'DVX', 'DVXSQ', 'DVXPOS', 'DOI_Lag1', 'DVX_Lag1']

for col in variables:
    df[col] = df[col].replace('*', np.nan)
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop rows where any of our variables of interest have NaN values.
# One observation is lost to first-differencing, one to the AR(1) lag,
# leaving N=77 from the original N=79 monthly series (Section 3, Table 1).
df_clean = df.dropna(subset=variables).copy()
print("Cleaned data shape (after dropping NaNs):", df_clean.shape)

# ---------- 3. Prepare Y and X ----------
y = df_clean['DOI']
X = df_clean[['DCM', 'DVX', 'DVXSQ', 'DVXPOS', 'DOI_Lag1', 'DVX_Lag1']]

X = sm.add_constant(X)

# ---------- 4. Estimate OLS with HAC Standard Errors ----------
# HAC (Newey-West) standard errors with maxlags=12: an accepted
# convention for monthly data capturing a full annual cycle. Results
# are robust to alternative lag choices (2-4 lags leave the
# significance pattern unchanged -- see Section 5.4).
model = sm.OLS(y, X)
results_hac = model.fit(cov_type='HAC', cov_kwds={'maxlags': 12})

# ---------- 5. Display Results ----------
print("\n" + "="*50)
print("OLS Regression Results with HAC Standard Errors")
print("="*50)
print(results_hac.summary())
