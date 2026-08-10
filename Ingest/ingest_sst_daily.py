"""
ERA5 — daily global mean sea surface temperature, 60N-60S ocean band.
Same metric/source as Copernicus Climate Pulse and the BBC "ocean temperatures"
chart (Source: ERA5, C3S/ECMWF).

Two modes:
  python ingest_sst_daily.py           -> incremental: fill gap from last stored
                                           date up to today-6 (ERA5 daily-stats lag)
  python ingest_sst_daily.py backfill  -> full history from 1979-01-01, one CDS
                                           request per (year, month), resumable —
                                           already-covered months are skipped

CDS dataset: derived-era5-single-levels-daily-statistics
  - "daily_mean" is computed server-side, so we only ever download one grid/day
    instead of hourly fields.
  - Area is clipped to the 60N-60S band up front (same band as the BBC chart).

The day's value is an area-weighted (cos-latitude) mean over ocean grid cells
only -- land cells are NaN in the "sst" variable and are excluded automatically
by xarray's weighted().mean(skipna=True).
"""

import os
import sys
import calendar
import cdsapi
import numpy as np
import pandas as pd
import xarray as xr
from datetime import date, timedelta, datetime

BASE      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE   = os.path.join(BASE, "Database", "sst_daily.parquet")
TMP_FILE  = os.path.join(BASE, "Ingest", "sst_tmp.nc")

AREA        = [60, -180, -60, 180]   # N, W, S, E -- 60N-60S band, global
START_DATE  = date(1979, 1, 1)       # ERA5 daily-statistics coverage start
LAG_DAYS    = 6                      # dataset updates with ~6-day delay


def fetch_month(client, year, month, days):
    """One CDS request -> per-day area-weighted mean SST (degC) for the given days."""
    client.retrieve(
        "derived-era5-single-levels-daily-statistics",
        {
            "product_type":    "reanalysis",
            "variable":        "sea_surface_temperature",
            "year":            f"{year}",
            "month":           f"{month:02d}",
            "day":             [f"{d:02d}" for d in days],
            "daily_statistic": "daily_mean",
            "time_zone":       "utc+00:00",
            "frequency":       "1_hourly",
            "area":            AREA,
        },
        TMP_FILE,
    )

    ds = xr.open_dataset(TMP_FILE)
    sst = ds["sst"] - 273.15  # K -> C
    weights = np.cos(np.deg2rad(ds.latitude))
    daily_mean = sst.weighted(weights).mean(dim=["latitude", "longitude"], skipna=True)

    out = pd.DataFrame({
        "date":  pd.to_datetime(ds.valid_time.values).normalize(),
        "sst_c": np.round(daily_mean.values, 4),
    })

    ds.close()
    if os.path.exists(TMP_FILE):
        os.remove(TMP_FILE)
    return out


def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_parquet(DB_FILE)
    return pd.DataFrame(columns=["date", "sst_c"])


def save_rows(df_existing, new_rows):
    if new_rows.empty:
        return df_existing
    if df_existing.empty:
        df = new_rows
    else:
        df = pd.concat([df_existing, new_rows], ignore_index=True)
    df = df.drop_duplicates(subset="date", keep="last").sort_values("date").reset_index(drop=True)
    df.to_parquet(DB_FILE, index=False)
    return df


def backfill():
    client = cdsapi.Client(quiet=True)
    df = load_db()
    existing_dates = set(df["date"].dt.date) if not df.empty else set()

    end = date.today() - timedelta(days=LAG_DAYS)
    year, month = START_DATE.year, START_DATE.month

    while (year, month) <= (end.year, end.month):
        last_day = calendar.monthrange(year, month)[1]
        month_end = date(year, month, last_day)
        if month_end > end:
            last_day = end.day
        days_in_month = [d for d in range(1, last_day + 1)]
        month_dates = {date(year, month, d) for d in days_in_month}

        if month_dates.issubset(existing_dates):
            print(f"  [skip] {year}-{month:02d} already in database")
        else:
            print(f"  [fetch] {year}-{month:02d} ({len(days_in_month)} days)...")
            try:
                rows = fetch_month(client, year, month, days_in_month)
                df = save_rows(df, rows)
                existing_dates.update(month_dates)
                print(f"    -> saved, database now {len(df)} rows")
            except Exception as e:
                print(f"    [ERROR] {year}-{month:02d} failed: {e}")

        month += 1
        if month > 12:
            month = 1
            year += 1

    print(f"\nBackfill complete. Database: {len(df)} rows, "
          f"{df['date'].min().date()} to {df['date'].max().date()}")


def update():
    client = cdsapi.Client(quiet=True)
    df = load_db()

    if df.empty:
        print("No existing database -- run 'python ingest_sst_daily.py backfill' first.")
        return

    last_date = df["date"].max().date()
    end = date.today() - timedelta(days=LAG_DAYS)
    start = last_date + timedelta(days=1)

    if start > end:
        print(f"Up to date (latest: {last_date}, available through: {end}).")
        return

    print(f"Filling {start} to {end}...")
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        last_day = calendar.monthrange(year, month)[1]
        d0 = start.day if (year, month) == (start.year, start.month) else 1
        d1 = end.day if (year, month) == (end.year, end.month) else last_day
        days = list(range(d0, d1 + 1))

        print(f"  [fetch] {year}-{month:02d} days {d0}-{d1}...")
        rows = fetch_month(client, year, month, days)
        df = save_rows(df, rows)

        month += 1
        if month > 12:
            month = 1
            year += 1

    print(f"Database updated -> {len(df)} rows, latest: {df['date'].max().date()}")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "update"
    print(f"\n{'='*50}")
    print(f"  ERA5 Daily SST (60N-60S)  |  mode={mode}  |  {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*50}")

    if mode == "backfill":
        backfill()
    else:
        update()

    from run_stamp import stamp
    stamp("sst_daily")
    print(f"[{datetime.now():%H:%M:%S}] Done.\n")


if __name__ == "__main__":
    main()
