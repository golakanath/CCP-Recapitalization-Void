# Data correction, 7 October 2026

Core SGF for the December 2022 quarter was entered as 5,197.37 (the June 2023 figure). The correct value is 4,432.51.
`SGF_corrected_07102026.xlsx/.xls` holds the corrected quarterly panel (only this one cell differs from `Paper_Regression_Data.xlsx`, sheet `ACTUAL_Jun2026_QTRLY`).

Affected outputs (re-estimated): Table 8 and Annexure F (Tables F1, F2; Figures F1, F2), Annexure H (LSGF ADF row; Johansen trace tests), and the actual-SGF series in Figures 3, 4, 5 and 11.
Unaffected: Table 6 (k and the March 2028 projection use only March and June 2026), and every OI/CM/FO/VIX model.
Quarterly SGF is now strictly increasing in all 26 quarter-on-quarter changes.

`Paper_Regression_Data.xlsx` (sheet `ACTUAL_Jun2026_QTRLY`, and the `SGF_K_RATIO_OI_YTDOI` sheet) still shows the superseded Dec-2022 value of 5,197.37; use `SGF_corrected_07102026.xlsx` for the regressions and figures.
`SAS_Table8_AnnexureF_ARDL.sas` reproduces Table 8 and Annexure F from the corrected panel.
