# =========================================================
# FO Trade Volume Forecasting: PRIMARY REPORTED SPECIFICATION
# (Excludes RBI_Deferred -- see Section 3.4 for rationale:
#  the term is unidentifiable, having zero variation across
#  the entire estimation sample.)
# Test: Apr-2025 -> Jul-2026 (16 months)
# Forecast: Aug-2026 -> Mar-2028 (20 months)
# Models: SARIMA, Prophet, Theta, ARIMA, ARIMAX (SARIMAX w/ Exog), Holt-Winters, ETS
# Validated against paper: ARIMAX MAPE=9.34%, Mar-2028 forecast ~Rs.69,955,687cr
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

INPUT_PATH = _find("FO_OUTLIER_RMVD.xlsx")
OUTPUT_PATH = str(HERE / "FO_Forecast_Results.xlsx")

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

df['LFO'] = np.log(df['FO'].astype(float))
ts = df['LFO']

# ---------- 2. Create Exogenous Dummies ----------
full_dates = pd.date_range(start='2020-01-01', end='2028-03-01', freq='MS')
exog_full = pd.DataFrame(index=full_dates)

# SEBI Partial Transition (Transient, Nov 2024 only) -- the Nov 20, 2024
# effective date fell mid-month with a phased lot-size rollout completing
# only by Dec 24-26, 2024, so Nov 2024 is a genuine mixed old/new-regime
# month, not a clean regime split. See Section 3.4.
exog_full['Partial_Transition'] = (exog_full.index == '2024-11-01').astype(int)

# SEBI Full Shock (Permanent, post-Dec 2024)
exog_full['Full_Shock'] = (exog_full.index >= '2024-12-01').astype(int)

# RBI Front-Run (transient, Apr-Jun 2026): BG collateral front-loading
# ahead of the RBI Capital Market Exposure Directions' July 1, 2026
# effective date (deferred from an original April 1, 2026 date).
exog_full['RBI_FrontRun'] = ((exog_full.index >= '2026-04-01') & (exog_full.index <= '2026-06-01')).astype(int)

# NOTE: RBI_Deferred (hypothesized renewal-cycle effect ~Apr-May 2027)
# is deliberately NOT included. It has zero variation across the entire
# estimation sample (train and full-history refit both end Jul-2026),
# making it statistically unidentifiable. See Section 3.4.

exog_hist = exog_full.loc[ts.index]

# ---------- 3. Train / Test Split ----------
train = ts.loc[:'2025-03-01']
test  = ts.loc['2025-04-01':'2026-07-01']

exog_train = exog_hist.loc[:'2025-03-01']
exog_test  = exog_hist.loc['2025-04-01':'2026-07-01']

H_test = len(test)
H_future = 20
future_idx = pd.date_range(start='2026-08-01', periods=H_future, freq='MS')
exog_future = exog_full.loc[future_idx]

def mape(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

Z_95 = 1.96
results = {}
test_fc, test_lower, test_upper = {}, {}, {}
future_fc, future_lower, future_upper = {}, {}, {}
residuals_dict = {}

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

def get_model_residuals(model, series):
    try:
        return model.resid
    except AttributeError:
        pass
    try:
        return series - model.fittedvalues
    except AttributeError:
        pass
    try:
        return series - model.fitted
    except AttributeError:
        pass
    try:
        return series - model.predict(start=series.index[0], end=series.index[-1])
    except Exception:
        pass
    return series.diff().dropna()

# ---------- 4a. Naive Model ----------
print("Fitting Naive ...")
test_fc['Naive'] = pd.Series(np.repeat(train.iloc[-1], H_test), index=test.index)
resid_std_naive = np.std(train.diff().dropna())
test_lower['Naive'], test_upper['Naive'] = empirical_ci(test_fc['Naive'], resid_std_naive)
future_fc['Naive'] = pd.Series(np.repeat(ts.iloc[-1], H_future), index=future_idx)
future_lower['Naive'], future_upper['Naive'] = empirical_ci(future_fc['Naive'], resid_std_naive)
residuals_dict['Naive'] = train - train.shift(1)

# ---------- 4b. ETS ----------
print("Fitting ETS ...")
ets = ETSModel(train, error='add', trend='add', seasonal='add', seasonal_periods=12).fit(disp=False)
test_fc['ETS'] = ets.forecast(steps=H_test)
resid_std_ets = get_resid_std(ets, train)
test_lower['ETS'], test_upper['ETS'] = empirical_ci(test_fc['ETS'], resid_std_ets)

ets_full = ETSModel(ts, error='add', trend='add', seasonal='add', seasonal_periods=12).fit(disp=False)
future_fc['ETS'] = ets_full.forecast(steps=H_future)
future_lower['ETS'], future_upper['ETS'] = empirical_ci(future_fc['ETS'], resid_std_ets)
residuals_dict['ETS'] = get_model_residuals(ets_full, ts)

# ---------- 4c. ARIMA (Auto AIC) ----------
print("Fitting ARIMA ...")
best_aic, best_order = np.inf, (1,1,1)
for order in [(1,1,1), (2,1,2), (0,1,1), (1,1,0), (2,0,2)]:
    try:
        m = ARIMA(train, order=order).fit()
        if m.aic < best_aic:
            best_aic, best_order = m.aic, order
    except: pass

m = ARIMA(train, order=best_order).fit()
fc_test = m.get_forecast(steps=H_test)
test_fc['ARIMA'] = fc_test.predicted_mean
ci_test = fc_test.conf_int(alpha=0.05)
test_lower['ARIMA'], test_upper['ARIMA'] = ci_test.iloc[:, 0], ci_test.iloc[:, 1]

m_full = ARIMA(ts, order=best_order).fit()
fc_future = m_full.get_forecast(steps=H_future)
future_fc['ARIMA'] = fc_future.predicted_mean
ci_future = fc_future.conf_int(alpha=0.05)
future_lower['ARIMA'], future_upper['ARIMA'] = ci_future.iloc[:, 0], ci_future.iloc[:, 1]
residuals_dict['ARIMA'] = get_model_residuals(m_full, ts)

# ---------- 4d. ARIMAX (SARIMAX with Exogenous Dummies) ----------
# NOTE: non-seasonal order=(1,1,1). Do NOT add seasonal_order or use
# auto_arima's seasonal search here -- the paper's validated MAPE (9.34%)
# and Annexure C's residual diagnostics both depend on this exact,
# non-seasonal specification.
print("Fitting ARIMAX (SARIMAX w/ Exog) ...")
arimax_model = SARIMAX(train, exog=exog_train, order=(1,1,1),
                        enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)

fc_test = arimax_model.get_forecast(steps=H_test, exog=exog_test)
test_fc['ARIMAX'] = fc_test.predicted_mean
ci_test = fc_test.conf_int(alpha=0.05)
test_lower['ARIMAX'], test_upper['ARIMAX'] = ci_test.iloc[:, 0], ci_test.iloc[:, 1]

arimax_full = SARIMAX(ts, exog=exog_hist, order=(1,1,1),
                       enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)

fc_future = arimax_full.get_forecast(steps=H_future, exog=exog_future)
future_fc['ARIMAX'] = fc_future.predicted_mean
ci_future = fc_future.conf_int(alpha=0.05)
future_lower['ARIMAX'], future_upper['ARIMAX'] = ci_future.iloc[:, 0], ci_future.iloc[:, 1]

residuals_dict['ARIMAX'] = get_model_residuals(arimax_full, ts)

# ---------- 4e. Prophet ----------
if PROPHET_INSTALLED:
    print("Fitting Prophet ...")
    prophet_train = pd.DataFrame({'ds': train.index, 'y': train.values})
    prophet_train = pd.concat([prophet_train.reset_index(drop=True), exog_train.reset_index(drop=True)], axis=1)

    p_model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    p_model.add_regressor('Partial_Transition')
    p_model.add_regressor('Full_Shock')
    p_model.add_regressor('RBI_FrontRun')
    p_model.fit(prophet_train)

    future_test_p = exog_test.copy()
    future_test_p['ds'] = exog_test.index
    fc_test_p = p_model.predict(future_test_p)
    test_fc['Prophet'] = fc_test_p['yhat'].values
    test_lower['Prophet'] = fc_test_p['yhat_lower'].values
    test_upper['Prophet'] = fc_test_p['yhat_upper'].values

    prophet_full = pd.DataFrame({'ds': ts.index, 'y': ts.values})
    prophet_full = pd.concat([prophet_full.reset_index(drop=True), exog_hist.reset_index(drop=True)], axis=1)
    p_full = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    p_full.add_regressor('Partial_Transition')
    p_full.add_regressor('Full_Shock')
    p_full.add_regressor('RBI_FrontRun')
    p_full.fit(prophet_full)

    future_future_p = exog_future.copy()
    future_future_p['ds'] = exog_future.index
    fc_future_p = p_full.predict(future_future_p)
    future_fc['Prophet'] = fc_future_p['yhat'].values
    future_lower['Prophet'] = fc_future_p['yhat_lower'].values
    future_upper['Prophet'] = fc_future_p['yhat_upper'].values

    cols_for_pred = ['ds', 'Partial_Transition', 'Full_Shock', 'RBI_FrontRun']
    resid_p = p_full.predict(prophet_full[cols_for_pred])['yhat']
    residuals_dict['Prophet'] = pd.Series(ts.values - resid_p.values, index=ts.index)

# ---------- 4f. Theta ----------
print("Fitting Theta ...")
tm = ThetaModel(train, period=12).fit()
test_fc['Theta'] = tm.forecast(steps=H_test)
resid_std_tm = get_resid_std(tm, train)
test_lower['Theta'], test_upper['Theta'] = empirical_ci(test_fc['Theta'], resid_std_tm)

tm_full = ThetaModel(ts, period=12).fit()
future_fc['Theta'] = tm_full.forecast(steps=H_future)
future_lower['Theta'], future_upper['Theta'] = empirical_ci(future_fc['Theta'], resid_std_tm)
residuals_dict['Theta'] = get_model_residuals(tm_full, ts)

# ---------- 4g. Holt-Winters ----------
print("Fitting Holt-Winters ...")
hw = ExponentialSmoothing(train, trend='add', seasonal='add', seasonal_periods=12).fit()
test_fc['Holt-Winters'] = hw.forecast(H_test)
resid_std_hw = get_resid_std(hw, train)
test_lower['Holt-Winters'], test_upper['Holt-Winters'] = empirical_ci(test_fc['Holt-Winters'], resid_std_hw)

hw_full = ExponentialSmoothing(ts, trend='add', seasonal='add', seasonal_periods=12).fit()
future_fc['Holt-Winters'] = hw_full.forecast(H_future)
future_lower['Holt-Winters'], future_upper['Holt-Winters'] = empirical_ci(future_fc['Holt-Winters'], resid_std_hw)
residuals_dict['Holt-Winters'] = get_model_residuals(hw_full, ts)

# ---------- 4h. SARIMA ----------
print("Fitting SARIMA ...")
sm_model = SARIMAX(train, order=(1,1,1), seasonal_order=(1,1,1,12),
                   enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
fc_test = sm_model.get_forecast(steps=H_test)
test_fc['SARIMA'] = fc_test.predicted_mean
ci_test = fc_test.conf_int(alpha=0.05)
test_lower['SARIMA'], test_upper['SARIMA'] = ci_test.iloc[:, 0], ci_test.iloc[:, 1]

sm_full = SARIMAX(ts, order=(1,1,1), seasonal_order=(1,1,1,12),
                  enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
fc_future = sm_full.get_forecast(steps=H_future)
future_fc['SARIMA'] = fc_future.predicted_mean
ci_future = fc_future.conf_int(alpha=0.05)
future_lower['SARIMA'], future_upper['SARIMA'] = ci_future.iloc[:, 0], ci_future.iloc[:, 1]
residuals_dict['SARIMA'] = get_model_residuals(sm_full, ts)

# ---------- 5. Calculate Metrics (Convert Back to FO Scale) ----------
test_fo_actuals = np.exp(test)

for name in test_fc.keys():
    fc_fo = np.exp(test_fc[name])
    results[name] = {
        'MAE': mean_absolute_error(test_fo_actuals, fc_fo),
        'RMSE': np.sqrt(mean_squared_error(test_fo_actuals, fc_fo)),
        'MAPE': mape(test_fo_actuals, fc_fo)
    }

metrics = pd.DataFrame(results).T[['MAE', 'RMSE', 'MAPE']]
print("\n=========== Model Comparison (Evaluated on Original FO Scale) ===========")
print(metrics.round(4).to_string())

best_model = metrics['MAPE'].idxmin()
print(f"\nBest model by MAPE: {best_model}")

# ---------- 6. Build Output Frames ----------
def build_df(index, fc, lower, upper, actuals_lfo=None):
    data = {}
    if actuals_lfo is not None:
        data['Actual_FO'] = np.exp(np.asarray(actuals_lfo).flatten())
    for name in fc.keys():
        data[f'{name}_FO_Forecast'] = np.exp(np.asarray(fc[name]).flatten())
        data[f'{name}_FO_Lower_95%'] = np.exp(np.asarray(lower[name]).flatten())
        data[f'{name}_FO_Upper_95%'] = np.exp(np.asarray(upper[name]).flatten())
        data[f'{name}_LFO_Forecast'] = np.asarray(fc[name]).flatten()
        data[f'{name}_LFO_Lower_95%'] = np.asarray(lower[name]).flatten()
        data[f'{name}_LFO_Upper_95%'] = np.asarray(upper[name]).flatten()
    return pd.DataFrame(data, index=index)

test_df = build_df(test.index, test_fc, test_lower, test_upper, actuals_lfo=test)
future_df = build_df(future_idx, future_fc, future_lower, future_upper)
future_df['Best_Model'] = best_model
future_df['Best_Forecast'] = future_df[f'{best_model}_FO_Forecast']

# ---------- 7. Save to Excel ----------
with pd.ExcelWriter(OUTPUT_PATH, engine='openpyxl') as w:
    metrics.round(4).to_excel(w, sheet_name='Model_Comparison')
    test_df.round(0).to_excel(w, sheet_name='Test_Forecasts')
    future_df.round(0).to_excel(w, sheet_name='Future_Forecasts')

print(f"\nForecast output written to: {OUTPUT_PATH}")

# ---------- 8. Save Residuals & Generate Graphs ----------
best_resid = residuals_dict.get(best_model, sm_full.resid).dropna()
resid_trimmed = best_resid.iloc[24:] if len(best_resid) > 24 else best_resid
resid_trimmed.to_frame('residual').to_excel(str(HERE / "FO_Residuals_Dated.xlsx"))

plt.figure(figsize=(12, 5))
plt.plot(resid_trimmed.index, resid_trimmed.values, color='purple', label=f'{best_model} Residuals (LFO Scale)')
plt.axhline(0, color='black', linestyle='--', alpha=0.7)
plt.title(f'Residuals of Best Model ({best_model}) - Log Scale (Burn-in Trimmed)')
plt.xlabel('Date'); plt.ylabel('Residual (Log Error)')
plt.legend(); plt.grid(True, alpha=0.3); plt.tight_layout()
plt.savefig(str(HERE / "FO_Residuals.png"), dpi=300)
plt.show()

plt.figure(figsize=(14, 6))
hist_to_plot = np.exp(ts).loc['2024-01-01':]
plt.plot(hist_to_plot.index, hist_to_plot.values, label='Historical FO Volume', color='blue', marker='o', markersize=4)
plt.plot(future_df.index, future_df['Best_Forecast'], label=f'Forecast ({best_model})', color='red', marker='o', markersize=5)
plt.fill_between(future_df.index, future_df[f"{best_model}_FO_Lower_95%"], future_df[f"{best_model}_FO_Upper_95%"],
                 color='red', alpha=0.15, label='95% Confidence Interval')
plt.axvline(x=ts.index[-1], color='gray', linestyle='--', alpha=0.8, label='Forecast Start (Aug-2026)')
plt.title('FO Trade Volume Forecast (Aug 2026 - Mar 2028) with 95% CI')
plt.xlabel('Date'); plt.ylabel('FO Trade Volume')
plt.legend(loc='upper left'); plt.grid(True, alpha=0.3); plt.tight_layout()
plt.savefig(str(HERE / "FO_Forecast_Path.png"), dpi=300)
plt.show()

print("Done.")
