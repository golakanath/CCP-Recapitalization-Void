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

The repository is flat: every file sits at the top level, so each script, input file and output sits next to the others.

```
Data (inputs)
  CM_ORIGINAL_DATA.xlsx, FO_ORIGINAL_DATA.xlsx, OI.xlsx   # Daily CM volume, FO volume and open interest, Jan 2020-Jul 2026
  VIX_ORIGINAL_DATA.xlsx                                  # Daily India VIX, Jan 2020-Jul 2026
  CM_OUTLIER_RMVD.xlsx, FO_OUTLIER_RMVD.xlsx, OI_MDA.xlsx # Monthly daily averages (CM/FO with 8 dates excluded; OI with none)
  SGF_QTRLY.xlsx, SGF_OI_LAGSGF.xlsx                      # Quarterly Core SGF, OI, YTDOI, CM, FO, VIX (Dec 2019-Jun 2026), corrected
  SGF_corrected_07102026.xls                              # Corrected quarterly panel (see "Data correction")
  paper_regression_data.sas7bdat                          # Quarterly ARDL panel, native SAS format (corrected)
  Paper_Regression_Data.xlsx                              # Same panel, Excel format (corrected)
  Unit.xlsx                                               # Six log series for the unit-root and cointegration tests (N = 26)

Code
  cm_forecast.py, fo_forecast.py, oi_forecast.py          # Forecasting models (Sections 3.3-3.5)
  oi_path_mapping.py                                      # OI path mapping used for the SGF projection
  oi_estimation_window_sensitivity.py                     # Table 9a: sensitivity to the OI estimation window
  ardl_ytdoi.sas, ardl_spotoi.sas                         # Table 8 ARDL(1,1): preferred (LYTDOI) and alternative (LOI)
  ardl_python.py                                          # Python equivalent of the two SAS programs (no SAS needed)
  unit_root_tests.py                                      # Annexure H: ADF and Johansen tests
  asymmetric_adl.py                                       # VIX-shock stress model (Section 5.4)

Outputs
  Regression_LSGF_LYTDOI_LAGLSGF.html                     # SAS output, preferred specification
  Regression_LSGF_LOI_LAGLSGF.html                        # SAS output, alternative specification
  Unit_Test_Results.xlsx                                  # Output of unit_root_tests.py (Annexure H)
  cm_forecast_results.xlsx, OI_Forecast_Results.xlsx,
  All_DATA_ACTUAL_FORECAST_JAN2020_MAR2028.xlsx           # Forecast paths and combined actual-plus-forecast series

README.md
```

## Data notes

- **CM and FO**: Monthly daily averages exclude 8 dates — 6 Muhurat trading sessions and 2 SEBI-mandated Business Continuity Plan (BCP) test dates — because these are non-representative, procedurally distinct trading sessions rather than data errors. November 27, 2020 was investigated as a possible Muhurat misclassification and confirmed instead to be an MSCI index rebalancing day; it is retained in all series. Full outlier rationale is in the paper's Section 3.2 and Table 2.
- **OI**: No outlier exclusion is applied. OI is a stock (point-in-time open positions), not a flow like CM/FO volume, so the same procedural-date argument for exclusion does not apply; retaining all dates is the paper's primary specification (Section 3.4).
- **OI forecasting model**: `oi_forecast.py` fits `ARIMA(2,1,2)` directly on **raw OI levels**, not log-transformed — this is deliberate, not an inconsistency with CM/FO's log-scale treatment. See the paper's Section 3.5 for why OI's larger absolute scale makes the log-transform safeguard unnecessary here.
- **Quarterly SGF data**: `SGF_QTRLY.xlsx` includes both YTDOI (fiscal-year-to-date cumulative average OI) and Spot OI (plain monthly daily average at quarter-end) as alternative regressors for the ARDL model — see Section 3.6 and Table 8 for why both are reported.
- **ARDL regression panel**: `paper_regression_data.sas7bdat` and `Paper_Regression_Data.xlsx` contain the same corrected quarterly panel (the workbook holds the same values as the SAS file, not a byte-for-byte copy): SGF, CM, OI, VIX, FO, YTDOI and their log/lag transforms (LSGF, LAGLSGF, LOI, LYTDOI, LCM, LVIX). It is the direct input to `ardl_ytdoi.sas` and `ardl_spotoi.sas` (Table 8). N = 26 usable quarters (Mar-2020 to Jun-2026), plus one Dec-2019 base row that supplies the lag. The scripts use the supplied `LAGLSGF` column, not `lag(LSGF)`, because LSGF is blank in the Dec-2019 base row and `lag()` would drop an observation (N = 25).
- **Why two languages**: The two Table 8 ARDL regressions (`ardl_ytdoi.sas`, `ardl_spotoi.sas`) were originally estimated in SAS (`PROC AUTOREG`), as that was the author's working environment for this stage of the analysis, and are included in their native form rather than re-implemented in Python, so the code exactly matches what produced the published coefficients. Every other script in this repository is Python. The same data step also constructs differenced and lagged variables (`DOI`, `DVIX`, `DVIXSQ`, `DVIXPOS`, `DCM`, `DYTDOI`, etc.). A quarterly regression of `DYTDOI` on these variables is a supplementary check only; the paper's Asymmetric ADL stress model (Section 5.4, Annexure I) is a separate monthly model (N = 77) estimated in Python in `asymmetric_adl.py`.

## Data correction (7 October 2026)

Core SGF for the December 2022 quarter had been entered as 5,197.37 (the June 2023 figure). The correct value, from NCL's published financial statements, is **4,432.51**. Quarterly Core SGF is therefore strictly increasing in all 26 quarter-on-quarter changes, with no decline in any quarter.

- Corrected panel: `SGF_corrected_07102026.xls` (the same correction has been applied to `SGF_QTRLY.xlsx`, `SGF_OI_LAGSGF.xlsx`, `Paper_Regression_Data.xlsx` and `paper_regression_data.sas7bdat`).
- Only the Dec-2022 SGF cell, and the cells computed from it (LSGF, LAGLSGF in the Mar-2023 row, k and the rolling k averages), differ from the earlier version. No OI, CM, FO or VIX value changed.
- Re-estimated outputs: Table 8, Annexure F (Tables F1 and F2, Figures F1 and F2), Annexure H (ADF and Johansen tests, re-run on `Unit.xlsx`; `Unit_Test_Results.xlsx`), and the actual-SGF series in Figures 3, 4, 5 and 11 of the paper.
- Unaffected: Table 6 (k and the March 2028 projection use only March and June 2026), the capital-gap figures, the sufficiency-threshold rate, and every OI, CM and FO forecasting model.

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

Running `ardl_ytdoi.sas` and `ardl_spotoi.sas` requires SAS, which is commercial (proprietary) software. A licensed SAS 9.4 works, and so does the free SAS OnDemand for Academics (SAS Studio), which is what the author used; it is free for non-commercial academic use. The other scripts are Python and need no SAS. Without SAS access, the saved outputs `Regression_LSGF_LYTDOI_LAGLSGF.html` and `Regression_LSGF_LOI_LAGLSGF.html` show the full Table 8 results, and `Paper_Regression_Data.xlsx` holds the same panel. For readers without SAS, `ardl_python.py` runs the same two regressions in Python (numpy, pandas, scipy only). It reads `paper_regression_data.sas7bdat` directly, and reproduces the SAS coefficients, standard errors, R-square, AIC/SBC, Durbin-Watson and Godfrey tests exactly. The SAS programs remain the code that produced the published Table 8; the Python script is an independent replication. Everything else in this repository runs in Python only.

### Reproducing the forecasts

Each forecasting script follows the same pattern: load the processed monthly data, split into a 63-month training window (Jan 2020–Mar 2025) and 16-month holdout (Apr 2025–Jul 2026), fit and compare candidate models on the holdout, then refit the best model on the full sample to forecast Aug 2026–Mar 2028.

```bash
python cm_forecast.py
python fo_forecast.py
python oi_forecast.py
```

Each script writes a model-comparison table and a full forecast path (point estimate + 95% interval) to the repository folder (for example, `cm_forecast_results.xlsx`).

### Reproducing the SGF projection and sufficiency-threshold rate

```
Run in SAS (SAS Studio / SAS OnDemand for Academics / SAS 9.4):
  ardl_ytdoi.sas    # Table 8, preferred specification (LYTDOI)
  ardl_spotoi.sas   # Table 8, alternative specification (LOI)
```

Both scripts read `paper_regression_data.sas7bdat` (corrected panel; see "Data correction" above) and reproduce Table 8's coefficients exactly (LYTDOI = 0.0792, LAGLSGF = 0.9108, R² = 0.9888, AIC = -70.037 for the preferred specification; LOI = 0.0734, LAGLSGF = 0.9250, R² = 0.9886, AIC = -69.618 for the alternative — a ΔAIC of ~0.4 in favor of the YTDOI specification, as reported in the paper). The saved SAS outputs are `Regression_LSGF_LYTDOI_LAGLSGF.html` (preferred) and `Regression_LSGF_LOI_LAGLSGF.html` (alternative).

```bash
python unit_root_tests.py
python oi_estimation_window_sensitivity.py
```

`unit_root_tests.py` reads `Unit.xlsx` (it looks in its own folder, `data/raw/` and the working folder, so it runs from anywhere; a path can also be passed as an argument) and writes `Unit_Test_Results.xlsx` next to it. It reproduces Annexure H: on the corrected panel LSGF has ADF statistic 0.271 (p = 0.976) in levels and -3.889 (p = 0.002) in first differences, i.e. I(1); LYTDOI is I(1); LOI, LFO and LVIX are I(0); and the Johansen trace statistics (constant term, 2 lags in levels) are 17.331 / 1.881 for LOI & LSGF and 21.235 / 4.509 for LSGF & LYTDOI.

The last script reproduces Table 9a's sensitivity range (~20–40%) by recomputing the OI forecast, SGF projection, and implied recovery rate across three alternative estimation windows.

### Reproducing the stress test

```bash
python asymmetric_adl.py
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
