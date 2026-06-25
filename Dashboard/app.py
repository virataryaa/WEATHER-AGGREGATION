import os
import glob
import streamlit as st

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR = os.path.join(BASE, "Database", "maps")

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
</style>
""", unsafe_allow_html=True)


def latest(pattern):
    files = sorted(glob.glob(os.path.join(MAPS_DIR, pattern)))
    return files[-1] if files else None


def latest_date_from(prefix, suffix="_precip.png"):
    files = sorted(glob.glob(os.path.join(MAPS_DIR, f"{prefix}*{suffix}")))
    if not files:
        return None
    fname = os.path.basename(files[-1])
    return fname.replace(prefix, "").replace(suffix, "")


def show(path):
    if path and os.path.exists(path):
        st.image(path, use_container_width=True)
    else:
        st.caption("Not available — run ingest.")


# ── Dates ────────────────────────────────────────────────────────────────────
ecmwf_date   = latest_date_from("", "_precip.png")
maxar_date   = latest_date_from("maxar_precip_7d_", ".png")
charts_date  = latest_date_from("opencharts_anom_tp_w1_", ".png")
static_date  = latest_date_from("static_geada_d1_", ".png")

# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Forecast", "Anomaly", "Frost Alert", "Observed", "Seasonal / ENSO", "ERA5"
])

# ── Tab 1: Forecast ──────────────────────────────────────────────────────────
with tab1:
    left, right = st.columns(2, gap="large")

    ECMWF_PARAMS = {"Precipitation": "precip", "Min Temp": "tmin", "Max Temp": "tmax"}
    MAXAR_OP_PARAMS = {
        "7-Day Precip":     "precip_7d",
        "% of Normal":      "precip_norm",
        "2m Temperature":   "temp_2m",
        "850mb Temp":       "temp_850",
        "Dewpoint":         "dewpoint",
    }

    with left:
        st.markdown('<div class="card-label">ECMWF Open Data -- South America</div>', unsafe_allow_html=True)
        e_p = st.radio("e", list(ECMWF_PARAMS), horizontal=True, label_visibility="collapsed", key="ecmwf")
        if ecmwf_date:
            show(os.path.join(MAPS_DIR, f"{ecmwf_date}_{ECMWF_PARAMS[e_p]}.png"))
        else:
            st.caption("Run Ingest/ingest.py")

    with right:
        st.markdown('<div class="card-label">Maxar WeatherDesk -- Brazil (ECMWF Op)</div>', unsafe_allow_html=True)
        m_p = st.radio("m", list(MAXAR_OP_PARAMS), horizontal=True, label_visibility="collapsed", key="maxar_op")
        if maxar_date:
            show(os.path.join(MAPS_DIR, f"maxar_{MAXAR_OP_PARAMS[m_p]}_{maxar_date}.png"))
        else:
            st.caption("Run Ingest/ingest_maxar.py")


# ── Tab 2: Anomaly ───────────────────────────────────────────────────────────
with tab2:
    left, right = st.columns(2, gap="large")

    WEEK_OPTS  = {"Week 1": "w1", "Week 2": "w2", "Week 3": "w3", "Week 4": "w4"}

    with left:
        st.markdown('<div class="card-label">ECMWF Extended -- Weekly Precip Anomaly</div>', unsafe_allow_html=True)
        wk_tp = st.radio("wtp", list(WEEK_OPTS), horizontal=True, label_visibility="collapsed", key="anom_tp")
        d = charts_date
        if d:
            show(os.path.join(MAPS_DIR, f"opencharts_anom_tp_{WEEK_OPTS[wk_tp]}_{d}.png"))
        else:
            st.caption("Run Ingest/ingest_opencharts.py")

    with right:
        st.markdown('<div class="card-label">ECMWF Extended -- Weekly Temp Anomaly</div>', unsafe_allow_html=True)
        wk_2t = st.radio("w2t", list(WEEK_OPTS), horizontal=True, label_visibility="collapsed", key="anom_2t")
        d2 = latest_date_from("opencharts_anom_2t_w1_", ".png")
        if d2:
            show(os.path.join(MAPS_DIR, f"opencharts_anom_2t_{WEEK_OPTS[wk_2t]}_{d2}.png"))
        else:
            st.caption("Run Ingest/ingest_opencharts.py")

    st.markdown("---")
    st.markdown('<div class="card-label">Maxar WeatherDesk -- Ensemble Precip (ECM vs GFS)</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="medium")
    EN_WINDOWS = {"Day 1-5": "day1-5", "Day 6-10": "day6-10", "Day 11-15": "day11-15"}
    en_window  = st.radio("enw", list(EN_WINDOWS), horizontal=True, label_visibility="collapsed", key="en_win")
    en_var     = st.radio("env", ["Precip (mm)", "% of Normal"], horizontal=True, label_visibility="collapsed", key="en_var")
    en_var_key = "precip_mm" if en_var == "Precip (mm)" else "precip_pct_normal"
    w          = EN_WINDOWS[en_window]
    d_en       = latest_date_from(f"maxar_en_ecm_{en_var_key}_{w}_", ".png")

    with c1:
        st.caption("ECM Ensemble")
        if d_en:
            show(os.path.join(MAPS_DIR, f"maxar_en_ecm_{en_var_key}_{w}_{d_en}.png"))
        else:
            st.caption("No data")
    with c2:
        st.caption("GFS Ensemble")
        d_gfs = latest_date_from(f"maxar_en_gfs_{en_var_key}_{w}_", ".png")
        if d_gfs:
            show(os.path.join(MAPS_DIR, f"maxar_en_gfs_{en_var_key}_{w}_{d_gfs}.png"))
        else:
            st.caption("No data")


# ── Tab 3: Frost Alert ───────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="card-label">CPTEC -- Previsao de Geadas (Brazil Frost Forecast)</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="medium")
    for col, day in zip([c1, c2, c3], [1, 2, 3]):
        with col:
            st.caption(f"Day {day}")
            d = latest_date_from(f"static_geada_d{day}_", ".png")
            if d:
                show(os.path.join(MAPS_DIR, f"static_geada_d{day}_{d}.png"))
            else:
                st.caption("Run Ingest/ingest_static.py")


# ── Tab 4: Observed ──────────────────────────────────────────────────────────
with tab4:
    left, right = st.columns(2, gap="large")

    CPC_OPTS = {
        "7-Day Observed":       "cpc_7d_obs",
        "7-Day Anomaly":        "cpc_7d_anom",
        "30-Day % of Normal":   "cpc_30d_pnorm",
    }
    GFS_OPTS = {
        "Week 1 Total Precip":  "gfs_w1",
        "Week 2 Total Precip":  "gfs_w2",
        "GEFS Anom Days 1-7":   "gefs_anom_d7",
        "GEFS Anom Days 8-14":  "gefs_anom_d14",
    }

    with left:
        st.markdown('<div class="card-label">CPC/NOAA -- Observed Precipitation (S. America)</div>', unsafe_allow_html=True)
        cpc_p = st.radio("cpc", list(CPC_OPTS), horizontal=True, label_visibility="collapsed", key="cpc")
        d = latest_date_from(f"static_{CPC_OPTS[cpc_p]}_", ".png")
        if d:
            show(os.path.join(MAPS_DIR, f"static_{CPC_OPTS[cpc_p]}_{d}.png"))
        else:
            st.caption("Run Ingest/ingest_static.py")

    with right:
        st.markdown('<div class="card-label">GFS / GEFS -- Model Forecast (S. America)</div>', unsafe_allow_html=True)
        gfs_p = st.radio("gfs", list(GFS_OPTS), horizontal=True, label_visibility="collapsed", key="gfs")
        d = latest_date_from(f"static_{GFS_OPTS[gfs_p]}_", ".png")
        if d:
            show(os.path.join(MAPS_DIR, f"static_{GFS_OPTS[gfs_p]}_{d}.png"))
        else:
            st.caption("Run Ingest/ingest_static.py")


# ── Tab 5: Seasonal / ENSO ───────────────────────────────────────────────────
with tab5:
    left, right = st.columns(2, gap="large")

    MONTH_OPTS = {"Month 1": "m1", "Month 2": "m2", "Month 3": "m3", "Month 4": "m4"}

    with left:
        st.markdown('<div class="card-label">ECMWF SEAS5 -- Seasonal Rainfall Forecast (S. America)</div>', unsafe_allow_html=True)
        mo = st.radio("mo", list(MONTH_OPTS), horizontal=True, label_visibility="collapsed", key="seas")
        d  = latest_date_from(f"opencharts_seas_{MONTH_OPTS[mo]}_", ".png")
        if d:
            show(os.path.join(MAPS_DIR, f"opencharts_seas_{MONTH_OPTS[mo]}_{d}.png"))
        else:
            st.caption("Run Ingest/ingest_opencharts.py")

    with right:
        st.markdown('<div class="card-label">ECMWF SEAS5 -- ENSO Nino 3.4 Plumes</div>', unsafe_allow_html=True)
        enso_f = latest(f"opencharts_enso_*.png")
        show(enso_f)
        if enso_f:
            st.caption(os.path.basename(enso_f).replace("opencharts_enso_", "").replace(".png", ""))


# ── Tab 6: ERA5 ──────────────────────────────────────────────────────────────
with tab6:
    left6, _ = st.columns([1, 1])
    with left6:
        st.markdown('<div class="card-label">ERA5 Reanalysis -- 30-Day Cumulative Precip</div>', unsafe_allow_html=True)
        era5_files = sorted(glob.glob(os.path.join(MAPS_DIR, "era5_precip30d_*.png")))
        if era5_files:
            show(era5_files[-1])
            fname = os.path.basename(era5_files[-1])
            st.caption(f"Generated: {fname.replace('era5_precip30d_', '').replace('.png', '')}")
        else:
            st.caption("Run Ingest/ingest_era5.py")
