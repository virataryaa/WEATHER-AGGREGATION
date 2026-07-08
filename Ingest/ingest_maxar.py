"""
Maxar WeatherDesk -- Global Models Images for Brazil.

Two sections:
  1. Operational (OP) single-frame variables  -> maxar_{key}_{date}.png
  2. Ensemble (EN) period-summary precip       -> maxar_en_{var}_{window}_{date}.png
     Variables: PS (mm), PPDP (% of normal)
     Windows:   day1-5, day6-10, day11-15
     Models:    ECM, GFS
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

# --- Operational single-frame variables ---
OP_VARIABLES = {
    "precip_7d":   ("PS",     "dr-0007", "7-Day Cumul. Precip"),
    "precip_norm": ("PPDP",   "dr-0007", "Precip % of Normal"),
    "temp_2m":     ("T2MS",   "hr-0024", "2m Temperature"),
    "temp_850":    ("T850C",  "hr-0024", "850mb Temp (Frost Signal)"),
    "dewpoint":    ("2MDEWP", "hr-0024", "Dewpoint"),
}

# --- Ensemble period-summary variables ---
EN_VARIABLES = {
    "PS":   "precip_mm",
    "PPDP": "precip_pct_normal",
}
EN_WINDOWS = [
    ("day1-5",   5),
    ("day6-10",  10),
    ("day11-15", 15),
]
EN_MODELS = ["ecm", "gfs"]


def api_get(params):
    r = requests.get(API_URL, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def download_image(path):
    r = requests.get(IMG_BASE + path, timeout=20)
    r.raise_for_status()
    return r.content


def _parse_dt(s):
    return datetime.fromisoformat(s[:19].replace("Z", ""))


# ── Operational ──────────────────────────────────────────────────────────────

def fetch_op(variable_key, code, pref_duration, run_date):
    params = {"model": "ecm", "type": "op", "run": "00", "region": "BR", "variable": code}
    try:
        data   = api_get(params)
    except Exception as e:
        print(f"  [op/{variable_key}] API error: {e}")
        return
    by_path   = data.get("models", {}).get("byPath", {})
    available = [p for p, v in by_path.items() if v.get("available")]
    preferred = [p for p in available if pref_duration in p]
    chosen    = preferred or available
    if not chosen:
        print(f"  [op/{variable_key}] no images")
        return
    path = chosen[len(chosen) // 2]
    try:
        content = download_image(path)
    except Exception as e:
        print(f"  [op/{variable_key}] download error: {e}")
        return
    out = os.path.join(MAPS_DIR, f"maxar_{variable_key}_{run_date}.png")
    with open(out, "wb") as f:
        f.write(content)
    print(f"  [op/{variable_key}] -> {os.path.basename(out)}  ({len(content):,} B)")


# ── Ensemble ─────────────────────────────────────────────────────────────────

def find_window_frame(by_path, init_dt, day_end):
    for path, info in by_path.items():
        if not info.get("available"):
            continue
        if "dr-0005_" not in os.path.basename(path):
            continue
        vt = info.get("validTime", "")
        if not vt:
            continue
        days_out = (_parse_dt(vt) - init_dt).total_seconds() / 86400
        if abs(days_out - day_end) < 0.1:
            return path
    return None


def find_combined_frame(by_path, init_dt):
    """Find the 1-15 day cumulative frame (dr-0015_) at day 15."""
    for path, info in by_path.items():
        if not info.get("available"):
            continue
        if "dr-0015_" not in os.path.basename(path):
            continue
        vt = info.get("validTime", "")
        if not vt:
            continue
        days_out = (_parse_dt(vt) - init_dt).total_seconds() / 86400
        if abs(days_out - 15) < 0.5:
            return path
    return None


def fetch_en(run_date):
    for model in EN_MODELS:
        for code, var_label in EN_VARIABLES.items():
            params = {"model": model, "type": "EN", "run": "00", "region": "BR", "variable": code}
            try:
                data = api_get(params)
            except Exception as e:
                print(f"  [en/{model}/{code}] API error: {e}")
                continue
            init_time = data.get("initTime", "")
            if not init_time:
                print(f"  [en/{model}/{code}] no initTime")
                continue
            init_dt  = _parse_dt(init_time)
            by_path  = data.get("models", {}).get("byPath", {})
            for window_label, day_end in EN_WINDOWS:
                path = find_window_frame(by_path, init_dt, day_end)
                if path is None:
                    print(f"  [en/{model}/{code}/{window_label}] frame not found")
                    continue
                key = f"en_{model}_{var_label}_{window_label}"
                out = os.path.join(MAPS_DIR, f"maxar_{key}_{run_date}.png")
                try:
                    content = download_image(path)
                    with open(out, "wb") as f:
                        f.write(content)
                    print(f"  [en/{model}/{code}/{window_label}] -> {os.path.basename(out)}  ({len(content):,} B)")
                except Exception as e:
                    print(f"  [en/{model}/{code}/{window_label}] download error: {e}")
            # 1-15 combined
            path15 = find_combined_frame(by_path, init_dt)
            if path15:
                key = f"en_{model}_{var_label}_day1-15"
                out = os.path.join(MAPS_DIR, f"maxar_{key}_{run_date}.png")
                try:
                    content = download_image(path15)
                    with open(out, "wb") as f:
                        f.write(content)
                    print(f"  [en/{model}/{code}/day1-15] -> {os.path.basename(out)}  ({len(content):,} B)")
                except Exception as e:
                    print(f"  [en/{model}/{code}/day1-15] download error: {e}")


# ── Regional runs ────────────────────────────────────────────────────────────
# region_key -> (Maxar region code, display name)
EXTRA_REGIONS = {
    "wa": ("WA", "West Africa"),
    "vn": ("SE", "Vietnam / SE Asia"),
    "co": ("CO", "Colombia / N. S. America"),
    "ca": ("CA", "Central America"),
    "ec": ("CO", "Ecuador (N. S. America map)"),   # CO covers Ecuador too
    "in": ("IN", "India"),
    "th": ("SE", "Thailand (SE Asia map)"),         # SE covers Thailand too
    "au": ("AU", "Australia"),
    "us": ("US", "United States"),
}


def fetch_op_region(region_key, maxar_region, run_date):
    for key, (code, duration, label) in OP_VARIABLES.items():
        params = {"model": "ecm", "type": "op", "run": "00",
                  "region": maxar_region, "variable": code}
        try:
            data   = api_get(params)
        except Exception as e:
            print(f"  [{region_key}/op/{key}] API error: {e}")
            continue
        by_path   = data.get("models", {}).get("byPath", {})
        available = [p for p, v in by_path.items() if v.get("available")]
        preferred = [p for p in available if duration in p]
        chosen    = preferred or available
        if not chosen:
            print(f"  [{region_key}/op/{key}] no images")
            continue
        path = chosen[len(chosen) // 2]
        try:
            content = download_image(path)
            out = os.path.join(MAPS_DIR, f"maxar_{region_key}_{key}_{run_date}.png")
            with open(out, "wb") as f:
                f.write(content)
            print(f"  [{region_key}/op/{key}] -> {os.path.basename(out)}")
        except Exception as e:
            print(f"  [{region_key}/op/{key}] download error: {e}")


def fetch_en_region(region_key, maxar_region, run_date):
    for model in EN_MODELS:
        for code, var_label in EN_VARIABLES.items():
            params = {"model": model, "type": "EN", "run": "00",
                      "region": maxar_region, "variable": code}
            try:
                data = api_get(params)
            except Exception as e:
                print(f"  [{region_key}/en/{model}/{code}] API error: {e}")
                continue
            init_time = data.get("initTime", "")
            if not init_time:
                continue
            init_dt = _parse_dt(init_time)
            by_path = data.get("models", {}).get("byPath", {})
            for window_label, day_end in EN_WINDOWS:
                path = find_window_frame(by_path, init_dt, day_end)
                if path is None:
                    print(f"  [{region_key}/en/{model}/{code}/{window_label}] not found")
                    continue
                out = os.path.join(MAPS_DIR,
                    f"maxar_en_{model}_{region_key}_{var_label}_{window_label}_{run_date}.png")
                try:
                    content = download_image(path)
                    with open(out, "wb") as f:
                        f.write(content)
                    print(f"  [{region_key}/en/{model}/{code}/{window_label}] -> {os.path.basename(out)}")
                except Exception as e:
                    print(f"  [{region_key}/en/{model}/{code}/{window_label}] error: {e}")
            # 1-15 combined
            path15 = find_combined_frame(by_path, init_dt)
            if path15:
                out = os.path.join(MAPS_DIR,
                    f"maxar_en_{model}_{region_key}_{var_label}_day1-15_{run_date}.png")
                try:
                    content = download_image(path15)
                    with open(out, "wb") as f:
                        f.write(content)
                    print(f"  [{region_key}/en/{model}/{code}/day1-15] -> {os.path.basename(out)}")
                except Exception as e:
                    print(f"  [{region_key}/en/{model}/{code}/day1-15] error: {e}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    run_date = date.today().isoformat()
    print(f"\n{'='*55}")
    print(f"  Maxar Ingest  |  {run_date}")
    print(f"{'='*55}")

    print("\n  [Brazil — Operational]")
    for key, (code, duration, label) in OP_VARIABLES.items():
        print(f"  {label} ...")
        fetch_op(key, code, duration, run_date)

    print("\n  [Brazil — Ensemble Period Summary]")
    fetch_en(run_date)

    for region_key, (maxar_region, display_name) in EXTRA_REGIONS.items():
        print(f"\n  [{display_name} — Operational]")
        fetch_op_region(region_key, maxar_region, run_date)
        print(f"\n  [{display_name} — Ensemble]")
        fetch_en_region(region_key, maxar_region, run_date)

    from run_stamp import stamp
    stamp("maxar")
    print(f"\n[{datetime.now():%H:%M:%S}] Done.\n")


if __name__ == "__main__":
    main()
