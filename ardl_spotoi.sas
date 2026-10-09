/* =========================================================
   ARDL(1,1) Regression: LSGF on LOI (Spot-OI) and LAGLSGF
   (Spot-OI alternative specification, compared against the
   YTDOI-preferred model in ardl_ytdoi.sas; Delta-AIC ~ 0.4
   favouring YTDOI)
   Verified against SAS output (PROC AUTOREG), N = 26,
   Mar-2020 to Jun-2026, corrected SGF data:
     LOI coefficient      = 0.0734  (p = 0.0301)
     LAGLSGF coefficient  = 0.9250  (p < .0001)
     R-square             = 0.9886
     AIC                  = -69.618
     Godfrey LM (lags 1-4): all p > 0.37 -> no residual
       autocorrelation.
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
    model LSGF = LOI LAGLSGF / method = ml GODFREY = 4;
    output out = resultsSpotOI p = predicted_val uclm = upper_ci lclm = lower_ci;
    title1 "Regression LSGF on Lag Values of SGF and LOI";
run;
