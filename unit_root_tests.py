# =========================================================
# Unit Root Tests (Level & 1st Diff) & Johansen Cointegration
# Annexure H
# Variables: LOI, LSGF, LFO, LCM, LVIX, LYTDOI
# Cointegration Pairs: (LOI, LSGF) & (LSGF, LYTDOI)
#
# Validated benchmark (Annexure H):
#   LOI=I(0), LSGF=I(1), LFO=I(0), LCM=I(2)/ambiguous (not used
#   in any model), LVIX=I(0), LYTDOI=I(1).
#   Johansen(LOI,LSGF): rejects r<=0 (17.36>15.49), fails to
#     reject r<=1 (1.95<3.84) -> r=1, but methodologically
#     mismatched given LOI is I(0) while LSGF is I(1).
#   Johansen(LSGF,LYTDOI): rejects r<=0 (19.39>15.49) AND
#     r<=1 (5.33>3.84) -- the second rejection is interpreted
#     as small-sample size distortion (Cheung & Lai 1993;
#     Reimers 1992), conclusion r=1. This is the paper's primary,
#     methodologically appropriate cointegration pairing, since
#     LSGF and LYTDOI share the same I(1) integration order.
# =========================================================
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.vector_ar.vecm import coint_johansen

# ---------- 1. Load Data ----------
input_path = r"data/raw/quarterly_sgf.xlsx"
output_path = r"outputs/forecast_results/Unit_Test_Results.xlsx"

df = pd.read_excel(input_path, sheet_name="Sheet1")
print("Raw data loaded. Shape:", df.shape)

# This test uses the same underlying quarterly master data as the
# ARDL models (data/raw/quarterly_sgf.xlsx), but excludes the Dec-2019
# row, which exists only to initialize the ARDL's lag structure and is
# not itself part of the N=26 estimation sample (Mar-2020 to Jun-2026).
df['MONTHYR'] = pd.to_datetime(df['MONTHYR'])
df = df[df['MONTHYR'] >= '2020-03-01'].reset_index(drop=True)
print("Filtered to N=26 estimation sample (Mar-2020 to Jun-2026). Shape:", df.shape)

# LFO is not a pre-existing column in the master file (unlike LOI, LSGF,
# LCM, LVIX, LYTDOI, which are already log-transformed there) -- compute
# it here. Verified to exactly reproduce the paper's original Unit.xlsx
# LFO column (max abs diff = 0.0).
df['LFO'] = np.log(df['FO'])

# ---------- 2. Data Cleaning ----------
vars_to_test = ['LOI', 'LSGF', 'LFO', 'LCM', 'LVIX', 'LYTDOI']

for col in vars_to_test:
    df[col] = df[col].replace(['*', '#NUM!', ''], np.nan)
    df[col] = pd.to_numeric(df[col], errors='coerce')

df_clean = df.dropna(subset=vars_to_test).copy()
print("Cleaned data shape (after dropping missing values):", df_clean.shape)

# ---------- 3. Augmented Dickey-Fuller (ADF) Test ----------
def run_adf(series):
    adf_test = adfuller(series, autolag='AIC')
    return {
        'Test Statistic': round(adf_test[0], 4),
        'p-value': round(adf_test[1], 4),
        'Critical Value (5%)': round(adf_test[4]['5%'], 4),
        'Stationary (5% sig.)': 'Yes' if adf_test[1] < 0.05 else 'No'
    }

adf_results = []

for col in vars_to_test:
    level_res = run_adf(df_clean[col])
    diff_series = df_clean[col].diff().dropna()
    diff_res = run_adf(diff_series)

    if level_res['Stationary (5% sig.)'] == 'Yes':
        integration_order = 'I(0)'
    elif diff_res['Stationary (5% sig.)'] == 'Yes':
        integration_order = 'I(1)'
    else:
        integration_order = 'I(2) or higher'

    adf_results.append({
        'Variable': col,
        'Level Stat': level_res['Test Statistic'],
        'Level p-value': level_res['p-value'],
        'Level Stationary': level_res['Stationary (5% sig.)'],
        '1st Diff Stat': diff_res['Test Statistic'],
        '1st Diff p-value': diff_res['p-value'],
        '1st Diff Stationary': diff_res['Stationary (5% sig.)'],
        'Integration Order': integration_order
    })

adf_df = pd.DataFrame(adf_results)

print("\n" + "="*80)
print("ADF Unit Root Test Results (Levels vs 1st Differences)")
print("="*80)
print(adf_df.to_string(index=False))

# ---------- 4. Johansen Cointegration Test ----------
def run_johansen(data, pair_name):
    # det_order = 0: no deterministic trend in cointegrating equation
    # k_ar_diff = 1: lag length (1st difference), matching the ARDL(1,1)
    # specification used for the SGF models elsewhere in this paper
    johansen_test = coint_johansen(data, det_order=0, k_ar_diff=1)

    trace_stats = johansen_test.lr1
    crit_vals = johansen_test.cvt

    results = []
    for r in range(len(data.columns)):
        results.append({
            'Variables Tested': pair_name,
            'Null Hypothesis': f'r <= {r} (Cointegration rank <= {r})',
            'Trace Statistic': round(trace_stats[r], 4),
            'Critical Value (90%)': round(crit_vals[r, 0], 4),
            'Critical Value (95%)': round(crit_vals[r, 1], 4),
            'Critical Value (99%)': round(crit_vals[r, 2], 4),
            'Reject Null (95% sig.)': 'Yes' if trace_stats[r] > crit_vals[r, 1] else 'No'
        })
    return pd.DataFrame(results)

# Test 1: LOI and LSGF -- reported as a secondary/mismatched pairing,
# since LOI is I(0) while LSGF is I(1); included for completeness/
# transparency, not as the primary cointegration evidence.
print("\n" + "="*80)
print("Johansen Cointegration Test (Trace Test) - LOI & LSGF")
print("="*80)
johansen_LOI_LSGF = run_johansen(df_clean[['LOI', 'LSGF']], 'LOI & LSGF')
print(johansen_LOI_LSGF.to_string(index=False))

# Test 2: LSGF and LYTDOI -- the paper's primary, methodologically
# appropriate pairing (both I(1)).
print("\n" + "="*80)
print("Johansen Cointegration Test (Trace Test) - LSGF & LYTDOI")
print("="*80)
johansen_LSGF_LYTDOI = run_johansen(df_clean[['LSGF', 'LYTDOI']], 'LSGF & LYTDOI')
print(johansen_LSGF_LYTDOI.to_string(index=False))

# ---------- 5. Export Results to Excel ----------
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    adf_df.to_excel(writer, sheet_name='ADF_Tests', index=False)
    johansen_LOI_LSGF.to_excel(writer, sheet_name='Johansen_LOI_LSGF', index=False)
    johansen_LSGF_LYTDOI.to_excel(writer, sheet_name='Johansen_LSGF_LYTDOI', index=False)

print(f"\nResults successfully written to: {output_path}")
