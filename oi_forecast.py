# =========================================================
# OI Forecasting: PRIMARY REPORTED SPECIFICATION (Table 4/5)
# ARIMA(2,1,2) | SARIMA | Holt-Winters | XGBoost
# Test: Apr-2025 -> Jul-2026 (16 months)
# Forecast: Aug-2026 -> Mar-2028 (20 months)
#
# IMPORTANT: OI is modeled on RAW LEVELS, not log-transformed --
# unlike CM and FO. See Section 3.5 for why: OI's absolute scale
# (1.5-3M+ crore) keeps a levels-based 95% interval comfortably
# positive without the log-transform safeguard CM required.
#
# IMPORTANT: no outlier removal is applied to OI (unlike CM/FO).
# OI is a stock (point-in-time open positions), not a flow, so
# the Muhurat/BCP procedural-date exclusion argument used for
# CM/FO volume does not apply. See Section 3.2/3.5.
#
# IMPORTANT: no `trend` parameter and no seasonal_order on the
# ARIMA(2,1,2) call. This exact, simplest specification --
# ARIMA(train, order=(2,1,2)).fit() -- is what reproduces the
# paper's validated benchmark (MAPE=4.9176%, Mar-2028=3,318,819).
# Adding trend='c', log-transforming, or using auto_arima's
# seasonal search will NOT reproduce these numbers; this was
# confirmed through extensive debugging during this project.
#
# Validated benchmark: ARIMA(2,1,2) MAPE=4.9176%, SARIMA=18.0390%,
# Holt-Winters=5.7874%, XGBoost=4.8871%; Mar-2028 forecast=3,318,819
# =========================================================
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from xgboost import XGBRegressor

# ---------- 1. Load data ----------
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

INPUT_PATH = _find("OI.xlsx")
OUTPUT_PATH = str(HERE / "OI_Forecast_Results.xlsx")

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
df = df.dropna(subset=['Date'])
df = df.sort_values('Date').reset_index(drop=True)
df.set_index('Date', inplace=True)

# NOTE: raw OI levels, NOT log-transformed -- this is deliberate.
ts = df['OI'].astype(float)

print("Series loaded:", ts.shape[0], "monthly obs |",
      ts.index[0].date(), "->", ts.index[-1].date())

# ---------- 2. Train / Test split ----------
train = ts.loc[:'2025-03-01']
test  = ts.loc['2025-04-01':'2026-07-01']

H_test = len(test)
H_future = 20
future_idx = pd.date_range(start='2026-08-01', periods=H_future, freq='MS')

def mape(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

results = {}
test_fc   = {}
future_fc = {}

# ---------- 3a. ARIMA(2,1,2) ----------
print("\nFitting ARIMA(2,1,2) ...")
m = ARIMA(train, order=(2,1,2)).fit()
test_fc['ARIMA(2,1,2)'] = m.forecast(steps=H_test)
future_fc['ARIMA(2,1,2)'] = ARIMA(ts, order=(2,1,2)).fit().forecast(steps=H_future)

results['ARIMA(2,1,2)'] = {
    'MAE' : mean_absolute_error(test, test_fc['ARIMA(2,1,2)']),
    'RMSE': np.sqrt(mean_squared_error(test, test_fc['ARIMA(2,1,2)'])),
    'MAPE': mape(test, test_fc['ARIMA(2,1,2)']),
}

# ---------- 3b. SARIMA (2,1,2)x(1,1,1,12) ----------
print("Fitting SARIMA ...")
sm = SARIMAX(train, order=(2,1,2),
             seasonal_order=(1,1,1,12),
             enforce_stationarity=False,
             enforce_invertibility=False).fit(disp=False)
test_fc['SARIMA'] = sm.forecast(steps=H_test)

future_fc['SARIMA'] = SARIMAX(ts, order=(2,1,2),
                             seasonal_order=(1,1,1,12),
                             enforce_stationarity=False,
                             enforce_invertibility=False).fit(disp=False).forecast(steps=H_future)

results['SARIMA'] = {
    'MAE' : mean_absolute_error(test, test_fc['SARIMA']),
    'RMSE': np.sqrt(mean_squared_error(test, test_fc['SARIMA'])),
    'MAPE': mape(test, test_fc['SARIMA']),
}

# ---------- 3c. Holt-Winters ----------
print("Fitting Holt-Winters ...")
hw = ExponentialSmoothing(train, trend='add', seasonal='add',
                          seasonal_periods=12).fit()
test_fc['Holt-Winters'] = hw.forecast(H_test)

future_fc['Holt-Winters'] = ExponentialSmoothing(
        ts, trend='add', seasonal='add',
        seasonal_periods=12).fit().forecast(H_future)

results['Holt-Winters'] = {
    'MAE' : mean_absolute_error(test, test_fc['Holt-Winters']),
    'RMSE': np.sqrt(mean_squared_error(test, test_fc['Holt-Winters'])),
    'MAPE': mape(test, test_fc['Holt-Winters']),
}

# ---------- 3d. XGBoost (lag features, recursive multi-step) ----------
# NOTE: retained for completeness/comparison only. Section 3.5 documents
# why XGBoost is NOT the reported model despite a marginally lower MAPE:
# its point forecast plateaus rather than continuing the sample's
# structural growth trend, and its 95% interval (constructed from
# in-sample residuals) fails to widen with horizon.
LAGS = 12

def make_features(series):
    d = pd.DataFrame({'y': series})
    for k in range(1, LAGS+1):
        d[f'lag_{k}'] = d['y'].shift(k)
    d['month']     = d.index.month
    d['diff_1']    = d['y'].diff(1)
    d['diff_12']   = d['y'].diff(12)
    return d.dropna()

def recursive_xgb(model, history, steps, feat_cols):
    hist = history.copy()
    preds, dates = [], []
    last_date = hist.index[-1]
    for _ in range(steps):
        nxt_date = last_date + pd.DateOffset(months=1)
        row = {f'lag_{k}': hist.iloc[-k] for k in range(1, LAGS+1)}
        row['month']   = nxt_date.month
        row['diff_1']  = hist.iloc[-1] - hist.iloc[-2]
        row['diff_12'] = hist.iloc[-1] - hist.iloc[-12] if len(hist) >= 13 else 0.0
        X = pd.DataFrame([row])[feat_cols]
        yhat = float(model.predict(X)[0])
        preds.append(yhat)
        dates.append(nxt_date)
        hist = pd.concat([hist, pd.Series([yhat], index=[nxt_date])])
        last_date = nxt_date
    return pd.Series(preds, index=dates)

print("Fitting XGBoost ...")
ftr_train = make_features(train)
X_tr = ftr_train.drop(columns='y'); y_tr = ftr_train['y']
xgb = XGBRegressor(n_estimators=500, learning_rate=0.05,
                   max_depth=4, subsample=0.9,
                   colsample_bytree=0.9, random_state=42)
xgb.fit(X_tr, y_tr)

test_fc['XGBoost'] = recursive_xgb(xgb, train, H_test, X_tr.columns)

ftr_full = make_features(ts)
X_full = ftr_full.drop(columns='y'); y_full = ftr_full['y']
xgb_full = XGBRegressor(n_estimators=500, learning_rate=0.05,
                         max_depth=4, subsample=0.9,
                         colsample_bytree=0.9, random_state=42)
xgb_full.fit(X_full, y_full)

future_fc['XGBoost'] = recursive_xgb(xgb_full, ts, H_future, X_full.columns)

results['XGBoost'] = {
    'MAE' : mean_absolute_error(test, test_fc['XGBoost']),
    'RMSE': np.sqrt(mean_squared_error(test, test_fc['XGBoost'])),
    'MAPE': mape(test, test_fc['XGBoost']),
}

# ---------- 4. Compare ----------
metrics = pd.DataFrame(results).T[['MAE','RMSE','MAPE']]
print("\n=========== Model Comparison ===========")
print(metrics.round(4).to_string())

best_model = metrics['MAPE'].idxmin()
print(f"\nBest model by MAPE: {best_model}")
print("NOTE: Table 4/5 report ARIMA(2,1,2) as the primary model regardless")
print("of which model wins on raw MAPE -- see Section 3.5 for the diagnostic")
print("reasons (point-forecast plausibility, interval behavior).")

# ---------- 5. Build output frames ----------
test_df = pd.DataFrame({k: v.values for k, v in test_fc.items()})
test_df.index = test.index
test_df.insert(0, 'Actual', test.values)

future_df = pd.DataFrame({k: v.values for k, v in future_fc.items()})
future_df.index = future_idx
future_df['Best_Model']    = best_model
future_df['Best_Forecast'] = future_df[best_model]

# ---------- 6. Save ----------
with pd.ExcelWriter(OUTPUT_PATH, engine='openpyxl') as w:
    metrics.round(4).to_excel(w, sheet_name='Model_Comparison')
    test_df.round(0).to_excel(w, sheet_name='Test_Forecasts')
    future_df.round(0).to_excel(w, sheet_name='Future_Forecasts')

print(f"\nOutput written to: {OUTPUT_PATH}")
print("\nFuture Forecasts (Aug-2026 -> Mar-2028):")
print(future_df.round(0).to_string())
