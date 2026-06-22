import os
import glob
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import date, timedelta

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE  = os.path.join(BASE, "Database", "weather_mg.parquet")
MAPS_DIR = os.path.join(BASE, "Database", "maps")

ZONES = ["Sul_de_Minas", "Cerrado_Mineiro", "Chapada_de_Minas", "Matas_de_Minas"]
ZONE_LABELS = {z: z.replace("_", " ") for z in ZONES}
ZONE_COLORS = {
    "Sul_de_Minas":     "#4299e1",
    "Cerrado_Mineiro":  "#48bb78",
    "Chapada_de_Minas": "#ed8936",
    "Matas_de_Minas":   "#9f7aea",
}

st.set_page_config(page_title="MG Weather — HardMiner", layout="wide", page_icon="")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] { background-color: #0d1117; }
    [data-testid="stSidebar"] { background-color: #111827; }
    h1, h2, h3, h4, p, label, div { color: #e2e8f0; }
    .kpi-card {
        background: #1a2232;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 18px 20px;
        text-align: center;
    }
    .kpi-label { font-size: 11px; color: #718096; letter-spacing: 0.08em; text-transform: uppercase; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #e2e8f0; margin: 6px 0 2px; }
    .kpi-sub   { font-size: 11px; color: #4a5568; }
    .kpi-up    { color: #68d391; }
    .kpi-down  { color: #fc8181; }
    .section-header {
        font-size: 11px; color: #718096; letter-spacing: 0.12em;
        text-transform: uppercase; margin: 24px 0 10px;
        border-bottom: 1px solid #2d3748; padding-bottom: 6px;
    }
    [data-testid="stPlotlyChart"] { border-radius: 8px; }
    .stSelectbox label { color: #a0aec0; font-size: 12px; }
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


def delta_str(current, previous, unit="mm"):
    if pd.isna(previous):
        return ""
    diff = current - previous
    sign = "+" if diff >= 0 else ""
    cls  = "kpi-up" if diff >= 0 else "kpi-down"
    return f'<span class="{cls}">{sign}{diff:.1f} {unit} vs prev</span>'


def kpi(label, value, sub="", fmt="{:.1f}"):
    val_str = fmt.format(value) if not pd.isna(value) else "—"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{val_str}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)


def chart_precip(df, window):
    df_w = df.tail(window)
    fig = go.Figure()
    for zone in ZONES:
        if zone in df_w.columns:
            fig.add_trace(go.Scatter(
                x=df_w["date"], y=df_w[zone],
                name=ZONE_LABELS[zone],
                mode="lines+markers",
                line=dict(color=ZONE_COLORS[zone], width=2),
                marker=dict(size=4),
                hovertemplate="%{x|%d %b}<br>%{y:.2f} mm<extra>" + ZONE_LABELS[zone] + "</extra>",
            ))
    fig.update_layout(
        plot_bgcolor="#111827", paper_bgcolor="#111827",
        font=dict(color="#a0aec0", size=11),
        legend=dict(bgcolor="#0d1117", bordercolor="#2d3748", borderwidth=1, font=dict(size=10)),
        xaxis=dict(gridcolor="#1f2937", zeroline=False, tickfont=dict(color="#718096")),
        yaxis=dict(gridcolor="#1f2937", zeroline=False, tickfont=dict(color="#718096"), title="mm"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        hovermode="x unified",
    )
    return fig


def chart_mslp(df, window):
    df_w = df.tail(window)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_w["date"], y=df_w["mslp_hpa"],
        mode="lines+markers",
        line=dict(color="#90cdf4", width=2),
        marker=dict(size=4),
        fill="tozeroy", fillcolor="rgba(144,205,244,0.07)",
        hovertemplate="%{x|%d %b}<br>%{y:.1f} hPa<extra>MSLP</extra>",
    ))
    fig.update_layout(
        plot_bgcolor="#111827", paper_bgcolor="#111827",
        font=dict(color="#a0aec0", size=11),
        xaxis=dict(gridcolor="#1f2937", zeroline=False, tickfont=dict(color="#718096")),
        yaxis=dict(gridcolor="#1f2937", zeroline=False, tickfont=dict(color="#718096"), title="hPa"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=240,
        showlegend=False,
    )
    return fig


def bar_zones(df):
    if df.empty:
        return go.Figure()
    latest = df.iloc[-1]
    zones  = [ZONE_LABELS[z] for z in ZONES if z in df.columns]
    values = [latest[z] for z in ZONES if z in df.columns]
    colors = [ZONE_COLORS[z] for z in ZONES if z in df.columns]
    fig = go.Figure(go.Bar(
        x=zones, y=values, marker_color=colors,
        hovertemplate="%{x}<br>%{y:.2f} mm<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor="#111827", paper_bgcolor="#111827",
        font=dict(color="#a0aec0", size=11),
        xaxis=dict(gridcolor="#1f2937", zeroline=False, tickfont=dict(color="#718096")),
        yaxis=dict(gridcolor="#1f2937", zeroline=False, tickfont=dict(color="#718096"), title="mm"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=240,
        showlegend=False,
    )
    return fig


# ── Layout ──────────────────────────────────────────────────────────────────

st.markdown("""
<div style="text-align:center; padding: 20px 0 10px;">
    <div style="font-size:26px; font-weight:700; color:#e2e8f0; letter-spacing:0.02em;">
        Minas Gerais — Weather Monitor
    </div>
    <div style="font-size:12px; color:#4a5568; margin-top:4px;">
        PRECIPITATION · MSLP  |  ECMWF Open Data  |  Arabica Growing Zones
    </div>
</div>
""", unsafe_allow_html=True)

df = load_data()

if df.empty:
    st.warning("No data yet. Run Ingest/ingest.py to populate the database.")
    st.stop()

today    = df.iloc[-1]
prev     = df.iloc[-2] if len(df) > 1 else pd.Series(dtype=float)
last_7   = df.tail(7)["precip_mm"].sum()
last_30  = df.tail(30)["precip_mm"].sum()
last_date = today["date"].strftime("%d %b %Y")

# KPI row
st.markdown('<div class="section-header">Today\'s Reading</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi("Date", 0, sub=last_date, fmt="{:.0f}")
    st.markdown(f"""<div class="kpi-card" style="margin-top:0;padding-top:0;border:none;">
        <div class="kpi-value" style="font-size:16px;">{last_date}</div></div>""", unsafe_allow_html=True)
with c1:
    pass

# rebuild cleaner
col1, col2, col3, col4 = st.columns(4)
with col1:
    sub = delta_str(today["precip_mm"], prev.get("precip_mm", float("nan")))
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">MG Precip (12–24h)</div>
        <div class="kpi-value">{today['precip_mm']:.2f} mm</div>
        <div class="kpi-sub">{sub}</div></div>""", unsafe_allow_html=True)
with col2:
    sub = delta_str(today["mslp_hpa"], prev.get("mslp_hpa", float("nan")), unit="hPa")
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">MSLP</div>
        <div class="kpi-value">{today['mslp_hpa']:.1f} hPa</div>
        <div class="kpi-sub">{sub}</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">7-Day Total</div>
        <div class="kpi-value">{last_7:.1f} mm</div>
        <div class="kpi-sub">rolling sum</div></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">30-Day Total</div>
        <div class="kpi-value">{last_30:.1f} mm</div>
        <div class="kpi-sub">rolling sum</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Map + Zone bar
left, right = st.columns([3, 2])
with left:
    st.markdown('<div class="section-header">Forecast Map</div>', unsafe_allow_html=True)
    map_path = latest_map()
    if map_path:
        st.image(map_path, use_container_width=True)
    else:
        st.info("Map not yet generated.")

with right:
    st.markdown('<div class="section-header">Zone Breakdown — Today</div>', unsafe_allow_html=True)
    st.plotly_chart(bar_zones(df), use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="section-header">MSLP Trend</div>', unsafe_allow_html=True)
    window = st.selectbox("Window", [7, 14, 30, 60, 90], index=1, label_visibility="collapsed")
    st.plotly_chart(chart_mslp(df, window), use_container_width=True, config={"displayModeBar": False})

# Precip time series
st.markdown('<div class="section-header">Precipitation by Zone</div>', unsafe_allow_html=True)
st.plotly_chart(chart_precip(df, window), use_container_width=True, config={"displayModeBar": False})

# Raw table toggle
with st.expander("Raw Data"):
    disp = df.copy()
    disp["date"] = disp["date"].dt.strftime("%d %b %Y")
    st.dataframe(disp.sort_values("date", ascending=False).reset_index(drop=True),
                 use_container_width=True, height=300)

st.markdown(f"""
<div style="text-align:center; margin-top:30px; color:#2d3748; font-size:10px;">
    Source: ECMWF Open Data · CC-BY-4.0 · Last updated {last_date}
</div>""", unsafe_allow_html=True)
