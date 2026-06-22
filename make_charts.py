"""Generate the charts used in the Question 1 summary report."""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("model_features.csv", parse_dates=["date"]).set_index("date")
feature_cols = ["vix", "sofr_effr_basis_bp", "rrp_bn", "spx_ret_21d"]

y = df["spread_3m_bp"]
X = sm.add_constant(df[feature_cols])
model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
df["fitted_3m"] = model.predict(X)
df["residual_3m"] = df["spread_3m_bp"] - df["fitted_3m"]

X_std = (df[feature_cols] - df[feature_cols].mean()) / df[feature_cols].std()
y_std = (y - y.mean()) / y.std()
model_std = sm.OLS(y_std, sm.add_constant(X_std)).fit()
importance = model_std.params.drop("const").sort_values(key=abs)

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

# Chart 1: spread vs VIX over time (dual axis)
fig, ax1 = plt.subplots(figsize=(9, 4))
ax1.plot(df.index, df["spread_3m_bp"], color="#1f4e79", label="3m financing spread (bp)")
ax1.plot(df.index, df["spread_1y_bp"], color="#1f4e79", alpha=0.4, label="1y financing spread (bp)")
ax1.set_ylabel("Spread over SOFR (bp)", color="#1f4e79")
ax1.tick_params(axis="y", labelcolor="#1f4e79")
ax2 = ax1.twinx()
ax2.plot(df.index, df["vix"], color="#c00000", alpha=0.6, label="VIX")
ax2.set_ylabel("VIX", color="#c00000")
ax2.tick_params(axis="y", labelcolor="#c00000")
ax1.set_title("Equity financing spread vs. VIX, 2020–2025")
ax1.xaxis.set_major_locator(mdates.YearLocator())
fig.tight_layout()
fig.savefig("charts/01_spread_vs_vix.png", dpi=150)
plt.close(fig)

# Chart 2: standardized coefficients (feature importance)
fig, ax = plt.subplots(figsize=(7, 3.5))
colors = ["#c00000" if v < 0 else "#1f7a3d" for v in importance.values]
ax.barh(importance.index, importance.values, color=colors)
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("Standardized coefficient (std-devs of spread per 1-std move in feature)")
ax.set_title("What drives the 3m financing spread — standardized importance")
fig.tight_layout()
fig.savefig("charts/02_feature_importance.png", dpi=150)
plt.close(fig)

# Chart 3: actual vs fitted, with residual panel
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5.5), sharex=True, height_ratios=[2, 1])
ax1.plot(df.index, df["spread_3m_bp"], label="Actual", color="#1f4e79")
ax1.plot(df.index, df["fitted_3m"], label="Model fair value", color="#c00000", linestyle="--", linewidth=1)
ax1.legend(loc="upper left")
ax1.set_ylabel("3m spread (bp)")
ax1.set_title("Actual vs. model-implied fair value, with residual")
ax2.fill_between(df.index, df["residual_3m"], 0, color="#7f7f7f", alpha=0.6)
last = df.index[-1]
ax2.scatter([last], [df["residual_3m"].iloc[-1]], color="#c00000", zorder=5)
ax2.annotate(f"{df['residual_3m'].iloc[-1]:+.0f}bp\n(latest)", (last, df["residual_3m"].iloc[-1]),
             textcoords="offset points", xytext=(-60, -10), color="#c00000", fontsize=9)
ax2.axhline(0, color="black", linewidth=0.8)
ax2.set_ylabel("Residual (bp)\nactual − fair value")
ax2.xaxis.set_major_locator(mdates.YearLocator())
fig.tight_layout()
fig.savefig("charts/03_actual_vs_fitted.png", dpi=150)
plt.close(fig)

print("Charts written to charts/")
print(model.summary())
