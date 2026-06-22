"""
AIMCo Centralized Treasury Take-Home — Question 2
Build a rich/cheap signal off the Question 1 model and backtest a timing strategy
against a naive "deploy evenly" baseline.

Lookahead-bias guardrails:
  1. The Q1 model is re-estimated WALK-FORWARD (expanding window, refit monthly) --
     fair value on any given day only uses data available up to that day.
  2. The residual is converted to a z-score using a TRAILING window of past
     residuals only (no centering on the full sample).
  3. The backtest decision for day t uses the signal as of t-1's close (the
     prior trading day), so no same-day information is used to "decide" deployment.
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm

pd.set_option("display.width", 140)

FEATURES = ["vix", "sofr_effr_basis_bp", "rrp_bn", "spx_ret_21d"]
TARGET = "spread_3m_bp"          # see Q1 write-up for why 3m, not 1y
BURN_IN = 252                    # 1 year minimum history before the signal starts
REFIT_EVERY = 21                 # refit the regression ~monthly, not daily (realistic + cheap)
ZSCORE_WINDOW = 60                # trailing window for residual z-score
RICH_Z, CHEAP_Z = 1.0, -1.0      # signal thresholds

df = pd.read_csv("model_features.csv", parse_dates=["date"]).set_index("date")

# ---------------------------------------------------------------------------
# 1. Walk-forward fair value: expanding-window OLS, refit every REFIT_EVERY days
# ---------------------------------------------------------------------------

fair_value = pd.Series(index=df.index, dtype=float)
coefs_over_time = []

fit_dates = df.index[BURN_IN::REFIT_EVERY]
for i, fit_date in enumerate(fit_dates):
    train = df.loc[:fit_date].iloc[:-1]  # strictly prior data only, no same-day leak
    y_train = train[TARGET]
    X_train = sm.add_constant(train[FEATURES])
    model = sm.OLS(y_train, X_train).fit()
    coefs_over_time.append({"refit_date": fit_date, **model.params.to_dict()})

    # apply this model out-of-sample until the next refit date
    next_fit_date = fit_dates[i + 1] if i + 1 < len(fit_dates) else df.index[-1]
    apply_idx = df.index[(df.index >= fit_date) & (df.index <= next_fit_date)]
    X_apply = sm.add_constant(df.loc[apply_idx, FEATURES], has_constant="add")
    fair_value.loc[apply_idx] = model.predict(X_apply)

df["fair_value_wf"] = fair_value
df["residual_wf"] = df[TARGET] - df["fair_value_wf"]
df = df.dropna(subset=["residual_wf"])

print(f"Walk-forward signal sample: {df.index.min().date()} to {df.index.max().date()}, n={len(df)}")
print(f"Model refit {len(fit_dates)} times (every {REFIT_EVERY} trading days)")

# ---------------------------------------------------------------------------
# 2. Trailing z-score of the residual (rich/cheap relative to recent history only)
# ---------------------------------------------------------------------------

roll_mean = df["residual_wf"].rolling(ZSCORE_WINDOW, min_periods=ZSCORE_WINDOW).mean()
roll_std = df["residual_wf"].rolling(ZSCORE_WINDOW, min_periods=ZSCORE_WINDOW).std()
df["signal_z"] = (df["residual_wf"] - roll_mean) / roll_std
df = df.dropna(subset=["signal_z"])

# Decision for day t uses the signal as of t-1 (yesterday's close) -- no same-day lookahead
df["signal_z_lagged"] = df["signal_z"].shift(1)
df = df.dropna(subset=["signal_z_lagged"])

df["regime"] = np.select(
    [df["signal_z_lagged"] > RICH_Z, df["signal_z_lagged"] < CHEAP_Z],
    ["rich", "cheap"],
    default="neutral",
)

print("\nSignal regime distribution:")
print(df["regime"].value_counts())
print(f"\nBacktest sample: {df.index.min().date()} to {df.index.max().date()}, n={len(df)}")

# ---------------------------------------------------------------------------
# 3. Backtest: signal-weighted deployment vs. naive even deployment
#    Same total capital deployed either way -- this isolates the value of
#    WHEN you deploy (timing) from the value of HOW MUCH you deploy (sizing).
#    Weights are a stated assumption, not fit to the data: deploy 2x on rich
#    days, 0.3x on cheap days (mostly-but-not-fully delay), 1x neutral.
# ---------------------------------------------------------------------------

WEIGHTS = {"rich": 2.0, "neutral": 1.0, "cheap": 0.3}
df["weight"] = df["regime"].map(WEIGHTS)

# --- Pooled, whole-period headline metric ---
naive_capture_overall = df[TARGET].mean()
signal_capture_overall = np.average(df[TARGET], weights=df["weight"])
advantage_overall_bp = signal_capture_overall - naive_capture_overall

print("\n" + "=" * 70)
print("HEADLINE: pooled over full backtest period")
print(f"  Naive (deploy evenly) average captured spread:  {naive_capture_overall:.2f} bp")
print(f"  Signal-weighted average captured spread:         {signal_capture_overall:.2f} bp")
print(f"  Advantage from timing:                            {advantage_overall_bp:+.2f} bp")
print("=" * 70)

# --- Sanity check: does the signal actually separate realized spread by regime? ---
print("\nRealized spread_3m_bp by regime (validates the signal has real content):")
print(df.groupby("regime")[TARGET].agg(["mean", "count"]).round(2))

# --- Monthly hit-rate metric ---
monthly = df.groupby(pd.Grouper(freq="ME")).apply(
    lambda g: pd.Series({
        "naive": g[TARGET].mean(),
        "signal": np.average(g[TARGET], weights=g["weight"]) if g["weight"].sum() > 0 else np.nan,
        "n_days": len(g),
    }),
    include_groups=False,
)
monthly["advantage_bp"] = monthly["signal"] - monthly["naive"]
monthly["hit"] = monthly["advantage_bp"] > 0

hit_rate = monthly["hit"].mean()
cumulative_advantage = monthly["advantage_bp"].sum()
avg_monthly_advantage = monthly["advantage_bp"].mean()

print("\n" + "=" * 70)
print(f"Monthly hit rate (months where signal beat naive): {hit_rate:.1%}  ({monthly['hit'].sum()}/{len(monthly)} months)")
print(f"Average monthly advantage: {avg_monthly_advantage:+.2f} bp")
print(f"Cumulative advantage over {len(monthly)} months: {cumulative_advantage:+.1f} bp")
print("=" * 70)

monthly.to_csv("signal_monthly_backtest.csv")
df.to_csv("signal_features.csv")
