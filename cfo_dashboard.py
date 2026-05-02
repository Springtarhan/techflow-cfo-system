
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title = "TechFlow CFO Intelligence System",
    page_icon  = "📊",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── Custom CSS ─────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #FAFAFA; }
    .block-container { padding-top: 1rem; }
    h1 { color: #1F3864; font-family: Arial; }
    h2 { color: #1F3864; font-family: Arial; }
    h3 { color: #1F3864; font-family: Arial; }
    .metric-card {
        background: #1F3864;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        color: white;
    }
    .metric-label {
        font-size: 11px;
        color: #AABBDD;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: white;
        margin: 5px 0;
    }
    .metric-delta {
        font-size: 13px;
        color: #AABBDD;
    }
    .stSelectbox label { color: #1F3864; font-weight: bold; }
    .stSlider label    { color: #1F3864; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── Colours ────────────────────────────────────────────────
COLOURS = {
    "EMEA"     : "#1F3864",
    "LATAM"    : "#C62828",
    "North_Am" : "#2E7D32",
    "APAC"     : "#E65100",
    "Forecast" : "#2E7D32",
    "Actual"   : "#1F3864",
    "CI"       : "rgba(46,125,50,0.12)",
}

# ══════════════════════════════════════════════════════════
#   DATA LOADING
# ══════════════════════════════════════════════════════════

@st.cache_data
def load_data(path):
    df = pd.read_excel(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

# ── Find the Excel file ────────────────────────────────────
import os, glob

# Search common locations
search_paths = [
    "/content/drive/MyDrive/TechFlow_CFO_System/data/output/forecast_results_2026.xlsx",
    "./forecast_results_2026.xlsx",
]
data_file = None
for p in search_paths:
    if os.path.exists(p):
        data_file = p
        break

if data_file is None:
    st.error("forecast_results_2026.xlsx not found. "
             "Check the file path.")
    st.stop()

df = load_data(data_file)

# ── Split actuals and forecasts ────────────────────────────
actuals   = df[df["Type"] == "Actual"].copy()
forecasts = df[df["Type"] == "Forecast"].copy()
regions   = sorted(df["Region"].unique().tolist())

# ══════════════════════════════════════════════════════════
#   SIDEBAR NAVIGATION + ASSUMPTIONS
# ══════════════════════════════════════════════════════════

st.sidebar.markdown("""
<div style="background:#1F3864; padding:15px;
            border-radius:8px; margin-bottom:20px">
    <h3 style="color:#FFFFFF; margin:0; font-size:16px">
        📊 TechFlow Solutions
    </h3>
    <p style="color:#AABBDD; margin:5px 0 0 0;
              font-size:12px">
        CFO Intelligence System
    </p>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigation",
    ["Executive Scorecard",
     "Regional Diagnostic",
     "Forecast View",
     "Model Governance"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Assumptions")

# ── Global assumption sliders ──────────────────────────────
rev_adj = st.sidebar.slider(
    "Revenue Growth Adjustment (%)",
    min_value = -20,
    max_value =  20,
    value     =   0,
    step      =   1,
    help      = "Adjust 2026 forecast revenue up or down",
)

opex_adj = st.sidebar.slider(
    "OpEx Reduction Target (%)",
    min_value = -20,
    max_value =  20,
    value     =   0,
    step      =   1,
    help      = "Positive = OpEx reduction vs forecast",
)

inflation = st.sidebar.slider(
    "Inflation Adjustment (%)",
    min_value = 0,
    max_value = 10,
    value     = 0,
    step      = 1,
    help      = "Applied to OpEx as cost pressure",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Region Filter")
selected_regions = st.sidebar.multiselect(
    "Select Regions",
    options  = regions,
    default  = regions,
)

# ── Apply adjustments to forecast ─────────────────────────
fc_adj = forecasts.copy()
fc_adj["Revenue"]    = fc_adj["Revenue"] * (
    1 + rev_adj / 100)
fc_adj["Total_OpEx"] = fc_adj["Total_OpEx"] * (
    1 - opex_adj / 100) * (1 + inflation / 100)
fc_adj["Operating_Income"] = (
    fc_adj["Revenue"] * 0.62 - fc_adj["Total_OpEx"])
fc_adj["Operating_Margin"] = (
    fc_adj["Operating_Income"] / fc_adj["Revenue"])

if fc_adj.get("CI_Lower_Revenue") is not None:
    fc_adj["CI_Lower_Revenue"] = (
        fc_adj["CI_Lower_Revenue"] * (1 + rev_adj / 100))
    fc_adj["CI_Upper_Revenue"] = (
        fc_adj["CI_Upper_Revenue"] * (1 + rev_adj / 100))

# ── Filter to selected regions ─────────────────────────────
act_f = actuals[actuals["Region"].isin(selected_regions)]
fc_f  = fc_adj[fc_adj["Region"].isin(selected_regions)]

# ══════════════════════════════════════════════════════════
#   PAGE 1 — EXECUTIVE SCORECARD
# ══════════════════════════════════════════════════════════

if page == "Executive Scorecard":

    st.markdown(
        "## TechFlow Solutions &nbsp;·&nbsp; "
        "Executive Scorecard 2026")
    st.markdown(
        "*Adjust sliders in the sidebar to stress-test "
        "assumptions in real time*")

    if rev_adj != 0 or opex_adj != 0 or inflation != 0:
        st.info(
            f"⚙️ Active adjustments: "
            f"Revenue {rev_adj:+d}% | "
            f"OpEx reduction {opex_adj:+d}% | "
            f"Inflation {inflation:+d}%"
        )

    # ── KPI calculations ───────────────────────────────────
    fc_2026_rev    = fc_f["Revenue"].sum()
    fc_2026_opex   = fc_f["Total_OpEx"].sum()
    fc_2026_oi     = fc_f["Operating_Income"].sum()
    fc_2026_margin = fc_2026_oi / fc_2026_rev                      if fc_2026_rev > 0 else 0

    act_rev_total  = act_f["Revenue"].sum()
    act_opex_total = act_f["Total_OpEx"].sum()
    act_oi_total   = act_f["Operating_Income"].sum()                      if "Operating_Income" in act_f else 0
    act_margin     = (act_oi_total / act_rev_total
                      if act_rev_total > 0 else 0)

    # Annualise actuals (24 months → 12 month equivalent)
    act_rev_annual  = act_rev_total  / 2
    act_opex_annual = act_opex_total / 2
    act_oi_annual   = act_oi_total   / 2

    rev_growth    = ((fc_2026_rev - act_rev_annual)
                     / act_rev_annual
                     if act_rev_annual > 0 else 0)
    opex_change   = ((fc_2026_opex - act_opex_annual)
                     / act_opex_annual
                     if act_opex_annual > 0 else 0)
    margin_change = fc_2026_margin - act_margin

    # ── KPI tiles ──────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">
                2026 Forecast Revenue</div>
            <div class="metric-value">
                ${fc_2026_rev/1e6:.1f}M</div>
            <div class="metric-delta">
                {rev_growth:+.1%} vs prior year</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        opex_color = ("#FF6B6B" if fc_2026_opex /
                      fc_2026_rev > 0.40
                      else "#FFD93D"
                      if fc_2026_opex / fc_2026_rev > 0.32
                      else "#6BCB77")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">
                2026 Forecast OpEx</div>
            <div class="metric-value">
                ${fc_2026_opex/1e6:.1f}M</div>
            <div class="metric-delta"
                 style="color:{opex_color}">
                {fc_2026_opex/fc_2026_rev:.1%} of Revenue
            </div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">
                2026 Operating Income</div>
            <div class="metric-value">
                ${fc_2026_oi/1e6:.1f}M</div>
            <div class="metric-delta">
                vs ${act_oi_annual/1e6:.1f}M prior yr
            </div>
        </div>""", unsafe_allow_html=True)

    with c4:
        m_color = ("#6BCB77" if fc_2026_margin > 0.20
                   else "#FFD93D"
                   if fc_2026_margin > 0.10
                   else "#FF6B6B")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">
                Operating Margin</div>
            <div class="metric-value"
                 style="color:{m_color}">
                {fc_2026_margin:.1%}</div>
            <div class="metric-delta">
                {margin_change:+.1%} vs prior year</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Revenue bridge chart ───────────────────────────────
    st.markdown("### Revenue & Margin Bridge — 2025 → 2026")

    bridge_dims   = selected_regions
    act_by_region = (act_f.groupby("Region")["Revenue"]
                     .sum() / 2)
    fc_by_region  = fc_f.groupby("Region")["Revenue"].sum()

    fig_bridge = go.Figure()

    for dim in bridge_dims:
        a = act_by_region.get(dim, 0) / 1e6
        f = fc_by_region.get(dim, 0)  / 1e6
        color = COLOURS.get(dim, "#555")

        fig_bridge.add_trace(go.Bar(
            name       = dim,
            x          = [f"Prior Yr<br>{dim}",
                           f"2026 FC<br>{dim}"],
            y          = [a, f],
            marker     = dict(color=color),
            text       = [f"${a:.1f}M", f"${f:.1f}M"],
            textposition= "outside",
            textfont   = dict(size=11),
            showlegend = True,
        ))

    fig_bridge.update_layout(
        height        = 350,
        plot_bgcolor  = "#FFFFFF",
        paper_bgcolor = "#FFFFFF",
        barmode       = "group",
        legend        = dict(
            orientation="h", y=-0.20,
            xanchor="center", x=0.5),
        margin        = dict(t=20, b=60, l=60, r=20),
        yaxis         = dict(
            tickprefix="$", ticksuffix="M",
            showgrid=True, gridcolor="#F0F0F0"),
        xaxis         = dict(showgrid=False),
        font          = dict(family="Arial", size=11),
    )
    st.plotly_chart(fig_bridge, use_container_width=True)

    # ── Region scorecard table ─────────────────────────────
    st.markdown("### 2026 Regional Scorecard")

    tbl_rows = []
    for dim in selected_regions:
        fc_dim   = fc_f[fc_f["Region"] == dim]
        act_dim  = act_f[act_f["Region"] == dim]
        rev_fc   = fc_dim["Revenue"].sum()
        opex_fc  = fc_dim["Total_OpEx"].sum()
        oi_fc    = fc_dim["Operating_Income"].sum()
        margin   = oi_fc / rev_fc if rev_fc > 0 else 0
        rev_act  = act_dim["Revenue"].sum() / 2
        rev_gr   = ((rev_fc - rev_act) / rev_act
                    if rev_act > 0 else 0)
        or_ratio = opex_fc / rev_fc if rev_fc > 0 else 0
        alert    = ("🔴 Alert" if or_ratio > 0.40
                    else "🟡 Watch" if or_ratio > 0.32
                    else "🟢 Healthy")
        tbl_rows.append({
            "Region"          : dim,
            "2026 Revenue"    : f"${rev_fc/1e6:.1f}M",
            "2026 OpEx"       : f"${opex_fc/1e6:.1f}M",
            "OpEx/Rev"        : f"{or_ratio:.1%}",
            "Op Margin"       : f"{margin:.1%}",
            "Rev Growth"      : f"{rev_gr:+.1%}",
            "Status"          : alert,
        })

    tbl_df = pd.DataFrame(tbl_rows)
    st.dataframe(tbl_df, use_container_width=True,
                 hide_index=True)

# ══════════════════════════════════════════════════════════
#   PAGE 2 — REGIONAL DIAGNOSTIC
# ══════════════════════════════════════════════════════════

elif page == "Regional Diagnostic":

    st.markdown(
        "## TechFlow Solutions &nbsp;·&nbsp; "
        "Regional Diagnostic")
    st.markdown(
        "*OpEx-to-Revenue ratio trend — "
        "the margin compression detector*")

    # ── OpEx ratio trend ───────────────────────────────────
    fig_diag = go.Figure()

    for dim in selected_regions:
        sub = (actuals[actuals["Region"] == dim]
               .sort_values("Date"))
        ratio = sub["Total_OpEx"] / sub["Revenue"]
        color = COLOURS.get(dim, "#555")

        fig_diag.add_trace(go.Scatter(
            x             = sub["Date"],
            y             = ratio,
            name          = dim,
            mode          = "lines+markers",
            line          = dict(color=color, width=2.5),
            marker        = dict(size=5),
            hovertemplate = (
                f"<b>{dim}</b><br>"
                f"%{{x|%b %Y}}<br>"
                f"OpEx/Rev: %{{y:.1%}}"
                f"<extra></extra>"),
        ))

    # 40% alert zone
    fig_diag.add_hline(
        y         = 0.40,
        line      = dict(color="#C62828",
                         width=1.5, dash="dash"),
        annotation_text     = "⚠️ 40% Alert Threshold",
        annotation_position = "right",
        annotation_font     = dict(
            color="#C62828", size=11),
    )

    fig_diag.update_layout(
        title = dict(
            text    = "<b>OpEx-to-Revenue Ratio by Region</b>"
                      "<br><sup>Rising = margin compression | "
                      "Red dashed = CFO alert zone</sup>",
            font    = dict(size=15, color="#1F3864"),
            x=0, xanchor="left",
        ),
        height        = 420,
        plot_bgcolor  = "#FFFFFF",
        paper_bgcolor = "#FFFFFF",
        yaxis         = dict(
            tickformat = ".0%",
            showgrid   = True,
            gridcolor  = "#F0F0F0",
            title      = "OpEx as % of Revenue",
        ),
        xaxis         = dict(
            showgrid   = True,
            gridcolor  = "#F0F0F0",
            tickformat = "%b %y",
        ),
        legend        = dict(
            orientation="h", y=-0.18,
            xanchor="center", x=0.5),
        font          = dict(family="Arial", size=11),
        margin        = dict(t=80, b=70, l=70, r=40),
    )
    st.plotly_chart(fig_diag, use_container_width=True)

    # ── Diagnostic table ───────────────────────────────────
    st.markdown("### Diagnostic Summary")
    diag_rows = []
    for dim in selected_regions:
        sub   = (actuals[actuals["Region"] == dim]
                 .sort_values("Date"))
        ratio = sub["Total_OpEx"] / sub["Revenue"]
        start = ratio.iloc[0]
        end   = ratio.iloc[-1]
        delta = end - start
        slope = np.polyfit(range(len(ratio)),
                           ratio, 1)[0]

        if slope > 0.003:
            urgency = "🔴 HIGH"
        elif slope > 0.001:
            urgency = "🟡 MEDIUM"
        else:
            urgency = "🟢 LOW"

        diag_rows.append({
            "Region"       : dim,
            "Jan 2024"     : f"{start:.1%}",
            "Dec 2025"     : f"{end:.1%}",
            "Change"       : f"{delta:+.1%}",
            "Trend Slope"  : f"{slope*100:+.3f}pp/mo",
            "Urgency"      : urgency,
            "Alert Zone"   : "YES 🔴" if end > 0.40
                             else "NO ✅",
        })

    st.dataframe(
        pd.DataFrame(diag_rows),
        use_container_width=True,
        hide_index=True,
    )

    # ── Revenue vs OpEx 2x2 ────────────────────────────────
    st.markdown("### Revenue vs OpEx — 24-Month History")

    n_regions = len(selected_regions)
    cols_n    = min(2, n_regions)
    rows_n    = (n_regions + 1) // 2

    fig_2x2 = make_subplots(
        rows               = max(rows_n, 1),
        cols               = cols_n,
        subplot_titles     = selected_regions,
        vertical_spacing   = 0.18,
        horizontal_spacing = 0.10,
    )

    for idx, dim in enumerate(selected_regions):
        row = idx // 2 + 1
        col = idx %  2 + 1
        sub = (actuals[actuals["Region"] == dim]
               .sort_values("Date"))
        color = COLOURS.get(dim, "#555")

        fig_2x2.add_trace(go.Scatter(
            x          = sub["Date"],
            y          = sub["Revenue"] / 1e6,
            name       = "Revenue",
            line       = dict(color=color, width=2),
            showlegend = (idx == 0),
            legendgroup= "Revenue",
            hovertemplate="$%{y:.2f}M<extra>Revenue</extra>",
        ), row=row, col=col)

        fig_2x2.add_trace(go.Scatter(
            x          = sub["Date"],
            y          = sub["Total_OpEx"] / 1e6,
            name       = "Total OpEx",
            line       = dict(color="#C62828",
                              width=2, dash="dot"),
            showlegend = (idx == 0),
            legendgroup= "OpEx",
            hovertemplate="$%{y:.2f}M<extra>OpEx</extra>",
        ), row=row, col=col)

    fig_2x2.update_layout(
        height        = 480,
        plot_bgcolor  = "#FFFFFF",
        paper_bgcolor = "#FFFFFF",
        font          = dict(family="Arial", size=11),
        margin        = dict(t=60, b=80, l=60, r=40),
        legend        = dict(
            orientation="h", y=-0.18,
            xanchor="center", x=0.5),
    )
    fig_2x2.update_xaxes(
        tickformat="%b %y", tickangle=-30,
        showgrid=True, gridcolor="#F0F0F0")
    fig_2x2.update_yaxes(
        tickprefix="$", ticksuffix="M",
        showgrid=True, gridcolor="#F0F0F0")

    st.plotly_chart(fig_2x2, use_container_width=True)

# ══════════════════════════════════════════════════════════
#   PAGE 3 — FORECAST VIEW
# ══════════════════════════════════════════════════════════

elif page == "Forecast View":

    st.markdown(
        "## TechFlow Solutions &nbsp;·&nbsp; "
        "2026 Forecast View")
    st.markdown(
        "*Actuals Jan 2024 – Dec 2025 | "
        "Forecast Jan – Dec 2026 | "
        "Adjust assumptions in sidebar*")

    if rev_adj != 0 or opex_adj != 0 or inflation != 0:
        st.info(
            f"⚙️ Adjusted forecast: "
            f"Revenue {rev_adj:+d}% | "
            f"OpEx reduction {opex_adj:+d}% | "
            f"Inflation {inflation:+d}%"
        )

    # ── Combined actuals + forecast chart ─────────────────
    n_regions = len(selected_regions)
    cols_n    = min(2, n_regions)
    rows_n    = (n_regions + 1) // 2

    fig_fc = make_subplots(
        rows               = max(rows_n, 1),
        cols               = cols_n,
        subplot_titles     = selected_regions,
        vertical_spacing   = 0.18,
        horizontal_spacing = 0.10,
    )

    for idx, dim in enumerate(selected_regions):
        row   = idx // 2 + 1
        col   = idx %  2 + 1
        color = COLOURS.get(dim, "#555")

        # Actuals
        act_dim = (actuals[actuals["Region"] == dim]
                   .sort_values("Date"))
        fig_fc.add_trace(go.Scatter(
            x             = act_dim["Date"],
            y             = act_dim["Revenue"] / 1e6,
            name          = "Actuals",
            mode          = "lines",
            line          = dict(color=color, width=2.5),
            showlegend    = (idx == 0),
            legendgroup   = "Actuals",
            hovertemplate = (
                f"<b>{dim}</b><br>"
                f"%{{x|%b %Y}}<br>"
                f"Actual: $%{{y:.2f}}M"
                f"<extra></extra>"),
        ), row=row, col=col)

        # Forecast
        fc_dim = (fc_f[fc_f["Region"] == dim]
                  .sort_values("Date"))
        if len(fc_dim) > 0:
            fig_fc.add_trace(go.Scatter(
                x             = fc_dim["Date"],
                y             = fc_dim["Revenue"] / 1e6,
                name          = "Forecast",
                mode          = "lines",
                line          = dict(
                    color="#2E7D32", width=2.5,
                    dash="dash"),
                showlegend    = (idx == 0),
                legendgroup   = "Forecast",
                hovertemplate = (
                    f"<b>{dim}</b><br>"
                    f"%{{x|%b %Y}}<br>"
                    f"Forecast: $%{{y:.2f}}M"
                    f"<extra></extra>"),
            ), row=row, col=col)

            # CI band
            if ("CI_Lower_Revenue" in fc_dim.columns and
                    fc_dim["CI_Lower_Revenue"].notna().any()):
                fig_fc.add_trace(go.Scatter(
                    x          = pd.concat([
                        fc_dim["Date"],
                        fc_dim["Date"][::-1]]),
                    y          = pd.concat([
                        fc_dim["CI_Upper_Revenue"] / 1e6,
                        fc_dim["CI_Lower_Revenue"][::-1]
                        / 1e6]),
                    fill       = "toself",
                    fillcolor  = "rgba(46,125,50,0.12)",
                    line       = dict(
                        color="rgba(0,0,0,0)"),
                    showlegend = (idx == 0),
                    name       = "80% CI",
                    legendgroup= "CI",
                    hoverinfo  = "skip",
                ), row=row, col=col)

        # Divider line
        fig_fc.add_vline(
            x    = "2026-01-01",
            line = dict(color="#AAAAAA",
                        width=1, dash="dot"),
            row=row, col=col,
        )

    fig_fc.update_layout(
        height        = 560,
        plot_bgcolor  = "#FFFFFF",
        paper_bgcolor = "#FFFFFF",
        font          = dict(family="Arial", size=11),
        margin        = dict(t=60, b=90, l=60, r=40),
        legend        = dict(
            orientation="h", y=-0.18,
            xanchor="center", x=0.5),
    )
    fig_fc.update_xaxes(
        tickformat="%b %y", tickangle=-30,
        showgrid=True, gridcolor="#F0F0F0")
    fig_fc.update_yaxes(
        tickprefix="$", ticksuffix="M",
        showgrid=True, gridcolor="#F0F0F0")

    st.plotly_chart(fig_fc, use_container_width=True)

    # ── Monthly forecast table ─────────────────────────────
    st.markdown("### Monthly Forecast Detail")
    region_sel = st.selectbox(
        "Select Region", selected_regions)

    fc_tbl = (fc_f[fc_f["Region"] == region_sel]
              .sort_values("Date")[[
                  "Date", "Revenue",
                  "Total_OpEx",
                  "Operating_Income",
                  "Operating_Margin"
              ]].copy())

    fc_tbl["Date"]             = fc_tbl["Date"].dt.strftime(
        "%b %Y")
    fc_tbl["Revenue"]          = fc_tbl["Revenue"].apply(
        lambda x: f"${x/1e6:.2f}M")
    fc_tbl["Total_OpEx"]       = fc_tbl["Total_OpEx"].apply(
        lambda x: f"${x/1e6:.2f}M")
    fc_tbl["Operating_Income"] = fc_tbl[
        "Operating_Income"].apply(
        lambda x: f"${x/1e6:.2f}M")
    fc_tbl["Operating_Margin"] = fc_tbl[
        "Operating_Margin"].apply(
        lambda x: f"{x:.1%}")

    fc_tbl.columns = ["Month", "Revenue",
                      "Total OpEx",
                      "Operating Income",
                      "Op Margin"]
    st.dataframe(fc_tbl, use_container_width=True,
                 hide_index=True)

# ══════════════════════════════════════════════════════════
#   PAGE 4 — MODEL GOVERNANCE
# ══════════════════════════════════════════════════════════

elif page == "Model Governance":

    st.markdown(
        "## TechFlow Solutions &nbsp;·&nbsp; "
        "Model Governance")
    st.markdown(
        "*Evidence-based model selection — "
        "accuracy vs interpretability*")

    # ── Governance summary ─────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Primary Model</div>
            <div class="metric-value"
                 style="font-size:20px">
                Holt-Winters</div>
            <div class="metric-delta">
                Validated on holdout test</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Shadow Model</div>
            <div class="metric-value"
                 style="font-size:20px">Prophet</div>
            <div class="metric-delta">
                Divergence monitoring active</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">
                Governance Threshold</div>
            <div class="metric-value"
                 style="font-size:20px">5%</div>
            <div class="metric-delta">
                MAPE gap to trigger review</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Model comparison metrics ───────────────────────────
    st.markdown("### Holdout Validation Results "
                "(Jul – Dec 2025)")

    metrics_data = {
        "Region"    : ["EMEA","EMEA","LATAM","LATAM",
                        "North_Am","North_Am","APAC","APAC"],
        "Target"    : ["Revenue","Total_OpEx"] * 4,
        "HW MAPE"   : ["2.3%","3.2%","6.3%","7.5%",
                        "6.2%","6.0%","0.8%","0.0%"],
        "Prophet MAPE": ["4.0%","9.6%","10.5%","9.2%",
                          "57.9%","0.6%","11.6%","2.3%"],
        "HW RMSE"   : ["$68K","$28K","$65K","$30K",
                        "$269K","$75K","$9K","$1K"],
        "Winner"    : ["HW","HW","HW","HW",
                        "HW","Prophet","HW","HW"],
    }
    metrics_df = pd.DataFrame(metrics_data)
    st.dataframe(metrics_df, use_container_width=True,
                 hide_index=True)

    # ── Trade-off argument ─────────────────────────────────
    st.markdown("### Model Trade-Off Governance Argument")

    st.markdown("""
    <div style="background:#F5F5F5; padding:20px;
                border-radius:8px;
                border-left:4px solid #1F3864;
                font-family:Arial; font-size:14px;
                line-height:1.7">

    <b>QUESTION:</b> Which forecasting model should be used
    for the TechFlow 2026 forecast?<br><br>

    <b>EVIDENCE:</b> Both Holt-Winters and Prophet were
    trained on 18 months and evaluated on a 6-month holdout
    test across 4 regions and 2 targets (8 series).<br><br>

    <b>RESULTS:</b><br>
    — Holt-Winters average MAPE: <b>4.0%</b><br>
    — Prophet average MAPE: <b>12.7%</b>
    (severely inflated by North_Am 57.9% error)<br>
    — Holt-Winters wins: <b>7 of 8 series</b><br><br>

    <b>NORTH_AM FINDING:</b> Prophet produced a 57.9% error
    on North_Am Revenue versus Holt-Winters 6.2%.
    Prophet's changepoint detection found a false structural
    break in the training data and extrapolated an incorrect
    trajectory. This demonstrates that model complexity does
    not guarantee accuracy on short training histories.<br><br>

    <b>DECISION: Holt-Winters is the PRIMARY model.</b><br><br>

    <b>RATIONALE:</b> Holt-Winters achieves lower average MAPE
    AND wins on interpretability. Its trend and seasonal
    components can be explained in plain English to any finance
    professional. Prophet runs as a shadow model — when the
    two diverge by more than 5% in future months, that
    divergence flags a data signal requiring investigation.<br><br>

    <b>GOVERNANCE RULE:</b> Holt-Winters is the board-facing
    model. Prophet divergence greater than 5% triggers an
    audit flag — not an automatic model switch.

    </div>
    """, unsafe_allow_html=True)

    # ── Scalability section ────────────────────────────────
    st.markdown("### Scalability Assessment")

    scale_data = {
        "Scenario"      : [
            "Double months (48 months history)",
            "Double regions (8 regions)",
            "Double cost categories (20 GL lines)",
            "Enterprise scale (500K+ rows)",
        ],
        "Impact"        : [
            "Forecast improves — more data",
            "Auto-handled via CONFIG dimension_values",
            "Auto-handled via column_map in CONFIG",
            "pandas bottleneck — needs Polars or SQL",
        ],
        "Action Required": [
            "None — pipeline handles automatically",
            "Add 4 region names to CONFIG only",
            "Add column names to CONFIG only",
            "Migrate ingestion layer to database backend",
        ],
        "Risk"          : [
            "🟢 None",
            "🟢 None",
            "🟢 None",
            "🟡 Medium — architecture change required",
        ],
    }
    st.dataframe(
        pd.DataFrame(scale_data),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("""
    <div style="background:#E8EAF6; padding:15px;
                border-radius:8px; margin-top:10px;
                border-left:4px solid #3949AB;
                font-size:13px">
    <b>Current prototype validated for mid-market scale
    (up to ~500K rows).</b><br>
    For enterprise scale, the ingestion and transformation
    layer would migrate to a database-backed architecture
    while the forecasting and visualisation layers
    remain identical. The CONFIG-driven design means
    no forecast or dashboard code changes are required
    — only the data connection layer changes.
    </div>
    """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#AAAAAA; "
    "font-size:12px'>"
    "TechFlow Solutions · CFO Intelligence System · "
    "Mastery Level · "
    "Built with Holt-Winters primary model · "
    "Prophet shadow model</p>",
    unsafe_allow_html=True,
)
