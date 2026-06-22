"""
Step 1 of the pipeline: pull the public macro/vol features from FRED.
No API key required -- FRED serves plain CSV at this endpoint for any series ID.
Run this once (or whenever you want fresher data) before build_model.py.
"""

import pandas as pd

SERIES = ["SOFR", "DFF", "VIXCLS", "RRPONTSYD", "T10Y3M", "SP500"]


def fetch_fred(series_id):
    df = pd.read_csv(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}")
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")[series_id]


if __name__ == "__main__":
    raw = pd.concat([fetch_fred(s) for s in SERIES], axis=1, sort=True)
    raw.to_csv("fred_raw.csv")
    print(f"Pulled {len(SERIES)} series, {len(raw)} rows, {raw.index.min().date()} to {raw.index.max().date()}")
    print("Saved to fred_raw.csv")
