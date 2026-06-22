"""
AIMCo Centralized Treasury Take-Home — Question 1
Build a regression explaining the daily S&P 500 equity financing spread over SOFR.
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm

pd.set_option("display.width", 140)

# ---------------------------------------------------------------------------
# 1. Load target data
# ---------------------------------------------------------------------------

spreads = pd.read_csv("financing_spreads.csv", parse_dates=["date"]).set_index("date")

# ---------------------------------------------------------------------------
# 2. Load cached FRED raw series, align to spreads' trading-day calendar
# ---------------------------------------------------------------------------

raw = pd.read_csv("fred_raw.csv", parse_dates=["date"]).set_index("date")
raw = raw.reindex(spreads.index.union(raw.index)).sort_index()
raw = raw.ffill(limit=5)          # carry last published value forward (weekends/holidays/weekly TGA-style gaps)
raw = raw.reindex(spreads.index)  # snap back to the exact trading days in our target

# ---------------------------------------------------------------------------
# 3. Engineer features
# ---------------------------------------------------------------------------

feat = pd.DataFrame(index=spreads.index)
feat["vix"] = raw["VIXCLS"]
feat["sofr_effr_basis_bp"] = (raw["SOFR"] - raw["DFF"]) * 100  # bp, sign: SOFR rich to EFFR = positive
feat["rrp_bn"] = raw["RRPONTSYD"]
feat["curve_slope_10y3m"] = raw["T10Y3M"]

spx_log_ret = np.log(raw["SP500"]).diff()
feat["spx_ret_21d"] = raw["SP500"].pct_change(21)
feat["spx_rvol_21d"] = spx_log_ret.rolling(21).std() * np.sqrt(252) * 100  # annualized, in vol points

df = pd.concat([spreads, feat], axis=1).dropna()
print(f"Modeling sample: {df.index.min().date()} to {df.index.max().date()}, n={len(df)}")

df.to_csv("model_features.csv")

# ---------------------------------------------------------------------------
# 4. Multicollinearity check
# ---------------------------------------------------------------------------

feature_cols = ["vix", "sofr_effr_basis_bp", "rrp_bn", "curve_slope_10y3m", "spx_ret_21d", "spx_rvol_21d"]
print("\nFeature correlation matrix:")
print(df[feature_cols].corr().round(2))

from statsmodels.stats.outliers_influence import variance_inflation_factor
X_vif = sm.add_constant(df[feature_cols])
vif = pd.Series(
    [variance_inflation_factor(X_vif.values, i) for i in range(1, X_vif.shape[1])],
    index=feature_cols,
)
print("\nVIF (>5 suggests problematic collinearity):")
print(vif.round(2))

# ---------------------------------------------------------------------------
# 5. OLS regression — spread_3m_bp
#    curve_slope_10y3m and spx_rvol_21d dropped: both insignificant (p=0.37, p=0.41)
#    in the full model and spx_rvol_21d duplicates vix (corr 0.82, VIF 3-4).
#    Dropping them costs 0.003 of R^2 (0.460 -> 0.457) -- they weren't pulling weight.
# ---------------------------------------------------------------------------

feature_cols = ["vix", "sofr_effr_basis_bp", "rrp_bn", "spx_ret_21d"]

y = df["spread_3m_bp"]
X = sm.add_constant(df[feature_cols])
model_3m = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})  # Newey-West SE: spread is autocorrelated daily

print("\n" + "=" * 70)
print("OLS: spread_3m_bp ~ features  (Newey-West HAC standard errors, 5 lags)")
print("=" * 70)
print(model_3m.summary())

# Standardized coefficients for fair importance ranking (units differ wildly: vix ~15-30, rrp ~ $bn, etc.)
X_std = (df[feature_cols] - df[feature_cols].mean()) / df[feature_cols].std()
y_std = (y - y.mean()) / y.std()
model_3m_std = sm.OLS(y_std, sm.add_constant(X_std)).fit()
print("\nStandardized coefficients (impact per 1-std move in each feature, in std-devs of spread):")
print(model_3m_std.params.drop("const").sort_values(key=abs, ascending=False).round(3))

# ---------------------------------------------------------------------------
# 5b. Robustness check: first-difference (day-over-day change) specification.
#    Levels regression has DW=0.10 -- residuals are extremely autocorrelated,
#    i.e. both Y and several X's are persistent/trending series. Two persistent
#    series can show a strong spurious relationship in levels even with no real
#    daily link (Granger-Newbold). Re-running on changes is the standard fix
#    and tells us which relationships are a real day-to-day link vs. just
#    slow co-trending over multi-month regimes.
# ---------------------------------------------------------------------------

dY = df["spread_3m_bp"].diff()
dX = sm.add_constant(df[feature_cols].diff())
model_diff = sm.OLS(dY, dX, missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": 5})

print("\n" + "=" * 70)
print("ROBUSTNESS CHECK: first-difference spec (day-over-day changes)")
print("=" * 70)
print(model_diff.params.round(3))
print("R2:", round(model_diff.rsquared, 3))
print("p-values:", model_diff.pvalues.round(4).to_dict())
print("Durbin-Watson on diff residuals:", round(sm.stats.durbin_watson(model_diff.resid), 3))

# ---------------------------------------------------------------------------
# 6. OLS regression — spread_1y_bp (secondary check)
# ---------------------------------------------------------------------------

y1y = df["spread_1y_bp"]
model_1y = sm.OLS(y1y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
print("\n" + "=" * 70)
print("OLS: spread_1y_bp ~ features  (for comparison)")
print("=" * 70)
print(model_1y.summary())

# ---------------------------------------------------------------------------
# 7. Current expected financing cost (latest available row)
# ---------------------------------------------------------------------------

latest_date = df.index.max()
latest_X = X.loc[[latest_date]]
pred_3m = model_3m.predict(latest_X).iloc[0]
pred_1y = model_1y.predict(latest_X).iloc[0]
actual_3m = df.loc[latest_date, "spread_3m_bp"]
actual_1y = df.loc[latest_date, "spread_1y_bp"]

print("\n" + "=" * 70)
print(f"Latest date in sample: {latest_date.date()}")
print(f"  Actual  spread_3m_bp: {actual_3m:.1f}   |  Model-implied fair value: {pred_3m:.1f}   |  Residual: {actual_3m - pred_3m:+.1f} bp")
print(f"  Actual  spread_1y_bp: {actual_1y:.1f}   |  Model-implied fair value: {pred_1y:.1f}   |  Residual: {actual_1y - pred_1y:+.1f} bp")
print("=" * 70)
