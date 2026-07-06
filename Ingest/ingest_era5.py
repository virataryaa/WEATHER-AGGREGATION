"""
ERA5 — 30-day cumulative precipitation maps.
Run once daily after ECMWF ingest. ERA5 has ~5-day lag so we pull up to 5 days ago.

Regions: Brazil (South America) and West Africa.
Output filenames:
  era5_precip30d_{date}.png         -- Brazil (existing name kept)
  era5_wa_precip30d_{date}.png      -- West Africa
"""

import os
import cdsapi
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import date, timedelta, datetime

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR = os.path.join(BASE, "Database", "maps")
TMP_FILE = os.path.join(BASE, "Ingest", "era5_tmp.nc")
os.makedirs(MAPS_DIR, exist_ok=True)

ERA5_REGIONS = {
    "br": {
        "name":    "South America",
        "title":   "South America — 30-Day Cumulative Precip",
        "bbox":    {"lat_min": -56.0, "lat_max": 13.0, "lon_min": -82.0, "lon_max": -34.0},
        "figsize": (5, 6),
        "zones": {
            "Sul de Minas":        {"lat": (-22.5, -20.5), "lon": (-47.5, -44.5)},
            "Cerrado Mineiro":     {"lat": (-19.5, -17.0), "lon": (-48.5, -45.5)},
            "Chapada de Minas":    {"lat": (-17.5, -15.5), "lon": (-42.5, -40.5)},
            "Matas de Minas":      {"lat": (-21.0, -18.5), "lon": (-43.5, -41.0)},
            "Bahia":               {"lat": (-14.5, -12.0), "lon": (-42.0, -39.5)},
            "Espirito Santo":      {"lat": (-20.5, -18.5), "lon": (-41.5, -40.0)},
            "Sao Paulo":           {"lat": (-23.5, -21.5), "lon": (-49.5, -47.0)},
            "Parana":              {"lat": (-24.5, -23.0), "lon": (-52.0, -50.0)},
            "Rondonia (Robusta)":  {"lat": (-12.5, -10.5), "lon": (-64.5, -62.0)},
        },
    },
    "wa": {
        "name":    "West Africa",
        "title":   "West Africa — 30-Day Cumulative Precip",
        "bbox":    {"lat_min": 0.0, "lat_max": 12.0, "lon_min": -10.0, "lon_max": 14.0},
        "figsize": (5, 4),
        "zones": {
            "Cote d'Ivoire": {"lat": (4.5, 8.0),  "lon": (-8.0, -3.0)},
            "Ghana":         {"lat": (5.0, 9.0),   "lon": (-3.0,  1.0)},
            "Nigeria":       {"lat": (5.0, 8.0),   "lon": ( 3.0,  8.0)},
            "Cameroon":      {"lat": (3.0, 6.0),   "lon": ( 9.0, 14.0)},
        },
    },
}


def out_filename(rk, run_date):
    if rk == "br":
        return f"era5_precip30d_{run_date}.png"
    return f"era5_{rk}_precip30d_{run_date}.png"


def download_region(bbox, days=30):
    end   = date.today() - timedelta(days=5)
    start = end - timedelta(days=days - 1)

    date_list = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    years  = sorted(set(d[:4] for d in date_list))
    months = sorted(set(d[5:7] for d in date_list))
    days_l = sorted(set(d[8:] for d in date_list))

    client = cdsapi.Client(quiet=True)
    client.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "variable": "total_precipitation",
            "year": years,
            "month": months,
            "day": days_l,
            "time": ["00:00", "06:00", "12:00", "18:00"],
            "area": [bbox["lat_max"], bbox["lon_min"], bbox["lat_min"], bbox["lon_max"]],
            "data_format": "netcdf",
        },
        TMP_FILE,
    )
    return start, end


def make_map(start, end, rk, cfg, run_date):
    ds     = xr.open_dataset(TMP_FILE)
    tp     = ds["tp"] * 1000
    tp_cum = tp.sum(dim="valid_time")
    lons   = tp_cum.longitude.values
    lats   = tp_cum.latitude.values
    data   = tp_cum.values
    bbox   = cfg["bbox"]

    fig = plt.figure(figsize=cfg["figsize"], facecolor="#ffffff")
    ax  = plt.axes(projection=ccrs.PlateCarree(), facecolor="#ccdff0")
    ax.set_extent([bbox["lon_min"], bbox["lon_max"], bbox["lat_min"], bbox["lat_max"]],
                  crs=ccrs.PlateCarree())

    ax.add_feature(cfeature.LAND.with_scale("50m"),      facecolor="#f0ece4", zorder=0)
    ax.add_feature(cfeature.STATES.with_scale("50m"),    edgecolor="#b0b8c0", linewidth=0.5, zorder=1)
    ax.add_feature(cfeature.BORDERS.with_scale("50m"),   edgecolor="#7a8490", linewidth=0.9, zorder=1)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), edgecolor="#7a8490", linewidth=0.9, zorder=1)

    levels = [5, 10, 20, 40, 60, 80, 100, 150, 200, 300, 400]
    cf = ax.contourf(lons, lats, data,
                     levels=levels, cmap="YlGnBu", alpha=0.85,
                     transform=ccrs.PlateCarree(), extend="max", zorder=2)

    for zone, bounds in cfg["zones"].items():
        clat = (bounds["lat"][0] + bounds["lat"][1]) / 2
        clon = (bounds["lon"][0] + bounds["lon"][1]) / 2
        ax.text(clon, clat, zone, fontsize=5.5, color="#1a202c",
                ha="center", va="center", transform=ccrs.PlateCarree(), zorder=4,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          alpha=0.72, edgecolor="#cbd5e0", linewidth=0.4))

    cbar = plt.colorbar(cf, ax=ax, orientation="vertical", pad=0.02, shrink=0.78, aspect=28)
    cbar.set_label("mm", color="#4a5568", fontsize=8)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#4a5568", fontsize=7)

    gl = ax.gridlines(draw_labels=True, linewidth=0.25, color="#c0c8d0", alpha=0.7, linestyle="--")
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"color": "#718096", "fontsize": 6}
    gl.ylabel_style = {"color": "#718096", "fontsize": 6}

    fig.text(0.5, 0.97, cfg["title"],
             ha="center", color="#1a202c", fontsize=11, fontweight="bold")
    fig.text(0.5, 0.935, f"ERA5 Reanalysis  |  {start} to {end}",
             ha="center", color="#718096", fontsize=7.5)
    fig.text(0.5, 0.005, "Source: ERA5 / ECMWF Copernicus CDS  |  CC-BY-4.0",
             ha="center", color="#a0aec0", fontsize=6.5)

    out_path = os.path.join(MAPS_DIR, out_filename(rk, run_date))
    plt.savefig(out_path, dpi=100, bbox_inches="tight", facecolor="#ffffff")
    plt.close()
    ds.close()

    if os.path.exists(TMP_FILE):
        os.remove(TMP_FILE)

    print(f"  [{rk}] Map saved -> {os.path.basename(out_path)}")
    return out_path


def main():
    run_date = date.today().isoformat()
    print(f"\n{'='*50}")
    print(f"  ERA5 Ingest  |  {run_date}")
    print(f"{'='*50}")

    for rk, cfg in ERA5_REGIONS.items():
        print(f"\n  -- {cfg['name']} --")
        print(f"  Downloading ERA5 ({cfg['name']}) ...")
        try:
            start, end = download_region(cfg["bbox"], days=30)
            print(f"  {start} to {end} — making map ...")
            make_map(start, end, rk, cfg, run_date)
        except Exception as e:
            print(f"  [{rk}] failed: {e}")

    from run_stamp import stamp
    stamp("era5")
    print(f"\n[{datetime.now():%H:%M:%S}] Done.\n")


if __name__ == "__main__":
    main()
