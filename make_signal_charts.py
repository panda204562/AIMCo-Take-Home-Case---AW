"""Generate the charts used in the Question 2 signal/backtest report."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("signal_features.csv", parse_dates=["date"]).set_index("date")
monthly = pd.read_csv("signal_monthly_backtest.csv", index_col=0, parse_dates=True)

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

# Chart 1: signal z-score over time with rich/cheap bands, spread overlaid
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5.5), sharex=True, height_ratios=[1, 1])
ax1.plot(df.index, df["spread_3m_bp"], color="#1f4e79", linewidth=1)
ax1.set_ylabel("3m spread (bp)")
ax1.set_title("Signal regime vs. realized spread")
colors = {"rich": "#1f7a3d", "cheap": "#c00000", "neutral": "#cccccc"}
for regime, c in colors.items():
    mask = df["regime"] == regime
    ax2.scatter(df.index[mask], df["signal_z_lagged"][mask], s=4, color=c, label=regime)
ax2.axhline(1.0, color="#1f7a3d", linestyle="--", linewidth=0.8)
ax2.axhline(-1.0, color="#c00000", linestyle="--", linewidth=0.8)
ax2.axhline(0, color="black", linewidth=0.6)
ax2.set_ylabel("Signal z-score\n(lagged 1 day)")
ax2.legend(loc="upper left", fontsize=8, markerscale=2)
ax2.xaxis.set_major_locator(mdates.YearLocator())
fig.tight_layout()
fig.savefig("charts/04_signal_regime.png", dpi=150)
plt.close(fig)

# Chart 2: realized spread by regime (validates signal content)
fig, ax = plt.subplots(figsize=(6, 3.5))
order = ["cheap", "neutral", "rich"]
means = df.groupby("regime")[ "spread_3m_bp"].mean().loc[order]
counts = df.groupby("regime")["spread_3m_bp"].count().loc[order]
bars = ax.bar(order, means.values, color=[colors[r] for r in order])
for i, (m, n) in enumerate(zip(means.values, counts.values)):
    ax.text(i, m + 1, f"{m:.1f}bp\n(n={n})", ha="center", fontsize=8.5)
ax.set_ylim(0, means.max() * 1.25)
ax.set_ylabel("Average realized 3m spread (bp)")
ax.set_title("Realized spread by signal regime — out-of-sample")
fig.tight_layout()
fig.savefig("charts/05_realized_by_regime.png", dpi=150)
plt.close(fig)

# Chart 3: cumulative advantage over time (is the edge steady or lumpy?)
fig, ax = plt.subplots(figsize=(9, 3.8))
cum = monthly["advantage_bp"].cumsum()
ax.plot(cum.index, cum.values, color="#1f4e79", linewidth=1.5)
ax.fill_between(cum.index, cum.values, 0, color="#1f4e79", alpha=0.15)
ax.axhline(0, color="black", linewidth=0.6)
ax.set_ylabel("Cumulative advantage (bp)")
ax.set_title("Cumulative advantage of signal-weighted vs. naive even deployment")
ax.xaxis.set_major_locator(mdates.YearLocator())
fig.tight_layout()
fig.savefig("charts/06_cumulative_advantage.png", dpi=150)
plt.close(fig)

print("Signal charts written to charts/")
print("\nMonths with negative advantage (signal underperformed naive):")
print(monthly[monthly["advantage_bp"] < 0][["naive", "signal", "advantage_bp"]].round(2))
