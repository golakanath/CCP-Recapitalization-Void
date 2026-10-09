/* =========================================================
   ARDL(1,1) Regression: LSGF on LYTDOI and LAGLSGF
   (YTDOI-preferred specification -- Table 8 of the paper)
   Verified against SAS output (PROC AUTOREG), N = 26,
   Mar-2020 to Jun-2026, corrected SGF data:
     LYTDOI coefficient   = 0.0792  (p = 0.0244)
     LAGLSGF coefficient  = 0.9108  (p < .0001)
     R-square             = 0.9888
     AIC                  = -70.037
     Godfrey LM (lags 1-4): all p > 0.39 -> no residual
       autocorrelation, consistent with no AR-error term
       being needed (method=ml has no effect here since no
       nlag= option is specified in the MODEL statement).
   Python equivalent: ardl_python.py (same results).
   ========================================================= */

data PaperReg;
    set '/home/u58761460/Oct2020/paper_regression_data.sas7bdat';
run;

data PaperReg;
    set PaperReg;
    LFO        = log(FO);
    DOI        = LOI - lag(LOI);
    DOI_Lag    = lag(DOI);
    DVIX       = LVIX - lag(LVIX);
    if DVIX > 0 then DVIXPOS = DVIX; else DVIXPOS = 0;
    DVIX_Lag   = lag(DVIX);
    DVIXSQ     = DVIX**2;
    DCM        = LCM - lag(LCM);
    DYTDOI     = LYTDOI - lag(LYTDOI);
    DYTDOI_Lag = lag(DYTDOI);
run;

proc autoreg data = PaperReg;
    model LSGF = LYTDOI LAGLSGF / method = ml GODFREY = 4;
    output out = resultsYTDOI p = predicted_val uclm = upper_ci lclm = lower_ci;
    title1 "Regression LSGF on LYTDOI aND LAGLSGF Variables";
run;
