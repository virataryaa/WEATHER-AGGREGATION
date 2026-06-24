"""
ERA5 — 30-day cumulative precipitation map for South America.
Run once daily after ECMWF ingest. ERA5 has ~5-day lag so we pull up to 5 days ago.
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

SA = {"lat_min": -56.0, "lat_max": 13.0, "lon_min": -82.0, "lon_max": -34.0}

ZONE_LABELS = {
    "Sul de Minas":        {"lat": (-22.5, -20.5), "lon": (-47.5, -44.5)},
    "Cerrado Mineiro":     {"lat": (-19.5, -17.0), "lon": (-48.5, -45.5)},
    "Chapada de Minas":    {"lat": (-17.5, -15.5), "lon": (-42.5, -40.5)},
    "Matas de Minas":      {"lat": (-21.0, -18.5), "lon": (-43.5, -41.0)},
    "Bahia":               {"lat": (-14.5, -12.0), "lon": (-42.0, -39.5)},
    "Espirito Santo":      {"lat": (-20.5, -18.5), "lon": (-41.5, -40.0)},
    "Sao Paulo":           {"lat": (-23.5, -21.5), "lon": (-49.5, -47.0)},
    "Parana":              {"lat": (-24.5, -23.0), "lon": (-52.0, -50.0)},
    "Rondonia (Robusta)":  {"lat": (-12.5, -10.5), "lon": (-64.5, -62.0)},
}


def download(days=30):
    # ERA5 has ~5-day lag
    end   = date.today() - timedelta(days=5)
    start = end - timedelta(days=days - 1)

    date_list = [(start + timedelta(days=i)).strftime("%Y-%m-%d")
                 for i in range(days)]
    years  = sorted(set(d[:4] for d in date_list))
    months = sorted(set(d[5:7] for d in date_list))
    days_l = sorted(set(d[8:] for d in date_list))

    print(f"  ERA5: {start} to {end} ({days} days)")

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
            "area": [SA["lat_max"], SA["lon_min"], SA["lat_min"], SA["lon_max"]],
            "data_format": "netcdf",
        },
        TMP_FILE,
    )
    return start, end


def make_map(start, end):
    ds  = xr.open_dataset(TMP_FILE)
    tp  = ds["tp"] * 1000   # m -> mm

    # Sum all time steps to get cumulative over the period
    tp_cum = tp.sum(dim="valid_time")

    lons = tp_cum.longitude.values
    lats = tp_cum.latitude.values
    data = tp_cum.values

    fig = plt.figure(figsize=(5, 6), facecolor="#ffffff")
    ax  = plt.axes(projection=ccrs.PlateCarree(), facecolor="#ccdff0")
    ax.set_extent([SA["lon_min"], SA["lon_max"], SA["lat_min"], SA["lat_max"]],
                  crs=ccrs.PlateCarree())

    ax.add_feature(cfeature.LAND.with_scale("50m"),      facecolor="#f0ece4", zorder=0)
    ax.add_feature(cfeature.STATES.with_scale("50m"),    edgecolor="#b0b8c0", linewidth=0.5, zorder=1)
    ax.add_feature(cfeature.BORDERS.with_scale("50m"),   edgecolor="#7a8490", linewidth=0.9, zorder=1)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), edgecolor="#7a8490", linewidth=0.9, zorder=1)

    levels = [5, 10, 20, 40, 60, 80, 100, 150, 200, 300, 400]
    cf = ax.contourf(lons, lats, data,
                     levels=levels, cmap="YlGnBu", alpha=0.85,
                     transform=ccrs.PlateCarree(), extend="max", zorder=2)

    for zone, bounds in ZONE_LABELS.items():
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

    fig.text(0.5, 0.97, "South America — 30-Day Cumulative Precip",
             ha="center", color="#1a202c", fontsize=11, fontweight="bold")
    fig.text(0.5, 0.935, f"ERA5 Reanalysis  |  {start} to {end}",
             ha="center", color="#718096", fontsize=7.5)
    fig.text(0.5, 0.005, "Source: ERA5 / ECMWF Copernicus CDS  |  CC-BY-4.0",
             ha="center", color="#a0aec0", fontsize=6.5)

    out_path = os.path.join(MAPS_DIR, f"era5_precip30d_{date.today().isoformat()}.png")
    plt.savefig(out_path, dpi=100, bbox_inches="tight", facecolor="#ffffff")
    plt.close()
    ds.close()

    if os.path.exists(TMP_FILE):
        os.remove(TMP_FILE)

    print(f"  Map saved -> {os.path.basename(out_path)}")
    return out_path


def main():
    print(f"\n{'='*50}")
    print(f"  ERA5 Ingest  |  {date.today().isoformat()}")
    print(f"{'='*50}")
    start, end = download(days=30)
    make_map(start, end)
    print(f"[{datetime.now():%H:%M:%S}] Done.\n")


if __name__ == "__main__":
    main()
