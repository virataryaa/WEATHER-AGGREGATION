"""
Maxar WeatherDesk — Global Models Images
Fetches pre-rendered ECMWF forecast maps for Brazil daily.
"""

import os
import requests
from datetime import datetime, date

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR = os.path.join(BASE, "Database", "maps")
os.makedirs(MAPS_DIR, exist_ok=True)

ACCOUNT  = "2e621a7f-2b1e-4f3e-af6a-5a986a68b398"
API_URL  = f"https://api.weatherdesk.xweather.com/{ACCOUNT}/services/models/v1/main"
IMG_BASE = f"https://img.weatherdesk.xweather.com/{ACCOUNT}"

# Variables to fetch: key -> (code, preferred_duration, label)
VARIABLES = {
    "precip_7d":   ("PS",     "dr-0007", "7-Day Cumul. Precip"),
    "precip_norm": ("PPDP",   "dr-0007", "Precip % of Normal"),
    "temp_2m":     ("T2MS",   "hr-0024", "2m Temperature"),
    "temp_850":    ("T850C",  "hr-0024", "850mb Temp (Frost Signal)"),
    "dewpoint":    ("2MDEWP", "hr-0024", "Dewpoint / Wind"),
}


def fetch_image(variable_key: str, code: str, pref_duration: str, run_date: str) -> str | None:
    params = {"model": "ecm", "type": "op", "run": "00", "region": "BR", "variable": code}
    try:
        r = requests.get(API_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  [{variable_key}] API error: {e}")
        return None

    by_path = data.get("models", {}).get("byPath", {})
    if not by_path:
        print(f"  [{variable_key}] No paths returned")
        return None

    # Pick best available path: preferred duration first, then any available
    available = [p for p, v in by_path.items() if v.get("available")]
    preferred = [p for p in available if pref_duration in p]
    chosen    = (preferred or available)
    if not chosen:
        print(f"  [{variable_key}] No available images")
        return None

    # Pick the middle step for multi-step durations (most representative)
    path = chosen[len(chosen) // 2]

    img_url = IMG_BASE + path
    try:
        r = requests.get(img_url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  [{variable_key}] Image download error: {e}")
        return None

    out_path = os.path.join(MAPS_DIR, f"maxar_{variable_key}_{run_date}.png")
    with open(out_path, "wb") as f:
        f.write(r.content)

    print(f"  [{variable_key}] Saved -> {os.path.basename(out_path)}  ({len(r.content):,} bytes)")
    return out_path


def main():
    run_date = date.today().isoformat()
    print(f"\n{'='*50}")
    print(f"  Maxar Ingest  |  {run_date}")
    print(f"{'='*50}")

    for key, (code, duration, label) in VARIABLES.items():
        print(f"  Fetching {label} ...")
        fetch_image(key, code, duration, run_date)

    print(f"[{datetime.now():%H:%M:%S}] Done.\n")


if __name__ == "__main__":
    main()
