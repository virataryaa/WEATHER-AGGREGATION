import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
from ecmwf.opendata import Client
from datetime import date, datetime

warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRIB_FILE = os.path.join(BASE, "Ingest", "today.grib")
DB_FILE   = os.path.join(BASE, "Database", "weather_mg.parquet")
MAPS_DIR  = os.path.join(BASE, "Database", "maps")
os.makedirs(MAPS_DIR, exist_ok=True)

# Minas Gerais bounding box (for statistics)
MG = {"lat_min": -22.9, "lat_max": -14.2, "lon_min": -51.0, "lon_max": -39.8}

# Full Brazil bounding box (for map)
BRAZIL = {"lat_min": -33.8, "lat_max": 5.3, "lon_min": -73.9, "lon_max": -34.8}

ZONE_LABELS = {
    "Sul de Minas":       {"lat": (-22.5, -20.5), "lon": (-47.5, -44.5)},
    "Cerrado Mineiro":    {"lat": (-19.5, -17.0), "lon": (-48.5, -45.5)},
    "Chapada de Minas":   {"lat": (-17.5, -15.5), "lon": (-42.5, -40.5)},
    "Matas de Minas":     {"lat": (-21.0, -18.5), "lon": (-43.5, -41.0)},
}


def download():
    print(f"[{datetime.now():%H:%M:%S}] Downloading ECMWF forecast...")
    client = Client("ecmwf", beta=False)
    client.retrieve(
        date=0,
        time=0,
        step=[12, 24],
        stream="oper",
        type="fc",
        levtype="sfc",
        param=["msl", "tp"],
        target=GRIB_FILE,
    )
    print(f"[{datetime.now():%H:%M:%S}] Download complete.")


def fix_lon(ds):
    if float(ds.longitude.max()) > 180:
        ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360) - 180)
        ds = ds.sortby("longitude")
    return ds


def clip_mg(da):
    return da.sel(
        latitude=slice(MG["lat_max"], MG["lat_min"]),
        longitude=slice(MG["lon_min"], MG["lon_max"]),
    )

def clip_brazil(da):
    return da.sel(
        latitude=slice(BRAZIL["lat_max"], BRAZIL["lat_min"]),
        longitude=slice(BRAZIL["lon_min"], BRAZIL["lon_max"]),
    )


def load_field(shortname, step_range):
    ds = xr.open_dataset(
        GRIB_FILE,
        engine="cfgrib",
        filter_by_keys={"shortName": shortname, "stepRange": step_range},
        indexpath=None,
    )
    ds = fix_lon(ds)
    var = list(ds.data_vars)[0]
    return ds[var]


def compute_zone_stats(da_mm):
    stats = {}
    for zone, bounds in ZONE_LABELS.items():
        sub = da_mm.sel(
            latitude=slice(bounds["lat"][1], bounds["lat"][0]),
            longitude=slice(bounds["lon"][0], bounds["lon"][1]),
        )
        stats[zone] = float(sub.mean().values)
    return stats


def make_map(tp_mg, msl_mg, run_date):
    fig = plt.figure(figsize=(10, 8), facecolor="#ffffff")
    ax = plt.axes(projection=ccrs.PlateCarree(), facecolor="#dce9f5")

    ax.set_extent([BRAZIL["lon_min"], BRAZIL["lon_max"],
                   BRAZIL["lat_min"], BRAZIL["lat_max"]],
                  crs=ccrs.PlateCarree())

    # land base — no OCEAN/LAND features (causes artifacts), just plain bg + borders
    ax.add_feature(cfeature.LAND.with_scale("10m"), facecolor="#f0ece4", zorder=0)
    ax.add_feature(cfeature.STATES.with_scale("10m"), edgecolor="#aab0b8", linewidth=0.8, zorder=1)
    ax.add_feature(cfeature.BORDERS.with_scale("10m"), edgecolor="#7a8490", linewidth=1.2, zorder=1)
    ax.add_feature(cfeature.COASTLINE.with_scale("10m"), edgecolor="#7a8490", linewidth=1.0, zorder=1)

    # precipitation fill
    levels_tp = [0.5, 1, 2, 5, 10, 15, 20, 30, 50, 75, 100]
    cmap_tp = plt.get_cmap("YlGnBu")
    cf = ax.contourf(
        tp_mg.longitude.values, tp_mg.latitude.values, tp_mg.values,
        levels=levels_tp, cmap=cmap_tp, alpha=0.80,
        transform=ccrs.PlateCarree(), extend="max", zorder=2,
    )

    # MSLP contours
    msl_levels = np.arange(
        int(msl_mg.values.min()) - (int(msl_mg.values.min()) % 2),
        int(msl_mg.values.max()) + 4, 2
    )
    cs = ax.contour(
        msl_mg.longitude.values, msl_mg.latitude.values, msl_mg.values,
        levels=msl_levels, colors="#2d3748", linewidths=0.8, alpha=0.6,
        transform=ccrs.PlateCarree(), zorder=3,
    )
    ax.clabel(cs, fmt="%d", fontsize=7, colors="#2d3748", inline=True)

    # zone labels
    for zone, bounds in ZONE_LABELS.items():
        clat = (bounds["lat"][0] + bounds["lat"][1]) / 2
        clon = (bounds["lon"][0] + bounds["lon"][1]) / 2
        ax.text(clon, clat, zone, fontsize=7.5, color="#1a202c",
                ha="center", va="center", transform=ccrs.PlateCarree(), zorder=4,
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.75, edgecolor="#cbd5e0", linewidth=0.5))

    cbar = plt.colorbar(cf, ax=ax, orientation="vertical", pad=0.02, shrink=0.80, aspect=25)
    cbar.set_label("Precipitation (mm)", color="#4a5568", fontsize=9)
    cbar.ax.yaxis.set_tick_params(color="#4a5568")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#4a5568", fontsize=8)

    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#c0c8d0", alpha=0.8, linestyle="--")
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"color": "#718096", "fontsize": 7}
    gl.ylabel_style = {"color": "#718096", "fontsize": 7}

    fig.text(0.5, 0.97, "Minas Gerais — Precipitation & MSLP",
             ha="center", color="#1a202c", fontsize=13, fontweight="bold")
    fig.text(0.5, 0.93, f"ECMWF Forecast  |  Valid: {run_date}  |  12-24h Accumulation",
             ha="center", color="#718096", fontsize=8)
    fig.text(0.5, 0.01, "Source: ECMWF Open Data  |  CC-BY-4.0",
             ha="center", color="#a0aec0", fontsize=7)

    out_path = os.path.join(MAPS_DIR, f"{run_date}.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#ffffff")
    plt.close()
    print(f"[{datetime.now():%H:%M:%S}] Map saved -> {out_path}")
    return out_path


def update_database(run_date, precip_mg_mean, mslp_mg_mean, zone_stats):
    row = {
        "date": pd.Timestamp(run_date),
        "precip_mm": round(precip_mg_mean, 3),
        "mslp_hpa": round(mslp_mg_mean, 2),
    }
    for zone, val in zone_stats.items():
        row[zone.replace(" ", "_")] = round(val, 3)

    new_row = pd.DataFrame([row])

    if os.path.exists(DB_FILE):
        df = pd.read_parquet(DB_FILE)
        df = df[df["date"] != pd.Timestamp(run_date)]
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        df = new_row

    df = df.sort_values("date").reset_index(drop=True)
    df.to_parquet(DB_FILE, index=False)
    print(f"[{datetime.now():%H:%M:%S}] Database updated -> {len(df)} records in {DB_FILE}")
    return df


def main():
    run_date = date.today().isoformat()
    print(f"\n{'='*50}")
    print(f"  MG Weather Ingest  |  {run_date}")
    print(f"{'='*50}")

    download()

    print(f"[{datetime.now():%H:%M:%S}] Processing fields...")
    tp_12  = load_field("tp",  "0-12")
    tp_24  = load_field("tp",  "0-24")
    msl_24 = load_field("msl", "24")

    # deaccumulate precip, convert to mm
    tp_delta = (tp_24 - tp_12) * 1000
    msl_hpa  = msl_24 / 100

    tp_mg     = clip_mg(tp_delta)
    msl_mg    = clip_mg(msl_hpa)
    tp_brazil = clip_brazil(tp_delta)
    msl_brazil= clip_brazil(msl_hpa)

    precip_mean = float(tp_mg.mean().values)
    mslp_mean   = float(msl_mg.mean().values)
    zone_stats  = compute_zone_stats(tp_mg)

    print(f"  MG mean precip : {precip_mean:.2f} mm")
    print(f"  MG mean MSLP   : {mslp_mean:.1f} hPa")
    for z, v in zone_stats.items():
        print(f"  {z:<22}: {v:.2f} mm")

    make_map(tp_brazil, msl_brazil, run_date)
    update_database(run_date, precip_mean, mslp_mean, zone_stats)

    # cleanup grib
    if os.path.exists(GRIB_FILE):
        os.remove(GRIB_FILE)
        for idx in [GRIB_FILE + ".923a8.idx"]:
            if os.path.exists(idx):
                os.remove(idx)

    print(f"[{datetime.now():%H:%M:%S}] Done.\n")


if __name__ == "__main__":
    main()
