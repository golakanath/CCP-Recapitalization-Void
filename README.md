# The CCP Recapitalization Void: Pre-Funding Systemic Risk in India's Equity & Equity Derivatives Market

Replication package for the paper analyzing NSE Clearing Limited's (NCL) Settlement Guarantee Fund (SGF) adequacy, forecasting NCL's capital requirements through March 2028, and deriving a sufficiency-threshold transaction-charge recovery rate to close the projected funding gap.

## What this project does

This repository contains the complete data pipeline and analysis code behind the paper's central results:

- **Forecasts three market activity series** — Cash Market (CM) volume, Futures & Options (FO) volume, and Open Interest (OI) — from August 2026 through March 2028, using monthly daily-average data benchmarked across seven candidate time-series models per series (Naive, ARIMA, SARIMA, ETS, Holt-Winters, Theta, Prophet, and an Intervention ARIMAX for FO).
- **Projects NCL's Settlement Guarantee Fund (SGF) requirement** through an ARDL(1,1) model relating quarterly SGF to Open Interest, estimated on two alternative OI constructions (YTDOI and Spot OI) for robustness.
- **Derives a sufficiency-threshold transaction-charge recovery rate** — the minimum revenue-recovery rate that closes the capital gap between NCL's projected SGF obligation and its standalone reserves — reported as a range (~20–40%) across alternative OI-forecasting windows rather than a single point estimate.
- **Stress-tests the SGF against a VIX shock** using an Asymmetric ADL model of OI's response to volatility spikes.

Every model comparison, structural-break diagnosis, and sensitivity check reported in the paper is reproducible from the scripts and data in this repository.

## Why this project is useful

NCL is India's dominant clearing corporation and a wholly-owned subsidiary of NSE, which was listed on BSE in September 2026 — a transition that has historically implied reduced parental willingness to backstop NCL's capital needs on a discretionary basis. This repository provides a transparent, fully reproducible template for assessing whether a CCP's fee structure is actuarially sufficient to fund its own risk-bearing capacity, independent of parental support. The framework is built to be adapted to other exchange-owned CCPs facing similar standalone-capitalization questions, in India or elsewhere.

An earlier stage of this research was used by the Securities and Exchange Board of India (SEBI) as the basis for constituting an Expert Working Group on "Review of Economic Structure of Clearing Corporations" (see the paper's Introduction and Conflict of Interest Statement for the full disclosure of this relationship).

## Repository structure

```
.
├── data/
│   ├── raw/
│   │   ├── CM.xlsx              # Daily Cash Market volume, Jan 2020–Jul 2026
│   │   ├── FO.xlsx              # Daily Futures & Options volume, Jan 2020–Jul 2026
│   │   ├── OI.xlsx              # Daily/monthly Open Interest, Jan 2020–Jul 2026
│   │   ├── vix.xlsx             # Daily India VIX, Jan 2020–Jul 2026
│   │   └── quarterly_sgf.xlsx   # Quarterly Core SGF, OI, YTDOI, CM, FO, VIX (Dec 2019–Jun 2026)
│   ├── processed/
│   │   ├── cm_outlier_removed.xlsx   # CM monthly daily average, 8 dates excluded (see Data Notes)
│   │   ├── fo_outlier_removed.xlsx   # FO monthly daily average, same 8 dates excluded
│   │   └── oi_monthly.xlsx           # OI monthly daily average, no outlier exclusion (see Data Notes)
│   └── regression/
│       ├── paper_regression_data.sas7bdat   # Quarterly ARDL panel, native SAS format
│       └── Paper_Regression_Data.xlsx       # Same panel, Excel format (sheet: ACTUAL_Jun2026_QTRLY)
│
├── code/
│   ├── forecasting/
│   │   ├── cm_forecast.py       # 7-model comparison; Holt-Winters (log-scale) selected
│   │   ├── fo_forecast.py       # 7-model comparison incl. Intervention ARIMAX; ARIMAX selected
│   │   └── oi_forecast.py       # 4-model comparison incl. XGBoost; ARIMA(2,1,2) selected
│   ├── sgf_ardl/
│   │   ├── ardl_ytdoi.sas       # Preferred ARDL specification (LYTDOI regressor) — PROC AUTOREG
│   │   ├── ardl_spotoi.sas      # Alternative ARDL specification (LOI / Spot OI regressor) — PROC AUTOREG
│   │   └── unit_root_tests.py   # ADF unit-root tests and Johansen cointegration diagnostics
│   ├── stress_test/
│   │   └── asymmetric_adl.py    # VIX-shock stress model (Section 5.4)
│   └── sensitivity/
│       ├── oi_structural_break.py     # PELT break detection on OI growth rate
│       └── oi_estimation_window.py    # Sensitivity of OI forecast to estimation window
│
├── outputs/
│   ├── forecast_results/        # Model comparison tables and forecast paths per market
│   └── figures/                 # Residual diagnostics and forecast-path charts
│
├── paper/
│   └── Paper_CCP_Final.docx     # Full manuscript
│
└── README.md
```

## Data notes

- **CM and FO**: Monthly daily averages exclude 8 dates — 6 Muhurat trading sessions and 2 SEBI-mandated Business Continuity Plan (BCP) test dates — because these are non-representative, procedurally distinct trading sessions rather than data errors. November 27, 2020 was investigated as a possible Muhurat misclassification and confirmed instead to be an MSCI index rebalancing day; it is retained in all series. Full outlier rationale is in the paper's Section 3.2 and Table 2.
- **OI**: No outlier exclusion is applied. OI is a stock (point-in-time open positions), not a flow like CM/FO volume, so the same procedural-date argument for exclusion does not apply; retaining all dates is the paper's primary specification (Section 3.4).
- **OI forecasting model**: `oi_forecast.py` fits `ARIMA(2,1,2)` directly on **raw OI levels**, not log-transformed — this is deliberate, not an inconsistency with CM/FO's log-scale treatment. See the paper's Section 3.5 for why OI's larger absolute scale makes the log-transform safeguard unnecessary here.
- **Quarterly SGF data**: `quarterly_sgf.xlsx` includes both YTDOI (fiscal-year-to-date cumulative average OI) and Spot OI (plain monthly daily average at quarter-end) as alternative regressors for the ARDL model — see Section 3.6 and Table 8 for why both are reported.
- **ARDL regression panel**: `data/regression/paper_regression_data.sas7bdat` and `data/regression/Paper_Regression_Data.xlsx` (sheet `ACTUAL_Jun2026_QTRLY`) contain the identical quarterly panel — SGF, CM, OI, VIX, FO, YTDOI and their log/lag transforms (LSGF, LAGLSGF, LOI, LYTDOI, LCM, LVIX) — used as direct input to both `ardl_ytdoi.sas` and `ardl_spotoi.sas` (Table 8). N = 26 usable quarters (Mar-2020 to Jun-2026), plus one Dec-2019 base row consumed by the lag construction. The two file formats have been verified byte-identical across every regression variable, so either can be used to reproduce Table 8's coefficients exactly.
- **Why two languages**: The two Table 8 ARDL regressions (`ardl_ytdoi.sas`, `ardl_spotoi.sas`) were originally estimated in SAS (`PROC AUTOREG`), as that was the author's working environment for this stage of the analysis, and are included in their native form rather than re-implemented in Python, so the code exactly matches what produced the published coefficients. Every other script in this repository is Python. The same underlying data step also constructs the differenced/lagged variables (`DOI`, `DVIX`, `DVIXSQ`, `DVIXPOS`, `DCM`, etc.) used by the Asymmetric ADL stress model in `asymmetric_adl.py`, which is estimated independently in Python and cross-checked against the SAS-derived values.

## Getting started

### Requirements

```
python >= 3.9
pandas
numpy
statsmodels
scikit-learn
xgboost
prophet
matplotlib
scipy
openpyxl
```

Install with:
```bash
pip install -r requirements.txt
```

Running `ardl_ytdoi.sas` and `ardl_spotoi.sas` requires SAS (SAS 9.4, or the free SAS OnDemand for Academics / SAS Studio). No Python equivalent is provided for these two scripts, by design — see "Why two languages" in Data Notes above. Everything else in this repository runs in Python only.

### Reproducing the forecasts

Each forecasting script follows the same pattern: load the processed monthly data, split into a 63-month training window (Jan 2020–Mar 2025) and 16-month holdout (Apr 2025–Jul 2026), fit and compare candidate models on the holdout, then refit the best model on the full sample to forecast Aug 2026–Mar 2028.

```bash
python code/forecasting/cm_forecast.py
python code/forecasting/fo_forecast.py
python code/forecasting/oi_forecast.py
```

Each script writes a model-comparison table and a full forecast path (point estimate + 95% interval) to `outputs/forecast_results/`.

### Reproducing the SGF projection and sufficiency-threshold rate

```
Run in SAS (SAS Studio / SAS OnDemand for Academics / SAS 9.4):
  code/sgf_ardl/ardl_ytdoi.sas    # Table 8, preferred specification (LYTDOI)
  code/sgf_ardl/ardl_spotoi.sas   # Table 8, alternative specification (LOI)
```

Both scripts read `data/regression/paper_regression_data.sas7bdat` and reproduce Table 8's coefficients exactly (LYTDOI = 0.0899, LAGLSGF = 0.8926, R² = 0.9839, AIC = -60.887 for the preferred specification; LOI = 0.0839, LAGLSGF = 0.9080, R² = 0.9837, AIC = -60.592 for the alternative — a ΔAIC of ~0.3 in favor of the YTDOI specification, as reported in the paper).

```bash
python code/sgf_ardl/unit_root_tests.py
python code/sensitivity/oi_estimation_window.py
```

The last script reproduces Table 9a's sensitivity range (~20–40%) by recomputing the OI forecast, SGF projection, and implied recovery rate across three alternative estimation windows.

### Reproducing the stress test

```bash
python code/stress_test/asymmetric_adl.py
```

## Where to get help

For questions about the methodology, data construction, or reproducing a specific result, please [open an issue](../../issues) in this repository. When reporting a discrepancy, please include the script name, the exact command run, and your `statsmodels` version (for Python scripts) or SAS version (for the two ARDL scripts) — several models in this repository (particularly the OI ARIMA(2,1,2) specification) are sensitive to solver and version differences; see the reproducibility notes in the paper's Section 3.5 and Annexure D before assuming a discrepancy is a data or code error.

## Who maintains this project

This repository is maintained by the paper's author. The author discloses institutional affiliations relevant to this research — including a Governing Board role at NSE Clearing Limited and a Standing Committee membership at the Reserve Bank of India — in the paper's Conflict of Interest and Disclosure Statement. All data in this repository is drawn from public disclosures (NSE/NCL Bhavcopy data, NCL's quarterly and annual financial statements, and SEBI/RBI circulars, each cited in the paper); no non-public information from either affiliation informed any part of this analysis.

Contributions, corrections, and independent replications are welcome via pull request or issue.

## Citation

If you use this data or code, please cite:

> [Golaka C Nath]. "The CCP Recapitalization Void: Pre-Funding Systemic Risk in India's Equity & Equity Derivatives Market." [Journal/Working Paper details, once finalized].

## License

[Specify license here — e.g., MIT for code, CC-BY-4.0 for data and paper text]
