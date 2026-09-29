/* =========================================================
   ARDL(1,1) Regression: LSGF on LOI (Spot-OI) and LAGLSGF
   (Spot-OI alternative specification, compared against the
   YTDOI-preferred model in ardl_ytdoi.sas; paper reports
   Delta-AIC ~ 0.3 favoring YTDOI)
   Verified exact match against SAS output (PROC AUTOREG):
     LOI coefficient      = 0.0839  (p = 0.0392)
     LAGLSGF coefficient  = 0.9080  (p < .0001)
     R-square             = 0.9837
     AIC                  = -60.592
     Godfrey LM (lags 1-4): all p > 0.39 -> no residual
       autocorrelation.
   Delta-AIC vs YTDOI model = -60.887 - (-60.592) = -0.295,
   i.e. ~0.3 AIC points in favor of the YTDOI specification,
   matching the paper's reported comparison.
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
