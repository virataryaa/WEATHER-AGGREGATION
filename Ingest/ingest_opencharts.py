"""
ECMWF OpenCharts API -- pre-rendered forecast/anomaly/seasonal maps.
Free public API, no auth required. Saves PNGs to Database/maps/.

Products fetched:
  - extended-anomaly-tp    : weekly precip anomaly (4 weeks)  -> opencharts_anom_tp_w{1-4}_{date}.png
  - extended-anomaly-2t    : weekly temp anomaly (4 weeks)    -> opencharts_anom_2t_w{1-4}_{date}.png
  - seasonal SEAS5 rain    : monthly total (4 months)         -> opencharts_seas_m{1-4}_{date}.png
  - seasonal ENSO plumes   : Nino 3.4 outlook                 -> opencharts_enso_{date}.png
"""

import io
import os
import re
import time
import requests
from datetime import date
from PIL import Image


def _crop_copyright(img: Image.Image) -> Image.Image:
    """Remove the bottom copyright/logo strip by finding the white gap above it."""
    import numpy as np
    arr = np.array(img)
    h = arr.shape[0]
    # A row is "white" if its average pixel value > 245
    row_is_white = arr.mean(axis=(1, 2)) > 245
    # Scan from bottom upward: skip the copyright content, then find white gap above it
    crop_y = h
    found_content = False
    for i in range(h - 1, h // 2, -1):
        if not row_is_white[i]:
            found_content = True
        elif found_content:
            # First white row above the bottom content block = top of the gap
            crop_y = i
            break
    return img.crop((0, 0, img.width, crop_y))


def save_compressed(data: bytes, out_path: str, max_width: int = 900):
    img = Image.open(io.BytesIO(data)).convert("RGB")
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    img = _crop_copyright(img)
    img.save(out_path, "PNG", optimize=True, compress_level=7)

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR = os.path.join(BASE, "Database", "maps")
os.makedirs(MAPS_DIR, exist_ok=True)

API_BASE = "https://charts.ecmwf.int/opencharts-api/v1/products"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Referer": "https://charts.ecmwf.int/",
}

SEASONAL_STEPS = [744, 1488, 2208, 2952]


def discover_first_step(product, projection=None, extra_params=None):
    params = {}
    if projection:
        params["projection"] = projection
    if extra_params:
        params.update(extra_params)
    r = requests.get(f"{API_BASE}/{product}/", params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    description = r.json()["data"]["attributes"]["description"]
    m = re.search(r"\(\+(\d+)h\)", description)
    if not m:
        raise ValueError(f"Cannot parse step from description: {description!r}")
    return int(m.group(1))


def fetch_image_bytes(product, step, projection=None, extra_params=None):
    params = {"step": step}
    if projection:
        params["projection"] = projection
    if extra_params:
        params.update(extra_params)
    for attempt in range(3):
        r = requests.get(f"{API_BASE}/{product}/", params=params, headers=HEADERS, timeout=15)
        if r.status_code != 403:
            break
        time.sleep(8 * (attempt + 1))
    r.raise_for_status()
    data      = r.json()["data"]
    image_url = data["link"]["href"]
    img = requests.get(image_url, headers=HEADERS, timeout=30)
    img.raise_for_status()
    return img.content


def fetch_weekly_anomaly(product, key, run_date):
    """Fetch 4 weekly anomaly steps (W1-W4)."""
    print(f"\n  {key.upper()} weekly anomaly ...")
    try:
        first_step = discover_first_step(product, projection="opencharts_south_america")
    except Exception as e:
        print(f"    Step discovery failed: {e}")
        return
    saved = 0
    for i in range(4):
        step = first_step + i * 168
        label = f"w{i+1}"
        out   = os.path.join(MAPS_DIR, f"opencharts_anom_{key}_{label}_{run_date}.png")
        print(f"    +{step}h ({label}) ...", end=" ", flush=True)
        try:
            data = fetch_image_bytes(product, step, projection="opencharts_south_america")
            save_compressed(data, out)
            print(f"ok  ({os.path.getsize(out)//1024} KB)")
            saved += 1
        except Exception as e:
            print(f"skipped ({e})")
        time.sleep(1)
    print(f"    Saved {saved}/4")


def fetch_seasonal_rain(run_date):
    """Fetch SEAS5 seasonal rainfall for months 1-4."""
    product = "seasonal_system5_standard_rain"
    extra   = {"area": "SAME", "stats": "tsum"}
    print(f"\n  SEAS5 seasonal rain ...")
    saved = 0
    for i, step in enumerate(SEASONAL_STEPS, 1):
        label = f"m{i}"
        out   = os.path.join(MAPS_DIR, f"opencharts_seas_{label}_{run_date}.png")
        print(f"    step={step} ({label}) ...", end=" ", flush=True)
        try:
            data = fetch_image_bytes(product, step, extra_params=extra)
            save_compressed(data, out)
            print(f"ok  ({os.path.getsize(out)//1024} KB)")
            saved += 1
        except Exception as e:
            print(f"skipped ({e})")
        time.sleep(1)
    print(f"    Saved {saved}/4")


def fetch_enso_plumes(run_date):
    """Fetch ENSO Nino 3.4 plumes chart."""
    product = "seasonal_system5_nino_plumes"
    extra   = {"nino_area": "NINO3-4"}
    out     = os.path.join(MAPS_DIR, f"opencharts_enso_{run_date}.png")
    print(f"\n  ENSO Nino 3.4 plumes ...", end=" ", flush=True)
    try:
        data = fetch_image_bytes(product, step=0, extra_params=extra)
        save_compressed(data, out)
        print(f"ok  ({os.path.getsize(out)//1024} KB)")
    except Exception as e:
        print(f"skipped ({e})")


# Extra regions: (region_key, projection, label)
REGION_PROJECTIONS = [
    ("wa", "opencharts_africa",         "West Africa"),
    ("vn", "opencharts_tropics",        "Vietnam / SE Asia"),
    ("co", "opencharts_south_america",  "Colombia"),
    ("ca", "opencharts_north_america",  "Central America"),
    ("ec", "opencharts_south_america",  "Ecuador"),
    ("in", "opencharts_south_asia",     "India"),
    ("th", "opencharts_tropics",        "Thailand"),
    ("au", "opencharts_australasia",    "Australia"),
]


def fetch_weekly_anomaly_region(product, key, region_key, projection, run_date):
    print(f"\n  [{region_key}] {key.upper()} weekly anomaly ({projection}) ...")
    try:
        first_step = discover_first_step(product, projection=projection)
    except Exception as e:
        print(f"    Step discovery failed: {e}")
        return
    saved = 0
    for i in range(4):
        step  = first_step + i * 168
        label = f"w{i+1}"
        out   = os.path.join(MAPS_DIR, f"opencharts_{region_key}_anom_{key}_{label}_{run_date}.png")
        print(f"    +{step}h ({label}) ...", end=" ", flush=True)
        try:
            data = fetch_image_bytes(product, step, projection=projection)
            save_compressed(data, out)
            print(f"ok  ({os.path.getsize(out)//1024} KB)")
            saved += 1
        except Exception as e:
            print(f"skipped ({e})")
        time.sleep(1)
    print(f"    Saved {saved}/4")


def main():
    run_date = date.today().isoformat()
    print(f"\n{'='*55}")
    print(f"  ECMWF OpenCharts Ingest  |  {run_date}")
    print(f"{'='*55}")

    # Brazil
    fetch_weekly_anomaly("extended-anomaly-tp", "tp", run_date)
    fetch_weekly_anomaly("extended-anomaly-2t", "2t", run_date)
    fetch_seasonal_rain(run_date)
    fetch_enso_plumes(run_date)

    # Extra regions
    for region_key, projection, label in REGION_PROJECTIONS:
        print(f"\n  -- {label} --")
        fetch_weekly_anomaly_region("extended-anomaly-tp", "tp", region_key, projection, run_date)
        fetch_weekly_anomaly_region("extended-anomaly-2t", "2t", region_key, projection, run_date)

    from run_stamp import stamp
    stamp("opencharts")
    print(f"\n{'='*55}")
    print(f"  Done.\n")


if __name__ == "__main__":
    main()
