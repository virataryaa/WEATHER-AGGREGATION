import os
import glob
import pandas as pd
import streamlit as st

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE  = os.path.join(BASE, "Database", "weather_mg.parquet")
MAPS_DIR = os.path.join(BASE, "Database", "maps")

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
        padding: 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .card-header {
        font-size: 11px;
        font-weight: 600;
        color: #718096;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .meta-strip {
        display: flex;
        gap: 24px;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #edf2f7;
    }
    .meta-item { text-align: left; }
    .meta-label { font-size: 10px; color: #a0aec0; text-transform: uppercase; letter-spacing: 0.08em; }
    .meta-value { font-size: 15px; font-weight: 700; color: #2d3748; }
    .page-title {
        font-size: 20px; font-weight: 700; color: #1a202c;
        letter-spacing: 0.01em; margin-bottom: 4px;
    }
    .page-sub {
        font-size: 11px; color: #a0aec0;
        text-transform: uppercase; letter-spacing: 0.10em;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_data():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    df = pd.read_parquet(DB_FILE)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")


def latest_map():
    maps = sorted(glob.glob(os.path.join(MAPS_DIR, "*.png")))
    return maps[-1] if maps else None


df   = load_data()
today = df.iloc[-1] if not df.empty else None

st.markdown('<div class="page-title">Weather Monitor</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Precipitation · MSLP · ECMWF Open Data</div>', unsafe_allow_html=True)

# ── Minas Gerais card ───────────────────────────────────────────────────────
map_path = latest_map()

meta_html = ""
if today is not None:
    date_str   = today["date"].strftime("%d %b %Y")
    precip_str = f"{today['precip_mm']:.2f} mm"
    mslp_str   = f"{today['mslp_hpa']:.1f} hPa"
    meta_html  = f"""
    <div class="meta-strip">
        <div class="meta-item">
            <div class="meta-label">Valid</div>
            <div class="meta-value">{date_str}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Precip (12-24h)</div>
            <div class="meta-value">{precip_str}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">MSLP</div>
            <div class="meta-value">{mslp_str}</div>
        </div>
    </div>"""

st.markdown(f"""
<div class="map-card">
    <div class="card-header">Minas Gerais — Arabica</div>
""", unsafe_allow_html=True)

if map_path:
    st.image(map_path, use_container_width=True)
else:
    st.info("No map yet. Run Ingest/ingest.py to generate.")

st.markdown(meta_html + "</div>", unsafe_allow_html=True)

st.markdown("""
<div style="margin-top:30px; font-size:10px; color:#cbd5e0; text-align:center;">
    Source: ECMWF Open Data · CC-BY-4.0
</div>""", unsafe_allow_html=True)
