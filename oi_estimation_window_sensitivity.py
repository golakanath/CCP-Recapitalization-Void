# =========================================================
# OI Sensitivity Check: Full Sample vs. Front-Run-Excluded vs. Post-Break-Only
# CORRECTED: uses validated raw-OI-levels ARIMA(2,1,2), no trend param,
# no log transform, no manual differencing trick.
# =========================================================
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

INPUT_PATH = r"c:/data/Oldata_final.xlsx"
OUTPUT_PATH = r"c:/data/OI_Sensitivity_Comparison_CORRECTED.xlsx"

df = pd.read_excel(INPUT_PATH, sheet_name="Sheet1")
df['Month'] = pd.to_datetime(df['Month'])
df = df.sort_values('Month').reset_index(drop=True)
df.set_index('Month', inplace=True)

H_future = 20
future_idx = pd.date_range(start='2026-08-01', periods=H_future, freq='MS')

def fit_and_forecast(series, label, steps):
    """Validated approach: plain ARIMA(2,1,2) on raw OI levels, no trend, no log."""
    m = ARIMA(series, order=(2,1,2)).fit()
    fc = m.forecast(steps=steps)
    print(f"\n--- {label} (N={len(series)}, {series.index.min().date()} to {series.index.max().date()}) ---")
    print(f"h=1 forecast:  {fc.iloc[0]:,.0f}")
    print(f"h={steps} forecast: {fc.iloc[-1]:,.0f}")
    return fc.values

# ---------- Fit 1: Full sample (VALIDATE against Table 4/6) ----------
full_series = df['OI'].astype(float)
fc1 = fit_and_forecast(full_series, "Fit 1: Full sample (Jan-2020 to Jul-2026)", H_future)
print("\n*** VALIDATION CHECK: Fit 1 h=1 / h=20 should be 2,792,344 / 3,318,819 ***\n")

# ---------- Fit 2: Excluding RBI front-run months (truncate at Mar-2026) ----------
trunc_series = df['OI'].astype(float).loc[:'2026-03-01']
fc2_full = fit_and_forecast(trunc_series, "Fit 2: Excluding Apr-Jul 2026 (truncated at Mar-2026)", H_future+4)
fc2_aligned = fc2_full[4:]
print(f"[Fit 2 aligned] Aug-26: {fc2_aligned[0]:,.0f} | Mar-28: {fc2_aligned[-1]:,.0f}")

# ---------- Fit 3: Post-break only (Oct-2024 onward) ----------
postbreak_series = df['OI'].astype(float).loc['2024-10-01':]
fc3 = fit_and_forecast(postbreak_series, "Fit 3: Post-October-2024 regime only", H_future)

comparison = pd.DataFrame({
    'Date': future_idx,
    'Fit1_FullSample': fc1,
    'Fit2_ExFrontRun': fc2_aligned,
    'Fit3_PostBreakOnly': fc3,
})
comparison.to_excel(OUTPUT_PATH, index=False)
print(f"\n✅ Comparison saved to {OUTPUT_PATH}")
print("\nNote: Fit 3 uses only ~22 observations for a 5-parameter ARIMA(2,1,2) —")
print("treat its result as indicative/directional, not a robust alternative estimate.")
