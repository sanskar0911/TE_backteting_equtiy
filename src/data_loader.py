"""
data_loader.py

Downloads historical daily OHLCV data for a set of NSE stocks using
yfinance, and saves each stock as its own CSV under data/raw/.

Run this on a machine with normal internet access:
    python src/data_loader.py

Notes:
- Tickers use the Yahoo Finance NSE suffix ".NS" (e.g. RELIANCE.NS).
- yfinance's `auto_adjust` defaults to True in recent versions, which means
  the "Close" column returned is already dividend/split-adjusted. We
  explicitly set auto_adjust=False here so raw Close and Adjusted Close are
  both available and clearly separate — this matters a lot for
  understanding corporate actions correctly (see Day 1 notes).
"""

import os
import time
import pandas as pd
import yfinance as yf

# --- Configuration -----------------------------------------------------

TICKERS = {
    "RELIANCE.NS": "RELIANCE",
    "TCS.NS": "TCS",
    "INFY.NS": "INFY",
    "HDFCBANK.NS": "HDFCBANK",
    "ICICIBANK.NS": "ICICIBANK",
}

START_DATE = "2020-01-01"
END_DATE = "2025-01-01"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def download_stock(yahoo_ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download OHLCV data for a single ticker."""
    df = yf.download(
        yahoo_ticker,
        start=start,
        end=end,
        auto_adjust=False,   # keep raw Close AND Adj Close separate
        progress=False,
    )

    if df.empty:
        raise ValueError(f"No data returned for {yahoo_ticker}. "
                          f"Check the ticker symbol and your internet connection.")

    # yfinance sometimes returns a MultiIndex column structure for a single
    # ticker depending on version — flatten it if so.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.index.name = "Date"
    return df


def download_all(tickers: dict, start: str, end: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    for yahoo_ticker, file_name in tickers.items():
        print(f"Downloading {yahoo_ticker} ...")
        try:
            df = download_stock(yahoo_ticker, start, end)
            out_path = os.path.join(output_dir, f"{file_name}.csv")
            df.to_csv(out_path)
            print(f"  Saved {len(df)} rows -> {out_path}")
        except Exception as e:
            print(f"  FAILED for {yahoo_ticker}: {e}")

        # Be polite to Yahoo's servers between requests.
        time.sleep(1)


if __name__ == "__main__":
    download_all(TICKERS, START_DATE, END_DATE, OUTPUT_DIR)
