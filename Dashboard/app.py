import os
import glob
import pandas as pd
import streamlit as st

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE  = os.path.join(BASE, "Database", "weather_mg.parquet")
MAPS_DIR = os.path.join(BASE, "Database", "maps")

PARAMS = {
    "Precipitation": "precip",
    "Min Temperature": "tmin",
    "Max Temperature": "tmax",
}

st.set_page_config(page_title="Weather — HardMiner", layout="wide")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="block-container"] {
        background-color: #f8f9fa !important;
    }
    .map-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 16px 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .card-header {
        font-size: 10px; font-weight: 600; color: #718096;
        letter-spacing: 0.10em; text-transform: uppercase; margin-bottom: 10px;
    }
    .meta-strip {
        display: flex; gap: 20px; margin-top: 8px;
        padding-top: 8px; border-top: 1px solid #edf2f7;
    }
    .meta-label { font-size: 9px; color: #a0aec0; text-transform: uppercase; letter-spacing: 0.08em; }
    .meta-value { font-size: 14px; font-weight: 700; color: #2d3748; }
    .page-title { font-size: 18px; font-weight: 700; color: #1a202c; margin-bottom: 2px; }
    .page-sub   { font-size: 10px; color: #a0aec0; text-transform: uppercase;
                  letter-spacing: 0.10em; margin-bottom: 16px; }
    div[data-testid="stRadio"] > label { font-size: 11px !important; }
    div[data-testid="stRadio"] { margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_data():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    df = pd.read_parquet(DB_FILE)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")


def get_map(run_date, param_key):
    path = os.path.join(MAPS_DIR, f"{run_date}_{param_key}.png")
    return path if os.path.exists(path) else None


def latest_date():
    maps = sorted(glob.glob(os.path.join(MAPS_DIR, "*_precip.png")))
    if not maps:
        return None
    return os.path.basename(maps[-1]).replace("_precip.png", "")


df         = load_data()
today      = df.iloc[-1] if not df.empty else None
run_date   = latest_date()

st.markdown('<div class="page-title">Weather Monitor</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Precipitation · Temperature · ECMWF Open Data</div>', unsafe_allow_html=True)

# ── South America — Coffee card ──────────────────────────────────────────────
col_map, col_gap = st.columns([2, 1])

with col_map:
    param_label = st.radio(
        "Parameter", list(PARAMS.keys()),
        horizontal=True, label_visibility="collapsed"
    )
    param_key = PARAMS[param_label]

    st.markdown('<div class="map-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">South America — Coffee Growing Regions</div>', unsafe_allow_html=True)

    if run_date:
        map_path = get_map(run_date, param_key)
        if map_path:
            st.image(map_path, use_container_width=True)
        else:
            st.info(f"No {param_label} map for {run_date}. Re-run ingest.")
    else:
        st.info("No maps yet. Run Ingest/ingest.py.")

    # meta strip
    if today is not None:
        date_str = today["date"].strftime("%d %b %Y")
        precip   = f"{today['precip_mm']:.2f} mm"
        tmin     = f"{today['tmin_c']:.1f} C" if "tmin_c" in today else "—"
        tmax     = f"{today['tmax_c']:.1f} C" if "tmax_c" in today else "—"
        mslp     = f"{today['mslp_hpa']:.1f} hPa"
        st.markdown(f"""
        <div class="meta-strip">
            <div><div class="meta-label">Valid</div><div class="meta-value">{date_str}</div></div>
            <div><div class="meta-label">MG Precip</div><div class="meta-value">{precip}</div></div>
            <div><div class="meta-label">MG Tmin</div><div class="meta-value">{tmin}</div></div>
            <div><div class="meta-label">MG Tmax</div><div class="meta-value">{tmax}</div></div>
            <div><div class="meta-label">MSLP</div><div class="meta-value">{mslp}</div></div>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div style="margin-top:20px;font-size:9px;color:#cbd5e0;text-align:center;">
    ECMWF Open Data · CC-BY-4.0
</div>""", unsafe_allow_html=True)
