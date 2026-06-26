"""
notify.py — Weather Aggregation email summary
Usage: python notify.py <status> <git_status>
  status     : ok | error
  git_status : pushed | skipped | failed
"""

import sys
import os
import glob
import datetime
from pathlib import Path

TO_EMAIL = "virat.arya@etgworld.com"
BASE     = Path(r"C:\Users\virat.arya\ETG\SoftsDatabase - Documents\Database\Hardmine\Non Fundamental\Weather\AGGREGATION OF WEATHER")
MAPS_DIR = BASE / "Database" / "maps"
LOG_PATH = BASE / "Automator" / "run_morning.log"
DASHBOARD_URL = "https://weather-aggregation-ggz3zjxavouuk2fbkg9wjh.streamlit.app/"

status     = sys.argv[1] if len(sys.argv) > 1 else "ok"
git_status = sys.argv[2] if len(sys.argv) > 2 else "unknown"
run_dt     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
today      = datetime.date.today().strftime("%d/%m/%Y")


REGIONS = [
    ("br", "Brazil"),
    ("co", "Colombia"),
    ("vn", "Vietnam"),
    ("ca", "Central America"),
    ("wa", "West Africa"),
    ("ec", "Ecuador"),
    ("in", "India"),
    ("th", "Thailand"),
    ("au", "Australia"),
]

SOURCES = [
    ("ECMWF Open Data",         "20??-??-??_precip.png",          "9 regions x 3 params"),
    ("ECMWF OpenCharts",        "opencharts_anom_tp_w1_*.png",    "anomaly W1-4 + seasonal"),
    ("Maxar WeatherDesk",       "maxar_precip_7d_*.png",          "OP + EN, 9 regions"),
    ("Static (CPTEC/CPC/GFS)",  "static_cpc_7d_obs_*.png",        "frost + observed + GFS"),
    ("ERA5 Reanalysis",         "era5_precip30d_*.png",           "30-day cumulative"),
]


def count_maps(pattern):
    return len(glob.glob(str(MAPS_DIR / pattern)))


def latest_mtime(pattern):
    files = sorted(glob.glob(str(MAPS_DIR / pattern)))
    if not files:
        return "—"
    ts = os.path.getmtime(files[-1])
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def ingest_summary():
    total = 0
    lines = []
    for label, pat, note in SOURCES:
        n = count_maps(pat)
        mt = latest_mtime(pat)
        status_tag = "OK" if n > 0 else "NO FILES"
        # estimate total maps per source (rough)
        if "20??-??-??_precip" in pat:
            n_total = count_maps("??_20??-??-??_precip.png") + count_maps("20??-??-??_precip.png")
            n_total *= 3   # 3 params
        elif "opencharts_anom_tp_w1" in pat:
            n_total = count_maps("opencharts_*anom_tp_*.png")
            n_total += count_maps("opencharts_*anom_2t_*.png")
            n_total += count_maps("opencharts_seas_*.png") + count_maps("opencharts_enso_*.png")
        elif "maxar_precip_7d" in pat:
            n_total = count_maps("maxar_*.png")
        elif "static_cpc" in pat:
            n_total = count_maps("static_*.png")
        elif "era5" in pat:
            n_total = count_maps("era5_*.png")
        else:
            n_total = n
        total += n_total
        lines.append(
            f"  {label:<28}  {n_total:>3} maps   {mt}   {status_tag}   ({note})"
        )
    lines.append("")
    lines.append(f"  {'Total maps on disk':<28}  {count_maps('*.png'):>3} files")
    sz = sum(
        os.path.getsize(f)
        for f in glob.glob(str(MAPS_DIR / "*.png"))
    ) / (1024 * 1024)
    lines.append(f"  {'Repo / maps size':<28}  {sz:.1f} MB")
    return "\n".join(lines)


def region_status():
    lines = []
    for rk, name in REGIONS:
        pat = f"20??-??-??_precip.png" if rk == "br" else f"{rk}_20??-??-??_precip.png"
        mt = latest_mtime(pat)
        tag = "OK" if mt != "—" else "MISSING"
        lines.append(f"  {name:<20}  {tag}   last: {mt}")
    return "\n".join(lines)


def brazil_stats():
    """Pull latest MG stats from weather_mg.parquet if available."""
    try:
        import pandas as pd
        pq = BASE / "Database" / "weather_mg.parquet"
        if not pq.exists():
            return "  weather_mg.parquet not found"
        df = pd.read_parquet(pq).sort_index()
        row = df.iloc[-1]
        dt  = df.index[-1]
        lines = [
            f"  Date    : {dt.strftime('%Y-%m-%d')}",
            f"  Precip  : {row.get('precip_mm', float('nan')):.2f} mm",
            f"  T min   : {row.get('tmin_c', float('nan')):.1f} °C",
            f"  T max   : {row.get('tmax_c', float('nan')):.1f} °C",
            f"  MSLP    : {row.get('mslp_hpa', float('nan')):.1f} hPa",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"  Could not read parquet: {e}"


def send_outlook_email(subject: str, body: str):
    try:
        import win32com.client
        outlook      = win32com.client.Dispatch("Outlook.Application")
        mail         = outlook.CreateItem(0)
        mail.To      = TO_EMAIL
        mail.Subject = subject
        mail.Body    = body
        mail.Send()
        print(f"  Email sent -> {TO_EMAIL}")
    except Exception as e:
        print(f"  Email failed: {e}")


ok  = status == "ok"
tag = "OK" if ok else "ERROR"

git_line = {
    "pushed":  "GitHub    : Pushed successfully",
    "skipped": "GitHub    : No changes — push skipped",
    "failed":  "GitHub    : PUSH FAILED",
}.get(git_status, f"GitHub    : {git_status}")

subject = f"Weather Aggregation — {tag} [{today}]"

body = f"""Weather Aggregation — {tag}
Run time  : {run_dt}
Status    : {"OK" if ok else "ERROR — check run_morning.log"}
{git_line}
Dashboard : {DASHBOARD_URL}

{"=" * 60}
INGEST SUMMARY
{"=" * 60}
{ingest_summary()}
{"=" * 60}
BRAZIL — MINAS GERAIS (latest ECMWF)
{"=" * 60}
{brazil_stats()}
{"=" * 60}
REGIONS
{"=" * 60}
{region_status()}
{"=" * 60}
Log : {LOG_PATH}
"""

print(body)
send_outlook_email(subject, body)
