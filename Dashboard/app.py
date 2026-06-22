import os
import glob
import streamlit as st

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR = os.path.join(BASE, "Database", "maps")

ECMWF_PARAMS = {
    "Precipitation": "precip",
    "Min Temp":      "tmin",
    "Max Temp":      "tmax",
}

MAXAR_PARAMS = {
    "7-Day Precip":      "precip_7d",
    "Precip vs Normal":  "precip_norm",
    "2m Temperature":    "temp_2m",
    "850mb Temp":        "temp_850",
    "Dewpoint":          "dewpoint",
}

st.set_page_config(page_title="Weather", layout="wide")

st.markdown("""
<style>
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="block-container"] {
        background-color: #f8f9fa !important;
        padding-top: 0 !important;
    }
    [data-testid="block-container"] { padding: 16px 24px 0 24px !important; }
    .card-label {
        font-size: 9px; font-weight: 600; color: #a0aec0;
        letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 6px;
    }
    div[data-testid="stRadio"] label p { font-size: 11px !important; color: #4a5568; }
    .stImage img { border-radius: 5px; }
    footer { display: none; }
    .divider { border-left: 1px solid #e2e8f0; height: 100%; }
</style>
""", unsafe_allow_html=True)


def latest_date(prefix="", suffix="_precip.png"):
    pattern = os.path.join(MAPS_DIR, f"{prefix}*{suffix}")
    maps = sorted(glob.glob(pattern))
    if not maps:
        return None
    fname = os.path.basename(maps[-1])
    return fname.replace(prefix, "").replace(suffix, "")


def show_map(path):
    if path and os.path.exists(path):
        st.image(path, use_container_width=True)
    else:
        st.caption("Map not available.")


ecmwf_date = latest_date(prefix="", suffix="_precip.png")
maxar_date = latest_date(prefix="maxar_precip_7d_", suffix=".png")

left, right = st.columns(2, gap="large")

# ── ECMWF card ───────────────────────────────────────────────────────────────
with left:
    st.markdown('<div class="card-label">ECMWF Open Data — South America</div>', unsafe_allow_html=True)
    e_param = st.radio("e", list(ECMWF_PARAMS.keys()), horizontal=True, label_visibility="collapsed", key="ecmwf")
    if ecmwf_date:
        show_map(os.path.join(MAPS_DIR, f"{ecmwf_date}_{ECMWF_PARAMS[e_param]}.png"))
    else:
        st.caption("Run Ingest/ingest.py to generate maps.")

# ── Maxar card ───────────────────────────────────────────────────────────────
with right:
    st.markdown('<div class="card-label">Maxar WeatherDesk — Brazil (ECMWF Op)</div>', unsafe_allow_html=True)
    m_param = st.radio("m", list(MAXAR_PARAMS.keys()), horizontal=True, label_visibility="collapsed", key="maxar")
    if maxar_date:
        show_map(os.path.join(MAPS_DIR, f"maxar_{MAXAR_PARAMS[m_param]}_{maxar_date}.png"))
    else:
        st.caption("Run Ingest/ingest_maxar.py to generate maps.")
