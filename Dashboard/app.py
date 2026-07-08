import os
import glob
import json
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
    [data-testid="block-container"] { padding: 8px 16px 0 16px !important; }

    /* Section divider bar */
    .sec-divider {
        background: #1a202c;
        padding: 5px 12px;
        margin: 16px 0 6px 0;
        border-radius: 3px;
    }
    .sec-divider-label {
        font-size: 9px; font-weight: 700; color: #e2e8f0;
        letter-spacing: 0.15em; text-transform: uppercase;
    }

    .map-cap {
        font-size: 9px; color: #8896a5; text-align: center;
        margin-bottom: 1px; margin-top: 0;
    }
    /* Tighten Streamlit's default column element spacing */
    [data-testid="stVerticalBlock"] { gap: 0rem !important; }
    [data-testid="stHorizontalBlock"] { gap: 6px !important; }
    .stImage { margin-bottom: 0 !important; }
    .stImage img { border-radius: 3px; }
    .stExpander { margin-bottom: 4px !important; }
    footer { display: none; }
    h1 { font-size: 17px !important; margin-bottom: 3px !important; }
</style>
""", unsafe_allow_html=True)

st.title("Weather Aggregation")


def latest(pattern):
    files = sorted(glob.glob(os.path.join(MAPS_DIR, pattern)))
    return files[-1] if files else None


STAMP_FILE = os.path.join(BASE, "Database", "last_run.json")

def last_run(key):
    try:
        with open(STAMP_FILE) as f:
            return json.load(f).get(key, "—")
    except Exception:
        return "—"


SOURCES = [
    ("ECMWF",       "ecmwf"),
    ("OpenCharts",  "opencharts"),
    ("Maxar",       "maxar"),
    ("GWI",         "gwi_pnorm"),
    ("CPC / CPTEC", "static"),
    ("ERA5",        "era5"),
]

parts = "  &nbsp;|&nbsp;  ".join(
    f'<span style="color:#a0aec0;font-size:10px;font-weight:600;letter-spacing:.1em">{lbl}</span>'
    f'<span style="color:#4a5568;font-size:10px;margin-left:5px">{last_run(key)}</span>'
    for lbl, key in SOURCES
)
st.markdown(
    f'<div style="margin:-6px 0 14px 0;padding:6px 10px;background:#f0f2f5;border-radius:6px;'
    f'white-space:nowrap;overflow:auto">{parts}</div>',
    unsafe_allow_html=True,
)


def sec(label):
    st.markdown(
        f'<div class="sec-divider"><span class="sec-divider-label">{label}</span></div>',
        unsafe_allow_html=True,
    )


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

    with st.expander("Short-term Forecast — ECMWF Open Data", expanded=False):
        show_grid([
            (latest(ecmwf_pat.format(p="precip")), "Precip"),
            (latest(ecmwf_pat.format(p="tmin")),   "Min Temp"),
            (latest(ecmwf_pat.format(p="tmax")),   "Max Temp"),
        ], n_cols=3)

    # Maxar EN — Brazil has no region slug, others have rk_ in the middle
    en_slug = "" if rk == "br" else f"{rk}_"

    sec("Ensemble Precip (mm) — ECM vs GFS")
    show_grid([
        (latest(f"maxar_en_ecm_{en_slug}precip_mm_day1-5_*.png"),   "ECM Ensemble Day 1-5"),
        (latest(f"maxar_en_ecm_{en_slug}precip_mm_day6-10_*.png"),  "ECM Ensemble Day 6-10"),
        (latest(f"maxar_en_ecm_{en_slug}precip_mm_day11-15_*.png"), "ECM Ensemble Day 11-15"),
    ], n_cols=3)
    show_grid([
        (latest(f"maxar_en_gfs_{en_slug}precip_mm_day1-5_*.png"),   "GFS Ensemble Day 1-5"),
        (latest(f"maxar_en_gfs_{en_slug}precip_mm_day6-10_*.png"),  "GFS Ensemble Day 6-10"),
        (latest(f"maxar_en_gfs_{en_slug}precip_mm_day11-15_*.png"), "GFS Ensemble Day 11-15"),
    ], n_cols=3)
    show_grid([
        (latest(f"maxar_en_ecm_{en_slug}precip_mm_day1-15_*.png"), "ECM Ensemble Day 1-15"),
        (latest(f"maxar_en_gfs_{en_slug}precip_mm_day1-15_*.png"), "GFS Ensemble Day 1-15"),
    ], n_cols=2)

    sec("Ensemble % of Normal — ECM vs GFS")
    show_grid([
        (latest(f"maxar_en_ecm_{en_slug}precip_pct_normal_day1-5_*.png"),   "ECM Ensemble Day 1-5"),
        (latest(f"maxar_en_ecm_{en_slug}precip_pct_normal_day6-10_*.png"),  "ECM Ensemble Day 6-10"),
        (latest(f"maxar_en_ecm_{en_slug}precip_pct_normal_day11-15_*.png"), "ECM Ensemble Day 11-15"),
    ], n_cols=3)
    show_grid([
        (latest(f"maxar_en_gfs_{en_slug}precip_pct_normal_day1-5_*.png"),   "GFS Ensemble Day 1-5"),
        (latest(f"maxar_en_gfs_{en_slug}precip_pct_normal_day6-10_*.png"),  "GFS Ensemble Day 6-10"),
        (latest(f"maxar_en_gfs_{en_slug}precip_pct_normal_day11-15_*.png"), "GFS Ensemble Day 11-15"),
    ], n_cols=3)
    show_grid([
        (latest(f"gwi_pnorm_{rk}_ecm_day1-15_*.png"), "ECM Ensemble Day 1-15 (GWI)"),
        (latest(f"gwi_pnorm_{rk}_gfs_day1-15_*.png"), "GFS Ensemble Day 1-15 (GWI)"),
    ], n_cols=2)

    # OpenCharts anomaly — Brazil uses no prefix, others use rk_ prefix
    oc_prefix = "" if rk == "br" else f"{rk}_"

    sec("Weekly Precip Anomaly — ECMWF Extended")
    show_grid([
        (latest(f"opencharts_{oc_prefix}anom_tp_w1_*.png"), "Week 1"),
        (latest(f"opencharts_{oc_prefix}anom_tp_w2_*.png"), "Week 2"),
    ], n_cols=2)
    show_grid([
        (latest(f"opencharts_{oc_prefix}anom_tp_w3_*.png"), "Week 3"),
        (latest(f"opencharts_{oc_prefix}anom_tp_w4_*.png"), "Week 4"),
    ], n_cols=2)

    sec("Weekly Temp Anomaly — ECMWF Extended")
    show_grid([
        (latest(f"opencharts_{oc_prefix}anom_2t_w1_*.png"), "Week 1"),
        (latest(f"opencharts_{oc_prefix}anom_2t_w2_*.png"), "Week 2"),
    ], n_cols=2)
    show_grid([
        (latest(f"opencharts_{oc_prefix}anom_2t_w3_*.png"), "Week 3"),
        (latest(f"opencharts_{oc_prefix}anom_2t_w4_*.png"), "Week 4"),
    ], n_cols=2)

    if rk == "br":
        sec("Frost Alert — CPTEC Geadas")
        show_grid([
            (latest("static_geada_d1_*.png"), "Day 1"),
            (latest("static_geada_d2_*.png"), "Day 2"),
            (latest("static_geada_d3_*.png"), "Day 3"),
        ], n_cols=3)

        sec("Observed — CPC / NOAA")
        show_grid([
            (latest("static_cpc_7d_obs_*.png"),   "CPC 7-Day Observed"),
            (latest("static_cpc_7d_anom_*.png"),  "CPC 7-Day Anomaly"),
            (latest("static_cpc_7d_pnorm_*.png"), "CPC 7-Day % Normal"),
        ], n_cols=3)
        show_grid([
            (latest("static_cpc_30d_pnorm_*.png"), "CPC 30-Day % Normal"),
        ], n_cols=1)

    # GEFS precip anomaly — Brazil, West Africa, India
    if rk in ("br", "wa", "in"):
        gefs_d7  = latest("static_gefs_anom_d7_*.png")  if rk == "br" else latest(f"static_{rk}_gefs_anom_d7_*.png")
        gefs_d14 = latest("static_gefs_anom_d14_*.png") if rk == "br" else latest(f"static_{rk}_gefs_anom_d14_*.png")
        sec("GEFS Precip Anomaly — TropicalTidbits")
        show_grid([
            (gefs_d7,  "Days 1-7"),
            (gefs_d14, "Days 8-14"),
        ], n_cols=2)

    # Seasonal SEAS5 — Brazil + WA, IN, VN, TH, AU
    if rk in ("br", "wa", "in", "vn", "th", "au"):
        seas_p = "" if rk == "br" else f"{rk}_"
        sec("Seasonal / ENSO — ECMWF SEAS5")
        show_grid([
            (latest(f"opencharts_{seas_p}seas_m1_*.png"), "Month 1"),
            (latest(f"opencharts_{seas_p}seas_m2_*.png"), "Month 2"),
        ], n_cols=2)
        show_grid([
            (latest(f"opencharts_{seas_p}seas_m3_*.png"), "Month 3"),
            (latest(f"opencharts_{seas_p}seas_m4_*.png"), "Month 4"),
        ], n_cols=2)
        show_grid([
            (latest("opencharts_enso_*.png"), "Nino 3.4 Plumes"),
        ], n_cols=1)

    # ERA5 30-day cumulative — Brazil and West Africa
    if rk in ("br", "wa"):
        era5_file = latest("era5_precip30d_[0-9]*.png") if rk == "br" else latest("era5_wa_precip30d_*.png")
        sec("ERA5 Reanalysis — 30-Day Cumulative Precip")
        left, _ = st.columns([1, 2])
        with left:
            if era5_file:
                st.image(era5_file, use_container_width=True)
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
