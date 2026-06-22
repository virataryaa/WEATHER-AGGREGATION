import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
from ecmwf.opendata import Client
from datetime import date, datetime

warnings.filterwarnings("ignore")

BASE      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRIB_FILE = os.path.join(BASE, "Ingest", "today.grib")
DB_FILE   = os.path.join(BASE, "Database", "weather_mg.parquet")
MAPS_DIR  = os.path.join(BASE, "Database", "maps")
os.makedirs(MAPS_DIR, exist_ok=True)

# Minas Gerais bbox — for statistics only
MG = {"lat_min": -22.9, "lat_max": -14.2, "lon_min": -51.0, "lon_max": -39.8}

# South America bbox — for map display
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

MAP_CONFIGS = {
    "precip": {
        "label":   "Precipitation (12-24h)",
        "unit":    "mm",
        "cmap":    "YlGnBu",
        "levels":  [0.5, 1, 2, 5, 10, 15, 20, 30, 50, 75, 100],
        "extend":  "max",
    },
    "tmin": {
        "label":   "Min Temperature (0-24h)",
        "unit":    "degC",
        "cmap":    "RdYlBu_r",
        "levels":  [-5, 0, 5, 10, 15, 18, 20, 22, 25, 28, 32],
        "extend":  "both",
    },
    "tmax": {
        "label":   "Max Temperature (0-24h)",
        "unit":    "degC",
        "cmap":    "YlOrRd",
        "levels":  [10, 15, 18, 20, 22, 25, 28, 30, 32, 35, 38],
        "extend":  "both",
    },
}


def download():
    print(f"[{datetime.now():%H:%M:%S}] Downloading ECMWF forecast...")
    client = Client("ecmwf", beta=False)
    client.retrieve(
        date=0, time=0,
        step=[12, 24],
        stream="oper", type="fc", levtype="sfc",
        param=["msl", "tp", "2t"],
        target=GRIB_FILE,
    )
    print(f"[{datetime.now():%H:%M:%S}] Download complete.")


def fix_lon(ds):
    if float(ds.longitude.max()) > 180:
        ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360) - 180)
        ds = ds.sortby("longitude")
    return ds


def clip(da, bbox):
    return da.sel(
        latitude=slice(bbox["lat_max"], bbox["lat_min"]),
        longitude=slice(bbox["lon_min"], bbox["lon_max"]),
    )


def load_field(shortname, step_range):
    ds = xr.open_dataset(
        GRIB_FILE, engine="cfgrib",
        filter_by_keys={"shortName": shortname, "stepRange": step_range},
        indexpath=None,
    )
    ds = fix_lon(ds)
    return ds[list(ds.data_vars)[0]]


def compute_mg_stats(tp_mg, msl_mg, tmin_mg, tmax_mg):
    stats = {
        "precip_mm": round(float(tp_mg.mean().values), 3),
        "mslp_hpa":  round(float(msl_mg.mean().values), 2),
        "tmin_c":    round(float(tmin_mg.mean().values), 2),
        "tmax_c":    round(float(tmax_mg.mean().values), 2),
    }
    return stats


def make_map(da_sa, msl_sa, param, run_date):
    cfg = MAP_CONFIGS[param]
    fig = plt.figure(figsize=(5, 6), facecolor="#ffffff")
    ax  = plt.axes(projection=ccrs.PlateCarree(), facecolor="#ccdff0")

    ax.set_extent([SA["lon_min"], SA["lon_max"], SA["lat_min"], SA["lat_max"]],
                  crs=ccrs.PlateCarree())

    ax.add_feature(cfeature.LAND.with_scale("50m"),     facecolor="#f0ece4", zorder=0)
    ax.add_feature(cfeature.STATES.with_scale("50m"),   edgecolor="#b0b8c0", linewidth=0.5, zorder=1)
    ax.add_feature(cfeature.BORDERS.with_scale("50m"),  edgecolor="#7a8490", linewidth=0.9, zorder=1)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"),edgecolor="#7a8490", linewidth=0.9, zorder=1)

    cf = ax.contourf(
        da_sa.longitude.values, da_sa.latitude.values, da_sa.values,
        levels=cfg["levels"], cmap=cfg["cmap"], alpha=0.82,
        transform=ccrs.PlateCarree(), extend=cfg["extend"], zorder=2,
    )

    # MSLP contours overlay on all maps
    msl_levels = np.arange(
        int(msl_sa.values.min()) - (int(msl_sa.values.min()) % 2),
        int(msl_sa.values.max()) + 4, 2
    )
    cs = ax.contour(
        msl_sa.longitude.values, msl_sa.latitude.values, msl_sa.values,
        levels=msl_levels, colors="#2d3748", linewidths=0.6, alpha=0.5,
        transform=ccrs.PlateCarree(), zorder=3,
    )
    ax.clabel(cs, fmt="%d", fontsize=6, colors="#2d3748", inline=True)

    for zone, bounds in ZONE_LABELS.items():
        clat = (bounds["lat"][0] + bounds["lat"][1]) / 2
        clon = (bounds["lon"][0] + bounds["lon"][1]) / 2
        ax.text(clon, clat, zone, fontsize=6, color="#1a202c",
                ha="center", va="center", transform=ccrs.PlateCarree(), zorder=4,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          alpha=0.72, edgecolor="#cbd5e0", linewidth=0.4))

    cbar = plt.colorbar(cf, ax=ax, orientation="vertical", pad=0.02, shrink=0.78, aspect=28)
    cbar.set_label(f"{cfg['unit']}", color="#4a5568", fontsize=8)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#4a5568", fontsize=7)

    gl = ax.gridlines(draw_labels=True, linewidth=0.25, color="#c0c8d0", alpha=0.7, linestyle="--")
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"color": "#718096", "fontsize": 6}
    gl.ylabel_style = {"color": "#718096", "fontsize": 6}

    fig.text(0.5, 0.97, f"South America — {cfg['label']}",
             ha="center", color="#1a202c", fontsize=11, fontweight="bold")
    fig.text(0.5, 0.935, f"ECMWF  |  {run_date}",
             ha="center", color="#718096", fontsize=7.5)
    fig.text(0.5, 0.005, "ECMWF Open Data · CC-BY-4.0",
             ha="center", color="#a0aec0", fontsize=6.5)

    out_path = os.path.join(MAPS_DIR, f"{run_date}_{param}.png")
    plt.savefig(out_path, dpi=100, bbox_inches="tight", facecolor="#ffffff")
    plt.close()
    print(f"[{datetime.now():%H:%M:%S}] Map saved -> {out_path}")
    return out_path


def update_database(run_date, stats):
    row = {"date": pd.Timestamp(run_date), **stats}
    new_row = pd.DataFrame([row])

    if os.path.exists(DB_FILE):
        df = pd.read_parquet(DB_FILE)
        df = df[df["date"] != pd.Timestamp(run_date)]
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        df = new_row

    df = df.sort_values("date").reset_index(drop=True)
    df.to_parquet(DB_FILE, index=False)
    print(f"[{datetime.now():%H:%M:%S}] Database updated -> {len(df)} records")


def main():
    run_date = date.today().isoformat()
    print(f"\n{'='*50}")
    print(f"  Weather Ingest  |  {run_date}")
    print(f"{'='*50}")

    download()

    print(f"[{datetime.now():%H:%M:%S}] Processing fields...")
    tp_12  = load_field("tp",  "0-12")
    tp_24  = load_field("tp",  "0-24")
    msl_24 = load_field("msl", "24")
    t2m_12 = load_field("2t",  "12")       # ~morning
    t2m_24 = load_field("2t",  "24")       # ~afternoon

    tp_mm   = (tp_24 - tp_12) * 1000      # deaccumulate + m -> mm
    msl_hpa = msl_24 / 100                 # Pa -> hPa
    tmin_c  = xr.where(t2m_12 < t2m_24, t2m_12, t2m_24) - 273.15   # K -> C
    tmax_c  = xr.where(t2m_12 > t2m_24, t2m_12, t2m_24) - 273.15   # K -> C

    # MG stats for parquet
    tp_mg   = clip(tp_mm,   MG)
    msl_mg  = clip(msl_hpa, MG)
    tmin_mg = clip(tmin_c,  MG)
    tmax_mg = clip(tmax_c,  MG)
    stats   = compute_mg_stats(tp_mg, msl_mg, tmin_mg, tmax_mg)

    print(f"  MG precip : {stats['precip_mm']:.2f} mm")
    print(f"  MG MSLP   : {stats['mslp_hpa']:.1f} hPa")
    print(f"  MG Tmin   : {stats['tmin_c']:.1f} C")
    print(f"  MG Tmax   : {stats['tmax_c']:.1f} C")

    # SA data for maps
    tp_sa   = clip(tp_mm,   SA)
    msl_sa  = clip(msl_hpa, SA)
    tmin_sa = clip(tmin_c,  SA)
    tmax_sa = clip(tmax_c,  SA)

    make_map(tp_sa,   msl_sa, "precip", run_date)
    make_map(tmin_sa, msl_sa, "tmin",   run_date)
    make_map(tmax_sa, msl_sa, "tmax",   run_date)

    update_database(run_date, stats)

    if os.path.exists(GRIB_FILE):
        os.remove(GRIB_FILE)

    print(f"[{datetime.now():%H:%M:%S}] Done.\n")


if __name__ == "__main__":
    main()
