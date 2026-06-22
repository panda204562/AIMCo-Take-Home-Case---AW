# AIMCo Centralized Treasury — Take-Home Technical Assessment

Analysis of the S&P 500 equity financing spread over SOFR: what drives it (Question 1) and a deployment-timing trading signal built from that model (Question 2).

## Deliverables

- `Q1_Financing_Spread_Drivers.pdf` — Question 1 write-up: regression model, findings, robustness checks, data sources considered.
- `Q2_Trading_Signal_Backtest.pdf` — Question 2 write-up: walk-forward signal, backtest vs. naive baseline, limitations.
- PowerPoint summary deck covering both questions (added separately).

## Pipeline (reproducible end-to-end)

Run in order from this folder:

```
python fetch_data.py          # pulls VIX/SOFR/EFFR/RRP/curve/SPX from FRED
python build_model.py         # Q1: feature engineering, OLS regression, robustness checks
python make_charts.py         # Q1 charts
python make_report.py         # Q1 PDF
python build_signal.py        # Q2: walk-forward signal + backtest
python make_signal_charts.py  # Q2 charts
python make_q2_report.py      # Q2 PDF
```

Requires: `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `matplotlib`, `reportlab`.

## Data

`financing_spreads.csv` — provided dataset (daily S&P 500 equity financing spread over SOFR, 2020–2025).
All other features are pulled live from FRED (no API key required) in `fetch_data.py`.
