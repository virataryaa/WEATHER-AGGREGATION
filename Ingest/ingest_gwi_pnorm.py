"""
GWI Station Data -- Day 1-15 % of Normal Precipitation.

Maxar's ensemble *image* API (ingest_maxar.py) never publishes a combined
1-15 day frame for PPDP (% of Normal) -- only PS (raw mm) gets a dr-0015
frame. The GWI Station Table/Map API has no such gap: PRCP_DEP with
grouping=T aggregates any custom start/end window (including forecast
days) into a single map, so a genuine day1-15 % of Normal chart can be
built directly from it.

Output filenames:
  gwi_pnorm_{region}_ecm_day1-15_{date}.png   -- ECM Ensemble (model=4)
  gwi_pnorm_{region}_gfs_day1-15_{date}.png   -- GFS Ensemble (model=2)
"""

import os
import requests
from datetime import date, timedelta

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR = os.path.join(BASE, "Database", "maps")
os.makedirs(MAPS_DIR, exist_ok=True)

ACCOUNT = "2e621a7f-2b1e-4f3e-af6a-5a986a68b398"
API_URL = f"https://api.weatherdesk.xweather.com/{ACCOUNT}/services/gwi/v1/getimage"

# region_key -> (GWI region id, display name)
REGIONS = {
    "br": (4,  "Brazil"),
    "wa": (25, "West Africa"),
    "vn": (22, "Vietnam / Thailand"),
    "co": (23, "Colombia / Venezuela"),
    "ca": (33, "Central America"),
    "ec": (23, "Ecuador (Colombia/Venezuela map)"),
    "in": (15, "India"),
    "th": (22, "Thailand (Vietnam/Thailand map)"),
    "au": (2,  "Australia"),
}

# model_key -> GWI model id
MODELS = {
    "ecm": 4,   # ECM Ensemble
    "gfs": 2,   # GFS Ensemble
}


def fetch_map(region_id, model_id, start, end):
    params = {
        "type": "station",
        "metric": 0,
        "region": region_id,
        "model": model_id,
        "parameter": "PRCP_DEP",
        "grouping": "T",
        "start": start,
        "end": end,
        "colorscale": 1,
    }
    r = requests.get(API_URL, params=params, timeout=25)
    r.raise_for_status()
    resource = r.json().get("outputs", {}).get("resource")
    if not resource:
        raise ValueError("no resource in response")
    img = requests.get(resource, timeout=20)
    img.raise_for_status()
    return img.content


def main():
    run_date = date.today().isoformat()
    start = run_date
    end   = (date.today() + timedelta(days=14)).isoformat()

    print(f"\n{'='*55}")
    print(f"  GWI Day 1-15 % of Normal Precip  |  {run_date}")
    print(f"{'='*55}")

    for region_key, (region_id, label) in REGIONS.items():
        print(f"\n  [{label}]")
        for model_key, model_id in MODELS.items():
            out = os.path.join(MAPS_DIR, f"gwi_pnorm_{region_key}_{model_key}_day1-15_{run_date}.png")
            print(f"  {model_key} ...", end=" ", flush=True)
            try:
                content = fetch_map(region_id, model_id, start, end)
                with open(out, "wb") as f:
                    f.write(content)
                print(f"ok  ({len(content):,} B)")
            except Exception as e:
                print(f"skipped ({e})")

    from run_stamp import stamp
    stamp("gwi_pnorm")
    print(f"\n{'='*55}")
    print(f"  Done.\n")


if __name__ == "__main__":
    main()
