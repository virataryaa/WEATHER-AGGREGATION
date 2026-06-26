import os
import glob
from datetime import datetime
import streamlit as st

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR = os.path.join(BASE, "Database", "maps")

st.set_page_config(page_title="Weather Aggregation", layout="wide")

st.markdown("""
<style>
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="block-container"] {
        background-color: #f8f9fa !important;
        padding-top: 0 !important;
    }
    [data-testid="block-container"] { padding: 12px 20px 0 20px !important; }
    .sec-label {
        font-size: 9px; font-weight: 700; color: #a0aec0;
        letter-spacing: 0.14em; text-transform: uppercase;
        margin: 18px 0 6px 0;
    }
    .map-cap {
        font-size: 10px; color: #718096; text-align: center; margin-bottom: 2px;
    }
    .stImage img { border-radius: 4px; }
    footer { display: none; }
    h1 { font-size: 18px !important; margin-bottom: 4px !important; }
</style>
""", unsafe_allow_html=True)

st.title("Weather Aggregation")


def latest(pattern):
    files = sorted(glob.glob(os.path.join(MAPS_DIR, pattern)))
    return files[-1] if files else None


def mtime(pattern):
    f = latest(pattern)
    if not f:
        return "—"
    return datetime.fromtimestamp(os.path.getmtime(f)).strftime("%d %b  %H:%M")


SOURCES = [
    ("ECMWF",       "20??-??-??_precip.png"),
    ("OpenCharts",  "opencharts_anom_tp_w1_*.png"),
    ("Maxar",       "maxar_precip_7d_*.png"),
    ("CPC / CPTEC", "static_cpc_7d_obs_*.png"),
    ("ERA5",        "era5_precip30d_*.png"),
]

parts = "  &nbsp;|&nbsp;  ".join(
    f'<span style="color:#a0aec0;font-size:10px;font-weight:600;letter-spacing:.1em">{lbl}</span>'
    f'<span style="color:#4a5568;font-size:10px;margin-left:5px">{mtime(pat)}</span>'
    for lbl, pat in SOURCES
)
st.markdown(
    f'<div style="margin:-6px 0 14px 0;padding:6px 10px;background:#f0f2f5;border-radius:6px;'
    f'white-space:nowrap;overflow:auto">{parts}</div>',
    unsafe_allow_html=True,
)


def sec(label):
    st.markdown(f'<div class="sec-label">{label}</div>', unsafe_allow_html=True)


def show_grid(items, n_cols):
    cols = st.columns(n_cols, gap="small")
    for i, (path, cap) in enumerate(items):
        with cols[i % n_cols]:
            st.markdown(f'<div class="map-cap">{cap}</div>', unsafe_allow_html=True)
            if path and os.path.exists(path):
                st.image(path, use_container_width=True)
            else:
                st.caption("—")


def region_tab(rk):
    """Render a full region tab given a region key (br / wa / vn / co)."""

    # ECMWF maps — Brazil files start with date (20??-??-??), others with rk_
    ecmwf_pat = "20??-??-??_{p}.png" if rk == "br" else f"{rk}_20??-??-??_{{p}}.png"

    sec("Short-term Forecast — ECMWF Open Data")
    show_grid([
        (latest(ecmwf_pat.format(p="precip")), "Precip"),
        (latest(ecmwf_pat.format(p="tmin")),   "Min Temp"),
        (latest(ecmwf_pat.format(p="tmax")),   "Max Temp"),
    ], n_cols=3)

    # Maxar OP — Brazil uses no prefix, others use rk_ prefix
    mx_prefix = "" if rk == "br" else f"{rk}_"

    sec("Maxar OP — 7-Day Summary")
    show_grid([
        (latest(f"maxar_{mx_prefix}precip_7d_*.png"),  "7-Day Precip"),
        (latest(f"maxar_{mx_prefix}precip_norm_*.png"),"% of Normal"),
        (latest(f"maxar_{mx_prefix}temp_850_*.png"),   "850mb Temp"),
        (latest(f"maxar_{mx_prefix}temp_2m_*.png"),    "2m Temp"),
        (latest(f"maxar_{mx_prefix}dewpoint_*.png"),   "Dewpoint"),
    ], n_cols=5)

    # Maxar EN — Brazil has no region slug, others have rk_ in the middle
    en_slug = "" if rk == "br" else f"{rk}_"

    sec("Ensemble Precip (mm) — ECM vs GFS")
    show_grid([
        (latest(f"maxar_en_ecm_{en_slug}precip_mm_day1-5_*.png"),   "ECM Day 1-5"),
        (latest(f"maxar_en_ecm_{en_slug}precip_mm_day6-10_*.png"),  "ECM Day 6-10"),
        (latest(f"maxar_en_ecm_{en_slug}precip_mm_day11-15_*.png"), "ECM Day 11-15"),
        (latest(f"maxar_en_gfs_{en_slug}precip_mm_day1-5_*.png"),   "GFS Day 1-5"),
        (latest(f"maxar_en_gfs_{en_slug}precip_mm_day6-10_*.png"),  "GFS Day 6-10"),
        (latest(f"maxar_en_gfs_{en_slug}precip_mm_day11-15_*.png"), "GFS Day 11-15"),
    ], n_cols=6)

    sec("Ensemble % of Normal — ECM vs GFS")
    show_grid([
        (latest(f"maxar_en_ecm_{en_slug}precip_pct_normal_day1-5_*.png"),   "ECM Day 1-5"),
        (latest(f"maxar_en_ecm_{en_slug}precip_pct_normal_day6-10_*.png"),  "ECM Day 6-10"),
        (latest(f"maxar_en_ecm_{en_slug}precip_pct_normal_day11-15_*.png"), "ECM Day 11-15"),
        (latest(f"maxar_en_gfs_{en_slug}precip_pct_normal_day1-5_*.png"),   "GFS Day 1-5"),
        (latest(f"maxar_en_gfs_{en_slug}precip_pct_normal_day6-10_*.png"),  "GFS Day 6-10"),
        (latest(f"maxar_en_gfs_{en_slug}precip_pct_normal_day11-15_*.png"), "GFS Day 11-15"),
    ], n_cols=6)

    # OpenCharts anomaly — Brazil uses no prefix, others use rk_ prefix
    oc_prefix = "" if rk == "br" else f"{rk}_"

    sec("Weekly Precip Anomaly — ECMWF Extended")
    show_grid([
        (latest(f"opencharts_{oc_prefix}anom_tp_w1_*.png"), "Week 1"),
        (latest(f"opencharts_{oc_prefix}anom_tp_w2_*.png"), "Week 2"),
        (latest(f"opencharts_{oc_prefix}anom_tp_w3_*.png"), "Week 3"),
        (latest(f"opencharts_{oc_prefix}anom_tp_w4_*.png"), "Week 4"),
    ], n_cols=4)

    sec("Weekly Temp Anomaly — ECMWF Extended")
    show_grid([
        (latest(f"opencharts_{oc_prefix}anom_2t_w1_*.png"), "Week 1"),
        (latest(f"opencharts_{oc_prefix}anom_2t_w2_*.png"), "Week 2"),
        (latest(f"opencharts_{oc_prefix}anom_2t_w3_*.png"), "Week 3"),
        (latest(f"opencharts_{oc_prefix}anom_2t_w4_*.png"), "Week 4"),
    ], n_cols=4)

    if rk == "br":
        sec("Frost Alert — CPTEC Geadas")
        show_grid([
            (latest("static_geada_d1_*.png"), "Day 1"),
            (latest("static_geada_d2_*.png"), "Day 2"),
            (latest("static_geada_d3_*.png"), "Day 3"),
        ], n_cols=3)

        sec("Observed — CPC / NOAA + GFS")
        show_grid([
            (latest("static_cpc_7d_obs_*.png"),    "CPC 7-Day Observed"),
            (latest("static_cpc_7d_anom_*.png"),   "CPC 7-Day Anomaly"),
            (latest("static_cpc_30d_pnorm_*.png"), "CPC 30-Day % Normal"),
            (latest("static_gfs_w1_*.png"),        "GFS Week 1"),
            (latest("static_gfs_w2_*.png"),        "GFS Week 2"),
        ], n_cols=5)

    if rk == "br":
        sec("Seasonal / ENSO — ECMWF SEAS5")
        show_grid([
            (latest("opencharts_seas_m1_*.png"), "Month 1"),
            (latest("opencharts_seas_m2_*.png"), "Month 2"),
            (latest("opencharts_seas_m3_*.png"), "Month 3"),
            (latest("opencharts_seas_m4_*.png"), "Month 4"),
            (latest("opencharts_enso_*.png"),    "Nino 3.4 Plumes"),
        ], n_cols=5)

        sec("ERA5 Reanalysis — 30-Day Cumulative Precip")
        left, _ = st.columns([1, 2])
        with left:
            f = latest("era5_precip30d_*.png")
            if f:
                st.image(f, use_container_width=True)
            else:
                st.caption("Run Ingest/ingest_era5.py")


# ─────────────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "Brazil", "Colombia", "Vietnam", "Central America",
    "West Africa", "Ecuador", "India", "Thailand", "Australia"
])
TAB_KEYS = ["br", "co", "vn", "ca", "wa", "ec", "in", "th", "au"]

for tab, rk in zip(tabs, TAB_KEYS):
    with tab:
        region_tab(rk)
