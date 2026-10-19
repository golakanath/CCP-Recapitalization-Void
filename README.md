# The CCP Recapitalization Void: Pre-Funding Systemic Risk in India's Equity & Equity Derivatives Market

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23480331.svg)](https://doi.org/10.5281/zenodo.23480331)

**Current release: v1.0.5** (archived on Zenodo, DOI [10.5281/zenodo.23480331](https://doi.org/10.5281/zenodo.23480331); see "Version history" below).

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

An earlier draft of this research was part of the background material circulated by the Securities and Exchange Board of India (SEBI) to the members of its Expert Working Group on "Review of Economic Structure of Clearing Corporations" before the group's first meeting in July 2025, to which the author was invited. The results in this repository and the paper were derived independently from public data. See the paper's Conflict of Interest and Disclosure Statement for the full disclosure. No confidential or non-public documents are included in this repository.

## Repository structure

The repository is flat: every file sits at the top level, so each script, input file and output sits next to the others.

```
Data (inputs)
  CM_ORIGINAL_DATA.xlsx, FO_ORIGINAL_DATA.xlsx, OI.xlsx   # Daily CM volume, FO volume and open interest, Jan 2020-Jul 2026
  VIX_ORIGINAL_DATA.xlsx                                  # Daily India VIX, Jan 2020-Jul 2026
  vixreg1.xlsx                                            # Monthly panel for the Asymmetric ADL stress model (sheet "RESULTS (2)", 79 months, N = 77 after differencing/lag)
  CM_OUTLIER_RMVD.xlsx, FO_OUTLIER_RMVD.xlsx, OI_MDA.xlsx # Monthly daily averages (CM/FO with 8 dates excluded; OI with none)
  SGF_QTRLY.xlsx                                          # Quarterly Core SGF, OI, YTDOI, CM, FO, VIX (Dec 2019-Jun 2026), corrected
  SGF_OI_LAGSGF.xlsx                                      # Spot-OI bounds-test input: MONTHYR, SGF1, OI, LSGF, LAGLSGF, LOI (log columns are LN formulas)
  SGF_OI_LAGSGF1.xlsx                                     # YTDOI bounds-test input: as above plus YTDOI, LYTDOI (log columns are LN formulas)
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
  bounds_test_spot_oi.py, bounds_test_ytdoi.py            # Annexure H: Pesaran-Shin-Smith bounds test, small-sample critical values (Spot OI / YTDOI)

Outputs
  Regression_LSGF_LYTDOI_LAGLSGF.html                     # SAS output, preferred specification
  Regression_LSGF_LOI_LAGLSGF.html                        # SAS output, alternative specification
  Unit_Test_Results.xlsx                                  # Output of unit_root_tests.py (Annexure H)
  output/bounds_oi_*.csv, output/bounds_ytdoi_*.csv       # Written by the bounds-test scripts (regression and critical values)
  cm_forecast_results.xlsx, OI_Forecast_Results.xlsx,
  All_DATA_ACTUAL_FORECAST_JAN2020_MAR2028.xlsx           # Forecast paths and combined actual-plus-forecast series

figures/                                                # Chart code and figures for the paper (see "Figures" below)
  Financials_NSE_NCL_Charges.xlsx                       # Annual NSE operating income and NCL clearing charges, FY2007-FY2026 (input to Figures 4 and 5)
  plot_*.py                                             # One script per figure (17 scripts)
  Figure_*.png                                          # The 19 figures used in the paper

README.md
```

## Data notes

- **CM and FO**: Monthly daily averages exclude 8 dates — 6 Muhurat trading sessions and 2 SEBI-mandated Business Continuity Plan (BCP) test dates — because these are non-representative, procedurally distinct trading sessions rather than data errors. November 27, 2020 was investigated as a possible Muhurat misclassification and confirmed instead to be an MSCI index rebalancing day; it is retained in all series. Full outlier rationale is in the paper's Section 3.2 and Table 2.
- **OI**: No outlier exclusion is applied. OI is a stock (point-in-time open positions), not a flow like CM/FO volume, so the same procedural-date argument for exclusion does not apply; retaining all dates is the paper's primary specification (Section 3.4).
- **OI forecasting model**: `oi_forecast.py` fits `ARIMA(2,1,2)` directly on **raw OI levels**, not log-transformed — this is deliberate, not an inconsistency with CM/FO's log-scale treatment. See the paper's Section 3.5 for why OI's larger absolute scale makes the log-transform safeguard unnecessary here.
- **Quarterly SGF data**: `SGF_QTRLY.xlsx` includes both YTDOI (fiscal-year-to-date cumulative average OI) and Spot OI (plain monthly daily average at quarter-end) as alternative regressors for the ARDL model — see Section 3.6 and Table 8 for why both are reported.
- **ARDL regression panel**: `paper_regression_data.sas7bdat` and `Paper_Regression_Data.xlsx` contain the same corrected quarterly panel (the workbook holds the same values as the SAS file, not a byte-for-byte copy): SGF, CM, OI, VIX, FO, YTDOI and their log/lag transforms (LSGF, LAGLSGF, LOI, LYTDOI, LCM, LVIX). It is the direct input to `ardl_ytdoi.sas` and `ardl_spotoi.sas` (Table 8). N = 26 usable quarters (Mar-2020 to Jun-2026), plus one Dec-2019 base row that supplies the lag. The scripts use the supplied `LAGLSGF` column, not `lag(LSGF)`, because LSGF is blank in the Dec-2019 base row and `lag()` would drop an observation (N = 25).
- **Reproducibility across software versions**: Forecast paths and full-sample results reproduce exactly (for example, the FO ARIMAX March-2028 forecast of 69,955,687 and the CM Holt-Winters forecast of 189,222). Holdout error metrics for models fitted by numerical optimisation (notably the FO ARIMAX, paper MAPE 9.34%) can differ in the third or fourth significant digit across `statsmodels` versions (a re-run produced 9.33%), and Prophet's 95% interval bounds vary slightly between runs because they are simulated. Neither affects the paper's conclusions: ARIMAX and Theta remain effectively tied for FO, and Holt-Winters remains the reported CM model.
- **Why two languages**: The two Table 8 ARDL regressions (`ardl_ytdoi.sas`, `ardl_spotoi.sas`) were originally estimated in SAS (`PROC AUTOREG`), as that was the author's working environment for this stage of the analysis, and are included in their native form rather than re-implemented in Python, so the code exactly matches what produced the published coefficients. Every other script in this repository is Python. The same data step also constructs differenced and lagged variables (`DOI`, `DVIX`, `DVIXSQ`, `DVIXPOS`, `DCM`, `DYTDOI`, etc.). A quarterly regression of `DYTDOI` on these variables is a supplementary check only; the paper's Asymmetric ADL stress model (Section 5.4, Annexure I) is a separate monthly model (N = 77) estimated in Python in `asymmetric_adl.py`.

- **Bounds-test inputs**: `SGF_OI_LAGSGF.xlsx` (Spot OI) and `SGF_OI_LAGSGF1.xlsx` (YTDOI) hold the monthly-dated quarterly series used by the two bounds-test scripts. The log columns are Excel `LN()` formulas, and the scripts in any case rebuild the logs from the raw columns (SGF1, OI or YTDOI), so the results do not depend on cached values.
- **March 2026 SGF**: the panel uses ₹13,027.77 crore for the March 2026 quarter. NCL's audited statements show ₹13,026.77 crore. The ₹1 crore difference is immaterial on the log scale and does not change any reported result at the precision shown. It is disclosed in a note under Table F2 of the paper. The panel has not been changed so that the archived data match the figures in the paper exactly.

## Data correction (7 October 2026)

Core SGF for the December 2022 quarter had been entered as 5,197.37 (the June 2023 figure). The correct value, from NCL's published financial statements, is **4,432.51**. Quarterly Core SGF is therefore strictly increasing in all 26 quarter-on-quarter changes, with no decline in any quarter.

- Corrected panel: `SGF_corrected_07102026.xls` (the same correction has been applied to `SGF_QTRLY.xlsx`, `SGF_OI_LAGSGF.xlsx`, `SGF_OI_LAGSGF1.xlsx`, `Paper_Regression_Data.xlsx` and `paper_regression_data.sas7bdat`).
- Only the Dec-2022 SGF cell, and the cells computed from it (LSGF, LAGLSGF in the Mar-2023 row, k and the rolling k averages), differ from the earlier version. No OI, CM, FO or VIX value changed.
- Re-estimated outputs: Table 8, Annexure F (Tables F1 and F2, Figures F1 and F2), Annexure H (ADF and Johansen tests, re-run on `Unit.xlsx`; `Unit_Test_Results.xlsx`), and the actual-SGF series in Figures 3, 4, 5 and 11 of the paper.
- Follow-up (v1.0.3): in `SGF_OI_LAGSGF.xlsx` the Dec-2022 LSGF and the Mar-2023 LAGLSGF had been typed as values from the old figure. They are now `LN()` formulas giving the correct 8.396721 (= ln 4,432.51).
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

`oi_estimation_window_sensitivity.py` reproduces Table 9a's sensitivity range (~20–40%) by recomputing the OI forecast, SGF projection, and implied recovery rate across three alternative estimation windows.

### Reproducing the bounds test (Annexure H)

```bash
python bounds_test_spot_oi.py      # reads SGF_OI_LAGSGF.xlsx
python bounds_test_ytdoi.py        # reads SGF_OI_LAGSGF1.xlsx
# optional: pass another workbook path as the first argument
```

Only `numpy`, `pandas` and `openpyxl` are needed. Each script rebuilds the logs from the raw columns and estimates the unrestricted error-correction form of the ARDL(1,1) (Pesaran, Shin and Smith 2001, Case III: unrestricted intercept, no trend, k = 1):

ΔLSGF_t = a + π1·LSGF_(t-1) + π2·LX_(t-1) + g·ΔLX_t + e_t

where X is Spot OI or YTDOI. The bounds F-statistic tests π1 = π2 = 0. Because the sample is small (25 usable quarterly observations), the scripts simulate the I(0) and I(1) critical bounds for that sample size (20,000 replications, fixed seed 20261019) rather than using asymptotic tables. Results are written to `./output/` as CSV files.

| Regressor | F-statistic | Observations | 10% bounds I(0)/I(1) | 5% bounds | 1% bounds |
|---|---|---|---|---|---|
| Spot OI | 2.854 | 25 | 4.322 / 5.191 | 5.453 / 6.479 | 8.108 / 9.855 |
| YTDOI | 3.228 | 25 | 4.322 / 5.191 | 5.453 / 6.479 | 8.108 / 9.855 |

Neither F-statistic exceeds the 10% lower bound, so the test does not reject the null of no level relationship. With 25 observations the test has low power, so this does not establish the absence of a long-run relationship. The paper therefore treats the single-cointegrating-relation conclusion from the Johansen test as tentative, and reports the ARDL(1,1) as a short-run dynamic projection model. See Annexure H. Narayan (2005) tabulates critical values only for n ≥ 30, so simulated values are used here.

### Reproducing the stress test

```bash
python asymmetric_adl.py
```

### Reproducing the figures

The paper's charts are in the `figures/` folder: one `plot_*.py` script per chart, the resulting `Figure_*.png` files, and `Financials_NSE_NCL_Charges.xlsx` (annual data for Figures 4 and 5). Each script finds its input files in the repository root (or in the `figures/` folder) and writes its PNG next to itself, so a script can be run from anywhere:

```
cd figures
python plot_sgf_composition.py
```

Re-running a script regenerates the figure in the paper; differences between machines are limited to font rendering. Notes:

- Figures B1 (SARIMA residuals) and B2 (CM forecast) come from `cm_forecast.py`, which draws them itself; they are included as images only.
- `plot_fo_residuals.py` reads `FO_Residuals_Dated.xlsx`, which `fo_forecast.py` writes. Run `fo_forecast.py` first.
- Some charts are illustrative and use values typed into the script rather than read from a data file (the waterfall, stress and sensitivity figures); each has a comment identifying the table or disclosure its values come from.
- The scripts read `SGF_corrected_07102026.xlsx` or `SGF_corrected_07102026.xls`, whichever is present. The `.xls` format needs `xlrd` (in `requirements.txt`).
- `Financials_NSE_NCL_Charges.xlsx` (FY2007-FY2026) is compiled by the author from NSE's annual reports (standalone financial statements). Columns: NSE revenue from operations, clearing and settlement charges paid by NSE (to NCL), and their ratio (the "Share" used in Figure 4). The FY2025 and FY2026 rows are from NSE's Integrated Annual Report 2025-26, Standalone Statement of Profit and Loss (revenue from operations ₹14,914.44 crore and ₹15,433.00 crore; clearing and settlement charges ₹796.86 crore and ₹1,357.54 crore). The consolidated revenue figure is not used.
- The chart code was written with the assistance of Claude (Anthropic); the author supplied and verified all underlying data and checked every figure. See the paper's AI Use Disclosure.

## Version history

| Version | Zenodo DOI | Change |
|---|---|---|
| v1.0.0 | 10.5281/zenodo.23285555 | First archived release |
| v1.0.1 | 10.5281/zenodo.23429548 | Documentation and file updates |
| v1.0.2 | 10.5281/zenodo.23447130 | Dec-2022 SGF correction (5,197.37 to 4,432.51) propagated to the data files |
| v1.0.3 | 10.5281/zenodo.23447404 | `SGF_OI_LAGSGF.xlsx`: Dec-2022 LSGF and LAGLSGF replaced by `LN()` formulas |
| v1.0.4 | 10.5281/zenodo.23480010 | Added the small-sample bounds-test scripts (`bounds_test_spot_oi.py`, `bounds_test_ytdoi.py`) and `SGF_OI_LAGSGF1.xlsx` |
| v1.0.5 | 10.5281/zenodo.23480331 | README updated (bounds test, March 2026 SGF note, version history); data and code unchanged from v1.0.4 |

## Where to get help

For questions about the methodology, data construction, or reproducing a specific result, please [open an issue](../../issues) in this repository. When reporting a discrepancy, please include the script name, the exact command run, and your `statsmodels` version (for Python scripts) or SAS version (for the two ARDL scripts) — several models in this repository (particularly the OI ARIMA(2,1,2) specification) are sensitive to solver and version differences; see the reproducibility notes in the paper's Section 3.5 and Annexure D before assuming a discrepancy is a data or code error.

## Who maintains this project

This repository is maintained by the paper's author. The author discloses institutional affiliations relevant to this research — including a Governing Board role at NSE Clearing Limited, a Standing Committee membership at the Reserve Bank of India, and past membership of the Benchmark Oversight Committee of Financial Benchmarks India Limited (FBIL) until 2021 — in the paper's Conflict of Interest and Disclosure Statement. All data in this repository is drawn from public disclosures (NSE/NCL Bhavcopy data, NCL's quarterly and annual financial statements, and SEBI/RBI circulars, each cited in the paper); no non-public information from either affiliation informed any part of this analysis.

Contributions, corrections, and independent replications are welcome via pull request or issue.

## Citation

If you use this data or code, please cite the archived version of this replication package:

> Nath, Golaka C. (2026). *Replication package for "The CCP Recapitalization Void: Pre-Funding Systemic Risk in India's Equity & Equity Derivatives Market"* (v1.0.5) [Data and code]. Zenodo. https://doi.org/10.5281/zenodo.23480331

The DOI above is the version DOI for v1.0.5. The paper's data-availability statement cites v1.0.4 (10.5281/zenodo.23480010), whose data and code are identical. All versions are reachable through the Zenodo record https://zenodo.org/records/23480331.

and the paper, once published: Nath, G. C. "The CCP Recapitalization Void: Pre-Funding Systemic Risk in India's Equity & Equity Derivatives Market." [Journal details to be added on publication.]

## License

- **Code** (all `.py` and `.sas` files): [MIT License](LICENSE). You may use, copy, modify and redistribute the code freely, including commercially, provided the copyright notice is kept.
- **Data compiled by the author and the paper text** (the Excel and SAS data files, the figures and the manuscript): [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). You may use and redistribute them freely, provided you cite the paper (see Citation).
- **Underlying source data** (NSE, NSE Clearing Limited, SEBI and RBI public disclosures) remain subject to the terms of the original publishers. The licences above apply only to the author's own compilation, code and analysis.
- Everything is provided "as is", without warranty. The analysis is the author's own and does not represent the views of any institution with which the author is affiliated.
