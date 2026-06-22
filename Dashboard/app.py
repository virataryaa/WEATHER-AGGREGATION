import os
import glob
import streamlit as st

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR = os.path.join(BASE, "Database", "maps")

PARAMS = {
    "Precipitation":   "precip",
    "Min Temperature": "tmin",
    "Max Temperature": "tmax",
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
    div[data-testid="stRadio"] > div { gap: 20px; }
    div[data-testid="stRadio"] label p { font-size: 12px !important; color: #4a5568; }
    .stImage img { border-radius: 6px; }
    footer { display: none; }
</style>
""", unsafe_allow_html=True)


def latest_date():
    maps = sorted(glob.glob(os.path.join(MAPS_DIR, "*_precip.png")))
    return os.path.basename(maps[-1]).replace("_precip.png", "") if maps else None


run_date = latest_date()

param_label = st.radio("", list(PARAMS.keys()), horizontal=True, label_visibility="collapsed")
param_key   = PARAMS[param_label]

if run_date:
    map_path = os.path.join(MAPS_DIR, f"{run_date}_{param_key}.png")
    if os.path.exists(map_path):
        st.image(map_path, use_container_width=True)
    else:
        st.caption(f"No {param_label} map for {run_date}.")
else:
    st.caption("No maps yet — run Ingest/ingest.py.")
