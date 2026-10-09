# =========================================================
# CM Trade Volume Forecasting: PRIMARY REPORTED SPECIFICATION
# 7 Models Comparison (Log Scale) -- Table 3a
# Test: Apr-2025 -> Jul-2026 (16 months)
# Forecast: Aug-2026 -> Mar-2028 (20 months)
# Models: Naive, ETS, ARIMA, Prophet, Theta, Holt-Winters, SARIMA
#
# Validated benchmark (Table 3a): Naive=14.003%, ARIMA=13.532%,
# Prophet=13.656%, Theta=10.732%, SARIMA=12.786%, ETS=6.572%,
# Holt-Winters=6.572% (ETS/Holt-Winters effectively tied; both
# reported together per Section 3.3 rather than treating either
# as decisively superior). Best_Model resolves to Holt-Winters.
# Aug-2026 forecast=144,030; Mar-2028 forecast=189,222.
#
# NOTE: CM is log-transformed (LCM = ln(CM)), unlike OI -- see
# Section 3.5 for why OI does NOT use a log transform while CM
# and FO do (CM's smaller absolute scale means a raw-levels 95%
# interval can collapse toward zero over a 20-month horizon;
# see Annexure B for the specific fix this required).
#
# NOTE: no regulatory-event exogenous dummies here, unlike FO.
# The Nov 2024 SEBI measures and the RBI BG-collateral rules are
# specifically F&O/derivatives-market events with no established
# causal link to CM (cash equity) volume in this project; do not
# import FO's dummy structure into this script.
# =========================================================
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.forecasting.theta import ThetaModel

try:
    from prophet import Prophet
    PROPHET_INSTALLED = True
except ImportError:
    PROPHET_INSTALLED = False
    print("Prophet is not installed. Skipping Prophet model. (Install via: pip install prophet)")

# ---------- 1. Load Data & Transform to Log ----------
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

INPUT_PATH = _find("CM_OUTLIER_RMVD.xlsx")
OUTPUT_PATH = str(HERE / "cm_forecast_results.xlsx")

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

df['LCM'] = np.log(df['CM'].astype(float))
ts = df['LCM']

# ---------- 2. Train / Test Split ----------
train = ts.loc[:'2025-03-01']
test  = ts.loc['2025-04-01':'2026-07-01']

H_test = len(test)
H_future = 20
future_idx = pd.date_range(start='2026-08-01', periods=H_future, freq='MS')

def mape(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

Z_95 = 1.96
results = {}
test_fc, test_lower, test_upper = {}, {}, {}
future_fc, future_lower, future_upper = {}, {}, {}

def empirical_ci(fc_series, resid_std):
    lower = np.asarray(fc_series) - Z_95 * resid_std
    upper = np.asarray(fc_series) + Z_95 * resid_std
    return lower, upper

def get_resid_std(model, train_series):
    try:
        return np.std(model.resid)
    except AttributeError:
        pass
    try:
        return np.std((train_series - model.fittedvalues).dropna())
    except AttributeError:
        pass
    try:
        return np.std((train_series - model.fitted).dropna())
    except AttributeError:
        pass
    return np.std(train_series.diff().dropna())

# ---------- 3a. Naive Model ----------
print("Fitting Naive ...")
test_fc['Naive'] = pd.Series(np.repeat(train.iloc[-1], H_test), index=test.index)
resid_std_naive = np.std(train.diff().dropna())
test_lower['Naive'], test_upper['Naive'] = empirical_ci(test_fc['Naive'], resid_std_naive)
future_fc['Naive'] = pd.Series(np.repeat(ts.iloc[-1], H_future), index=future_idx)
future_lower['Naive'], future_upper['Naive'] = empirical_ci(future_fc['Naive'], resid_std_naive)

# ---------- 3b. ETS ----------
print("Fitting ETS ...")
ets = ETSModel(train, error='add', trend='add', seasonal='add', seasonal_periods=12).fit(disp=False)
test_fc['ETS'] = ets.forecast(steps=H_test)
resid_std_ets = get_resid_std(ets, train)
test_lower['ETS'], test_upper['ETS'] = empirical_ci(test_fc['ETS'], resid_std_ets)

ets_full = ETSModel(ts, error='add', trend='add', seasonal='add', seasonal_periods=12).fit(disp=False)
future_fc['ETS'] = ets_full.forecast(steps=H_future)
future_lower['ETS'], future_upper['ETS'] = empirical_ci(future_fc['ETS'], resid_std_ets)

# ---------- 3c. ARIMA (Auto AIC) ----------
print("Fitting ARIMA ...")
best_aic, best_order = np.inf, (1,1,1)
for order in [(1,1,1), (2,1,2), (0,1,1), (1,1,0), (2,0,2)]:
    try:
        m = ARIMA(train, order=order).fit()
        if m.aic < best_aic:
            best_aic, best_order = m.aic, order
    except:
        pass

m = ARIMA(train, order=best_order).fit()
fc_test = m.get_forecast(steps=H_test)
test_fc['ARIMA'] = fc_test.predicted_mean
ci_test = fc_test.conf_int(alpha=0.05)
test_lower['ARIMA'] = ci_test.iloc[:, 0]
test_upper['ARIMA'] = ci_test.iloc[:, 1]

m_full = ARIMA(ts, order=best_order).fit()
fc_future = m_full.get_forecast(steps=H_future)
future_fc['ARIMA'] = fc_future.predicted_mean
ci_future = fc_future.conf_int(alpha=0.05)
future_lower['ARIMA'] = ci_future.iloc[:, 0]
future_upper['ARIMA'] = ci_future.iloc[:, 1]

# ---------- 3d. Prophet ----------
if PROPHET_INSTALLED:
    print("Fitting Prophet ...")
    prophet_train = pd.DataFrame({'ds': train.index, 'y': train.values})
    p_model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    p_model.fit(prophet_train)

    future_test = p_model.make_future_dataframe(periods=H_test, freq='MS')
    fc_test_p = p_model.predict(future_test).tail(H_test)
    test_fc['Prophet'] = fc_test_p['yhat'].values
    test_lower['Prophet'] = fc_test_p['yhat_lower'].values
    test_upper['Prophet'] = fc_test_p['yhat_upper'].values

    prophet_full = pd.DataFrame({'ds': ts.index, 'y': ts.values})
    p_full = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    p_full.fit(prophet_full)

    future_future = p_full.make_future_dataframe(periods=H_future, freq='MS')
    fc_future_p = p_full.predict(future_future).tail(H_future)
    future_fc['Prophet'] = fc_future_p['yhat'].values
    future_lower['Prophet'] = fc_future_p['yhat_lower'].values
    future_upper['Prophet'] = fc_future_p['yhat_upper'].values

# ---------- 3e. Theta ----------
print("Fitting Theta ...")
tm = ThetaModel(train, period=12).fit()
test_fc['Theta'] = tm.forecast(steps=H_test)
resid_std_tm = get_resid_std(tm, train)
test_lower['Theta'], test_upper['Theta'] = empirical_ci(test_fc['Theta'], resid_std_tm)

tm_full = ThetaModel(ts, period=12).fit()
future_fc['Theta'] = tm_full.forecast(steps=H_future)
future_lower['Theta'], future_upper['Theta'] = empirical_ci(future_fc['Theta'], resid_std_tm)

# ---------- 3f. Holt-Winters ----------
print("Fitting Holt-Winters ...")
hw = ExponentialSmoothing(train, trend='add', seasonal='add', seasonal_periods=12).fit()
test_fc['Holt-Winters'] = hw.forecast(H_test)
resid_std_hw = get_resid_std(hw, train)
test_lower['Holt-Winters'], test_upper['Holt-Winters'] = empirical_ci(test_fc['Holt-Winters'], resid_std_hw)

hw_full = ExponentialSmoothing(ts, trend='add', seasonal='add', seasonal_periods=12).fit()
future_fc['Holt-Winters'] = hw_full.forecast(H_future)
future_lower['Holt-Winters'], future_upper['Holt-Winters'] = empirical_ci(future_fc['Holt-Winters'], resid_std_hw)

# ---------- 3g. SARIMA ----------
# NOTE: this specification -- SARIMAX(1,1,1)(1,1,1,12) -- is also cited
# directly in Section 3.3/Annexure B for residual diagnostics (the two
# largest residuals trace to the Nov 2023 Muhurat and May 2024 BCP
# outlier-adjustment dates). Keep this order fixed; it is not re-selected
# by AIC search the way the plain ARIMA model above is.
print("Fitting SARIMA ...")
sm = SARIMAX(train, order=(1,1,1), seasonal_order=(1,1,1,12),
             enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
fc_test = sm.get_forecast(steps=H_test)
test_fc['SARIMA'] = fc_test.predicted_mean
ci_test = fc_test.conf_int(alpha=0.05)
test_lower['SARIMA'] = ci_test.iloc[:, 0]
test_upper['SARIMA'] = ci_test.iloc[:, 1]

sm_full = SARIMAX(ts, order=(1,1,1), seasonal_order=(1,1,1,12),
                  enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
fc_future = sm_full.get_forecast(steps=H_future)
future_fc['SARIMA'] = fc_future.predicted_mean
ci_future = fc_future.conf_int(alpha=0.05)
future_lower['SARIMA'] = ci_future.iloc[:, 0]
future_upper['SARIMA'] = ci_future.iloc[:, 1]

# ---------- 4. Calculate Metrics (Convert Back to CM Scale) ----------
test_cm_actuals = np.exp(test)

for name in test_fc.keys():
    fc_cm = np.exp(test_fc[name])
    results[name] = {
        'MAE': mean_absolute_error(test_cm_actuals, fc_cm),
        'RMSE': np.sqrt(mean_squared_error(test_cm_actuals, fc_cm)),
        'MAPE': mape(test_cm_actuals, fc_cm)
    }

metrics = pd.DataFrame(results).T[['MAE', 'RMSE', 'MAPE']]
print("\n=========== Model Comparison (Evaluated on Original CM Scale) ===========")
print(metrics.round(4).to_string())

best_model = metrics['MAPE'].idxmin()
print(f"\nBest model by MAPE: {best_model}")
print("NOTE: ETS and Holt-Winters are effectively tied (see Section 3.3);")
print("both are reported together in the paper rather than treating")
print("either as decisively superior.")

# ---------- 5. Build Output Frames (Exponentiate back to CM Scale) ----------
def build_df(index, fc, lower, upper, actuals_lcm=None):
    data = {}
    if actuals_lcm is not None:
        data['Actual_CM'] = np.exp(np.asarray(actuals_lcm).flatten())
    for name in fc.keys():
        fc_arr = np.exp(np.asarray(fc[name]).flatten())
        lower_arr = np.exp(np.asarray(lower[name]).flatten())
        upper_arr = np.exp(np.asarray(upper[name]).flatten())
        data[f'{name}_Forecast'] = fc_arr
        data[f'{name}_Lower_95%'] = lower_arr
        data[f'{name}_Upper_95%'] = upper_arr
    return pd.DataFrame(data, index=index)

test_df = build_df(test.index, test_fc, test_lower, test_upper, actuals_lcm=test)
future_df = build_df(future_idx, future_fc, future_lower, future_upper)
future_df['Best_Model'] = best_model
future_df['Best_Forecast'] = future_df[f'{best_model}_Forecast']

# ---------- 6. Save to Excel ----------
with pd.ExcelWriter(OUTPUT_PATH, engine='openpyxl') as w:
    metrics.round(4).to_excel(w, sheet_name='Model_Comparison')
    test_df.round(0).to_excel(w, sheet_name='Test_Forecasts')
    future_df.round(0).to_excel(w, sheet_name='Future_Forecasts')

print(f"\nOutput written to: {OUTPUT_PATH}")

# ---------- 7. Generate Graphs ----------
plt.figure(figsize=(12, 5))
resid_trimmed = sm_full.resid.iloc[24:]
resid_trimmed.to_frame('residual').to_excel(str(HERE / "CM_Residuals_Dated.xlsx"))

plt.plot(resid_trimmed.index, resid_trimmed.values, color='purple', label='SARIMA Residuals (LCM Scale)')
plt.axhline(0, color='black', linestyle='--', alpha=0.7)
plt.title('(a) Residuals of Final SARIMA Model (Log Scale) - Burn-in Trimmed')
plt.xlabel('Date'); plt.ylabel('Residual (Log Error)')
plt.legend(); plt.grid(True, alpha=0.3); plt.tight_layout()
plt.savefig(str(HERE / "CM_SARIMA_Residuals.png"), dpi=300)
plt.show()

plt.figure(figsize=(14, 6))
hist_to_plot = np.exp(ts).loc['2024-01-01':]
plt.plot(hist_to_plot.index, hist_to_plot.values, label='Historical CM Volume', color='blue', marker='o', markersize=4)
plt.plot(future_df.index, future_df['Best_Forecast'], label=f'Forecast ({best_model})', color='red', marker='o', markersize=5)
plt.fill_between(future_df.index, future_df[f"{best_model}_Lower_95%"], future_df[f"{best_model}_Upper_95%"],
                 color='red', alpha=0.15, label='95% Confidence Interval')
plt.axvline(x=ts.index[-1], color='gray', linestyle='--', alpha=0.8, label='Forecast Start (Aug-2026)')
plt.title('(b) Cash Market MDA Forecast (Aug 2026 - Mar 2028) with 95% CI')
plt.xlabel('Date'); plt.ylabel('CM Trade Volume')
plt.legend(loc='upper left'); plt.grid(True, alpha=0.3); plt.tight_layout()
plt.savefig(str(HERE / "CM_Forecast_Path.png"), dpi=300)
plt.show()

print("Done.")
