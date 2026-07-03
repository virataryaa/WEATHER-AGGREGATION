"""
Static chart ingest -- CPTEC Geadas (frost), CPC/NOAA observed, GFS week 1/2, TropicalTidbits GEFS.
Converts GIFs to PNG. Saves to Database/maps/.

Output filenames:
  static_geada_d{1-3}_{date}.png          -- CPTEC frost Day 1/2/3
  static_cpc_7d_obs_{date}.png            -- CPC 7-day observed precip (S. America)
  static_cpc_7d_anom_{date}.png           -- CPC 7-day precip anomaly
  static_cpc_30d_pnorm_{date}.png         -- CPC 30-day % of normal
  static_gfs_w1_{date}.png               -- GFS week 1 total precip
  static_gfs_w2_{date}.png               -- GFS week 2 total precip
  static_gefs_anom_d7_{date}.png          -- GEFS precip anomaly days 1-7
  static_gefs_anom_d14_{date}.png         -- GEFS precip anomaly days 8-14
"""

import io
import os
import re
import requests
from datetime import date, datetime, timedelta, timezone
from PIL import Image

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR = os.path.join(BASE, "Database", "maps")
os.makedirs(MAPS_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
}

TT_HEADERS = {
    **HEADERS,
    "Referer": "https://www.tropicaltidbits.com/analysis/models/",
}

CPC_BASE  = "https://www.cpc.ncep.noaa.gov/products/international"
CRNG_BASE = "https://ftp.cptec.inpe.br/modelos/tempo/CRNG/GEADA"

STATIC_SOURCES = [
    # CPTEC frost forecasts (Geadas) -- most tradeable signal for KC
    {"key": "geada_d1",      "url": f"{CRNG_BASE}/indice1.gif"},
    {"key": "geada_d2",      "url": f"{CRNG_BASE}/indice2.gif"},
    {"key": "geada_d3",      "url": f"{CRNG_BASE}/indice3.gif"},
    # CPC observed (gauge-based)
    {"key": "cpc_7d_obs",    "url": f"{CPC_BASE}/cpcuni_gauge/cpcuni_gauge_7day_sam_obs.gif"},
    {"key": "cpc_7d_anom",   "url": f"{CPC_BASE}/cpcuni_gauge/cpcuni_gauge_7day_sam_anom.gif"},
    {"key": "cpc_7d_pnorm",  "url": f"{CPC_BASE}/cpcuni_gauge/cpcuni_gauge_7day_sam_pnorm.gif"},
    {"key": "cpc_30d_pnorm", "url": f"{CPC_BASE}/cpcuni_gauge/cpcuni_gauge_30day_sam_pnorm.gif"},
    # GFS model
    {"key": "gfs_w1",        "url": f"{CPC_BASE}/cpci/data/00/gfs.t00z.totp.week1.samerica.gif"},
    {"key": "gfs_w2",        "url": f"{CPC_BASE}/cpci/data/00/gfs.t00z.totp.week2.samerica.gif"},
]


def download_as_png(url, hdrs=None, max_width: int = 1000):
    r = requests.get(url, headers=hdrs or HEADERS, timeout=20)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("RGB")
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True, compress_level=7)
    return buf.getvalue()


def tt_runtime():
    now  = datetime.now(timezone.utc)
    d    = now.date() if now.hour >= 6 else (now - timedelta(days=1)).date()
    return d.strftime("%Y%m%d") + "00"


def fetch_tt_image(model, region, pkg, fh):
    runtime  = tt_runtime()
    page_url = (
        f"https://www.tropicaltidbits.com/analysis/models/"
        f"?model={model}&region={region}&pkg={pkg}&runtime={runtime}&fh={fh}"
    )
    r = requests.get(page_url, headers=TT_HEADERS, timeout=15)
    r.raise_for_status()
    m = re.search(r'og:image["\s]+content="([^"]+\.png)"', r.text)
    if not m:
        raise ValueError(f"og:image not found for fh={fh}")
    img_url = m.group(1)
    return download_as_png(img_url, TT_HEADERS)


def main():
    run_date = date.today().isoformat()
    print(f"\n{'='*55}")
    print(f"  Static Charts Ingest  |  {run_date}")
    print(f"{'='*55}")

    # CPTEC + CPC + GFS
    for src in STATIC_SOURCES:
        key = src["key"]
        out = os.path.join(MAPS_DIR, f"static_{key}_{run_date}.png")
        print(f"  {key} ...", end=" ", flush=True)
        try:
            data = download_as_png(src["url"])
            with open(out, "wb") as f:
                f.write(data)
            print(f"ok  ({len(data)//1024} KB)")
        except Exception as e:
            print(f"skipped ({e})")

    # TropicalTidbits GEFS anomaly
    tt_charts = [
        ("gefs_anom_d7",  168),
        ("gefs_anom_d14", 344),
    ]
    for key, fh in tt_charts:
        out = os.path.join(MAPS_DIR, f"static_{key}_{run_date}.png")
        print(f"  {key} (TropicalTidbits fh={fh}) ...", end=" ", flush=True)
        try:
            data = fetch_tt_image("gfs-ens", "samer", "apcpna", fh)
            with open(out, "wb") as f:
                f.write(data)
            print(f"ok  ({len(data)//1024} KB)")
        except Exception as e:
            print(f"skipped ({e})")

    from run_stamp import stamp
    stamp("static")
    print(f"\n{'='*55}")
    print(f"  Done.\n")


if __name__ == "__main__":
    main()
