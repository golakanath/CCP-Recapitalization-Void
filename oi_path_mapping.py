# =========================================================
# OI Out-of-Sample Path Mapping & FRE Detail — CORRECTED
# Model: ARIMA(2,1,2) on RAW OI LEVELS (validated specification —
# NOT log-transformed; see Section 3.5 for why OI differs from CM/FO)
# Test Period: April 2025 – July 2026
# =========================================================
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

from pathlib import Path
try:
    HERE = Path(__file__).resolve().parent
except NameError:                       # running inside Jupyter
    HERE = Path.cwd()

def _find(name):
    """Locate an input file (case-insensitive) in the script folder,
    data/raw or the current folder."""
    for folder in (HERE, HERE / "data" / "raw", Path.cwd()):
        if folder.is_dir():
            for f in folder.iterdir():
                if f.name.lower() == name.lower():
                    return str(f)
    raise FileNotFoundError(f"{name} not found; place it next to this script.")

INPUT_PATH = _find("OI.xlsx")
OUTPUT_PATH = str(HERE / "OI_Path_Mapping_FRE_CORRECTED.xlsx")

df = pd.read_excel(INPUT_PATH, sheet_name="Sheet1")

month_map = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
             'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}

def parse_month(s):
    if isinstance(s, pd.Timestamp):
        return s
    s_str = str(s).strip()
    parts = s_str.split('-')
    if len(parts) == 2:
        m, y = parts
        m = m.strip(); y = y.strip()
        if m in month_map:
            return pd.Timestamp(year=2000 + int(y), month=month_map[m], day=1)
    return pd.to_datetime(s_str, errors='coerce')

df['Date'] = df['Month'].apply(parse_month)
df = df.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)
df.set_index('Date', inplace=True)

# CORRECTED: model on raw OI, matching the validated benchmark (Table 4/6)
ts = df['OI'].astype(float)

train = ts.loc[:'2025-03-01']
test  = ts.loc['2025-04-01':'2026-07-01']
H_test = len(test)

print("Fitting ARIMA(2,1,2) on raw OI levels (validated specification)...")
m = ARIMA(train, order=(2,1,2)).fit()
forecast_oi = m.forecast(steps=H_test)

actual_oi = test

mape_pct = np.abs((actual_oi - forecast_oi) / actual_oi) * 100
fre_pct = ((forecast_oi - actual_oi) / actual_oi) * 100

path_mapping_df = pd.DataFrame({
    'Month': test.index.strftime('%b-%y'),
    'Actual MDA OI (Rs. Cr)': actual_oi.values.round(0),
    'ARIMA Forecast (Rs. Cr)': forecast_oi.values.round(0),
    'MAPE%': mape_pct.values.round(2),
    'FRE%': fre_pct.values.round(2)
})
path_mapping_df.set_index('Month', inplace=True)

print("\n============= Out-of-Sample Path Mapping – OI (April 2025 – July 2026) =============")
print(path_mapping_df.to_string())
print(f"\nMean MAPE%: {mape_pct.mean():.4f} (should match Table 4's 4.918%)")

path_mapping_df.to_excel(OUTPUT_PATH, sheet_name='OI_Path_Mapping_FRE')
print(f"\n✅ Corrected Out-of-Sample Path Mapping saved to: {OUTPUT_PATH}")
