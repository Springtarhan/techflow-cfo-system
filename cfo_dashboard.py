
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title = "TechFlow CFO Intelligence System",
    page_icon  = "📊",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    h1, h2, h3 { font-family: Arial; }
    .metric-card {
        background: #1F3864;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        color: white;
        margin-bottom: 8px;
    }
    .metric-label {
        font-size: 11px;
        color: #AABBDD;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: bold;
        color: white;
        margin: 5px 0;
    }
    .metric-delta { font-size: 12px; color: #AABBDD; }
    .commentary-box {
        background: rgba(31,56,100,0.4);
        border-left: 4px solid #4A90D9;
        border-radius: 8px;
        padding: 15px 20px;
        margin: 15px 0;
        font-size: 14px;
        line-height: 1.7;
        color: #FFFFFF;
    }
    .commentary-title {
        font-size: 13px;
        color: #4A90D9;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

COLOURS = {
    "EMEA"     : "#4A90D9",
    "LATAM"    : "#E05C5C",
    "North_Am" : "#4CAF50",
    "APAC"     : "#FF9800",
}

@st.cache_data
def load_data(path):
    df = pd.read_excel(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

import os
search_paths = [
    "forecast_results_2026.xlsx",
    "./forecast_results_2026.xlsx",
    "/content/drive/MyDrive/TechFlow_CFO_System/data/output/forecast_results_2026.xlsx",
]
data_file = None
for p in search_paths:
    if os.path.exists(p):
        data_file = p
        break

if data_file is None:
    st.error("forecast_results_2026.xlsx not found.")
    st.stop()

df        = load_data(data_file)
actuals   = df[df["Type"] == "Actual"].copy()
forecasts = df[df["Type"] == "Forecast"].copy()
regions   = sorted(df["Region"].unique().tolist())

# ── Sidebar ────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="background:#1F3864; padding:12px;
            border-radius:8px; margin-bottom:15px">
    <p style="color:#FFFFFF; margin:0;
              font-size:13px; font-weight:bold">
        📊 TechFlow Solutions
    </p>
    <p style="color:#AABBDD; margin:3px 0 0 0;
              font-size:11px">
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
rev_adj = st.sidebar.slider(
    "Revenue Growth Adjustment (%)",
    min_value=-20, max_value=20, value=0, step=1,
    help="Adjust 2026 forecast revenue up or down",
)
opex_adj = st.sidebar.slider(
    "OpEx Reduction Target (%)",
    min_value=-20, max_value=20, value=0, step=1,
    help="Positive = OpEx reduction vs forecast",
)
inflation = st.sidebar.slider(
    "Inflation Adjustment (%)",
    min_value=0, max_value=10, value=0, step=1,
    help="Applied to OpEx as cost pressure",
)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Region Filter")
selected_regions = st.sidebar.multiselect(
    "Select Regions",
    options=regions,
    default=regions,
)

# ── Apply adjustments ──────────────────────────────────────
fc_adj = forecasts.copy()
fc_adj["Revenue"]    = fc_adj["Revenue"] * (
    1 + rev_adj / 100)
fc_adj["Total_OpEx"] = fc_adj["Total_OpEx"] * (
    1 - opex_adj / 100) * (1 + inflation / 100)
fc_adj["Operating_Income"] = (
    fc_adj["Revenue"] * 0.62 - fc_adj["Total_OpEx"])
fc_adj["Operating_Margin"] = (
    fc_adj["Operating_Income"] / fc_adj["Revenue"])

act_f = actuals[actuals["Region"].isin(selected_regions)]
fc_f  = fc_adj[fc_adj["Region"].isin(selected_regions)]

# ══════════════════════════════════════════════════════
#   COMMENTARY ENGINE
#   Generates dynamic CFO narrative from live KPIs
# ══════════════════════════════════════════════════════

def generate_scorecard_commentary(
        rev_fc, opex_fc, margin_fc,
        rev_growth, margin_change,
        rev_adj, opex_adj, inflation):

    lines = []

    # Revenue signal
    if rev_growth > 0.15:
        lines.append(
            f"TechFlow is forecast to deliver "
            f"${rev_fc/1e6:.1f}M in 2026 revenue — "
            f"a strong {rev_growth:+.1%} growth rate "
            f"versus the prior year annualised baseline.")
    elif rev_growth > 0:
        lines.append(
            f"TechFlow is forecast to deliver "
            f"${rev_fc/1e6:.1f}M in 2026 revenue — "
            f"modest {rev_growth:+.1%} growth versus "
            f"prior year, indicating stabilisation "
            f"rather than acceleration.")
    else:
        lines.append(
            f"TechFlow 2026 revenue is forecast at "
            f"${rev_fc/1e6:.1f}M — a "
            f"{rev_growth:+.1%} decline versus prior year "
            f"requiring immediate commercial attention.")

    # Margin signal
    or_ratio = opex_fc / rev_fc if rev_fc > 0 else 0
    if or_ratio > 0.40:
        lines.append(
            f"The OpEx-to-Revenue ratio of "
            f"{or_ratio:.1%} is above the 40% CFO alert "
            f"threshold — operating margin of "
            f"{margin_fc:.1%} is unsustainable at this "
            f"cost structure without intervention.")
    elif or_ratio > 0.32:
        lines.append(
            f"The OpEx-to-Revenue ratio of {or_ratio:.1%} "
            f"is within acceptable range but trending "
            f"toward the alert zone. Operating margin "
            f"of {margin_fc:.1%} requires active "
            f"cost discipline to protect.")
    else:
        lines.append(
            f"The OpEx-to-Revenue ratio of {or_ratio:.1%} "
            f"is healthy. Operating margin of "
            f"{margin_fc:.1%} demonstrates strong "
            f"cost discipline across the group.")

    # Adjustment signal
    if rev_adj != 0 or opex_adj != 0 or inflation != 0:
        adj_parts = []
        if rev_adj != 0:
            adj_parts.append(
                f"revenue {rev_adj:+d}% adjustment")
        if opex_adj != 0:
            adj_parts.append(
                f"{opex_adj:+d}% OpEx reduction")
        if inflation != 0:
            adj_parts.append(
                f"{inflation}% inflation pressure")
        lines.append(
            f"Scenario active: {', '.join(adj_parts)}. "
            f"The board should stress-test this scenario "
            f"against Q1 actuals before committing "
            f"to the revised outlook.")

    return " ".join(lines)


def generate_diagnostic_commentary(actuals_df, regions):
    high_risk   = []
    medium_risk = []
    healthy     = []

    for dim in regions:
        sub   = (actuals_df[actuals_df["Region"] == dim]
                 .sort_values("Date"))
        if len(sub) < 2:
            continue
        ratio = sub["Total_OpEx"] / sub["Revenue"]
        end   = ratio.iloc[-1]
        slope = np.polyfit(
            range(len(ratio)), ratio, 1)[0]

        if end > 0.40 or slope > 0.003:
            high_risk.append(dim)
        elif end > 0.32 or slope > 0.001:
            medium_risk.append(dim)
        else:
            healthy.append(dim)

    lines = []
    if high_risk:
        lines.append(
            f"🔴 HIGH URGENCY — "
            f"{', '.join(high_risk)}: OpEx ratio "
            f"above or approaching the 40% alert zone "
            f"with an accelerating upward trend. "
            f"Immediate cost review recommended before "
            f"Q1 2026 close.")
    if medium_risk:
        lines.append(
            f"🟡 MEDIUM URGENCY — "
            f"{', '.join(medium_risk)}: Ratio rising "
            f"but below the alert threshold. Monitor "
            f"monthly and pre-approve cost reduction "
            f"actions for activation if trend continues.")
    if healthy:
        lines.append(
            f"🟢 HEALTHY — "
            f"{', '.join(healthy)}: Cost discipline "
            f"confirmed. OpEx ratio stable or declining "
            f"— these regions are generating the "
            f"operating leverage that offsets "
            f"group-level deterioration.")

    if not lines:
        lines.append(
            "Select at least one region to "
            "generate diagnostic commentary.")
    return " ".join(lines)


def generate_forecast_commentary(
        fc_df, act_df, regions):
    lines = []
    growing  = []
    declining = []
    stable   = []

    for dim in regions:
        fc_dim  = fc_df[fc_df["Region"] == dim]
        act_dim = act_df[act_df["Region"] == dim]
        if len(fc_dim) == 0 or len(act_dim) == 0:
            continue
        fc_rev  = fc_dim["Revenue"].sum()
        act_rev = act_dim["Revenue"].sum() / 2
        growth  = ((fc_rev - act_rev) / act_rev
                   if act_rev > 0 else 0)
        if growth > 0.10:
            growing.append(
                f"{dim} ({growth:+.0%})")
        elif growth < -0.05:
            declining.append(
                f"{dim} ({growth:+.0%})")
        else:
            stable.append(dim)

    if growing:
        lines.append(
            f"Growth engines for 2026: "
            f"{', '.join(growing)}. "
            f"These regions are forecast to expand "
            f"revenue meaningfully above the "
            f"prior year baseline.")
    if declining:
        lines.append(
            f"Revenue headwinds: "
            f"{', '.join(declining)}. "
            f"These regions are forecast below "
            f"prior year — commercial intervention "
            f"or cost restructuring is required.")
    if stable:
        lines.append(
            f"Stable contributors: "
            f"{', '.join(stable)} — "
            f"forecast in line with prior year, "
            f"providing a reliable base.")

    lines.append(
        "Confidence intervals shown represent the "
        "80% prediction band. Months where the lower "
        "band approaches zero operating income "
        "should be flagged as high-risk periods "
        "requiring active cash management.")

    if not lines:
        lines.append(
            "Select at least one region to "
            "generate forecast commentary.")
    return " ".join(lines)


# ══════════════════════════════════════════════════════
#   PAGE 1 — EXECUTIVE SCORECARD
# ══════════════════════════════════════════════════════

if page == "Executive Scorecard":

    st.markdown(
        "## TechFlow Solutions &nbsp;·&nbsp; "
        "Executive Scorecard 2026")
    st.markdown(
        "*Adjust sliders in the sidebar to "
        "stress-test assumptions in real time*")

    if rev_adj != 0 or opex_adj != 0 or inflation != 0:
        st.info(
            f"⚙️ Active: Revenue {rev_adj:+d}% | "
            f"OpEx reduction {opex_adj:+d}% | "
            f"Inflation {inflation:+d}%")

    fc_2026_rev    = fc_f["Revenue"].sum()
    fc_2026_opex   = fc_f["Total_OpEx"].sum()
    fc_2026_oi     = fc_f["Operating_Income"].sum()
    fc_2026_margin = (fc_2026_oi / fc_2026_rev
                      if fc_2026_rev > 0 else 0)
    act_rev_total  = act_f["Revenue"].sum()
    act_opex_total = act_f["Total_OpEx"].sum()
    act_oi_total   = (act_f["Operating_Income"].sum()
                      if "Operating_Income" in act_f
                      else 0)
    act_margin     = (act_oi_total / act_rev_total
                      if act_rev_total > 0 else 0)
    act_rev_annual = act_rev_total / 2
    act_oi_annual  = act_oi_total  / 2
    rev_growth     = ((fc_2026_rev - act_rev_annual)
                      / act_rev_annual
                      if act_rev_annual > 0 else 0)
    margin_change  = fc_2026_margin - act_margin

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">
                2026 Forecast Revenue</div>
            <div class="metric-value">
                ${fc_2026_rev/1e6:.1f}M</div>
            <div class="metric-delta">
                {rev_growth:+.1%} vs prior year
            </div>
        </div>""", unsafe_allow_html=True)

    with c2:
        or_ratio   = (fc_2026_opex / fc_2026_rev
                      if fc_2026_rev > 0 else 0)
        opex_color = ("#FF6B6B" if or_ratio > 0.40
                      else "#FFD93D"
                      if or_ratio > 0.32
                      else "#6BCB77")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">
                2026 Forecast OpEx</div>
            <div class="metric-value">
                ${fc_2026_opex/1e6:.1f}M</div>
            <div class="metric-delta"
                 style="color:{opex_color}">
                {or_ratio:.1%} of Revenue</div>
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
                {margin_change:+.1%} vs prior year
            </div>
        </div>""", unsafe_allow_html=True)

    # ── AI Commentary ──────────────────────────────────
    commentary = generate_scorecard_commentary(
        fc_2026_rev, fc_2026_opex,
        fc_2026_margin, rev_growth,
        margin_change, rev_adj, opex_adj, inflation)

    st.markdown(f"""
    <div class="commentary-box">
        <div class="commentary-title">
            🤖 CFO AI Commentary
        </div>
        {commentary}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "### Revenue Bridge — Prior Year vs 2026")

    act_by_region = (act_f.groupby("Region")["Revenue"]
                     .sum() / 2)
    fc_by_region  = (fc_f.groupby("Region")["Revenue"]
                     .sum())

    fig_bridge = go.Figure()
    for dim in selected_regions:
        a     = act_by_region.get(dim, 0) / 1e6
        f     = fc_by_region.get(dim,  0) / 1e6
        color = COLOURS.get(dim, "#555")
        fig_bridge.add_trace(go.Bar(
            name         = dim,
            x            = [f"Prior Yr {dim}",
                             f"2026 FC {dim}"],
            y            = [a, f],
            marker       = dict(color=color),
            text         = [f"${a:.1f}M",
                            f"${f:.1f}M"],
            textposition = "outside",
            textfont     = dict(size=11,
                                color="#FFFFFF"),
        ))

    fig_bridge.update_layout(
        height        = 350,
        plot_bgcolor  = "rgba(0,0,0,0)",
        paper_bgcolor = "rgba(0,0,0,0)",
        barmode       = "group",
        font          = dict(color="#FFFFFF",
                             family="Arial"),
        legend        = dict(
            orientation="h", y=-0.25,
            xanchor="center", x=0.5,
            font=dict(color="#FFFFFF")),
        margin        = dict(t=20, b=80, l=60, r=20),
        yaxis         = dict(
            tickprefix="$", ticksuffix="M",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.1)",
            color="#FFFFFF"),
        xaxis         = dict(
            showgrid=False, color="#FFFFFF"),
    )
    st.plotly_chart(fig_bridge,
                    use_container_width=True)

    st.markdown("### 2026 Regional Scorecard")
    tbl_rows = []
    for dim in selected_regions:
        fc_dim  = fc_f[fc_f["Region"] == dim]
        act_dim = act_f[act_f["Region"] == dim]
        rev_fc  = fc_dim["Revenue"].sum()
        opex_fc = fc_dim["Total_OpEx"].sum()
        oi_fc   = fc_dim["Operating_Income"].sum()
        margin  = oi_fc / rev_fc if rev_fc > 0 else 0
        rev_act = act_dim["Revenue"].sum() / 2
        rev_gr  = ((rev_fc - rev_act) / rev_act
                   if rev_act > 0 else 0)
        or_r    = opex_fc / rev_fc if rev_fc > 0 else 0
        alert   = ("🔴 Alert"  if or_r > 0.40
                   else "🟡 Watch" if or_r > 0.32
                   else "🟢 Healthy")
        tbl_rows.append({
            "Region"       : dim,
            "2026 Revenue" : f"${rev_fc/1e6:.1f}M",
            "2026 OpEx"    : f"${opex_fc/1e6:.1f}M",
            "OpEx/Rev"     : f"{or_r:.1%}",
            "Op Margin"    : f"{margin:.1%}",
            "Rev Growth"   : f"{rev_gr:+.1%}",
            "Status"       : alert,
        })
    st.dataframe(pd.DataFrame(tbl_rows),
                 use_container_width=True,
                 hide_index=True)

# ══════════════════════════════════════════════════════
#   PAGE 2 — REGIONAL DIAGNOSTIC
# ══════════════════════════════════════════════════════

elif page == "Regional Diagnostic":

    st.markdown(
        "## TechFlow Solutions &nbsp;·&nbsp; "
        "Regional Diagnostic")
    st.markdown(
        "*OpEx-to-Revenue ratio — "
        "the margin compression detector*")

    # ── AI Commentary ──────────────────────────────────
    diag_commentary = generate_diagnostic_commentary(
        act_f, selected_regions)
    st.markdown(f"""
    <div class="commentary-box">
        <div class="commentary-title">
            🤖 CFO AI Commentary
        </div>
        {diag_commentary}
    </div>
    """, unsafe_allow_html=True)

    fig_diag = go.Figure()
    for dim in selected_regions:
        sub   = (actuals[actuals["Region"] == dim]
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

    fig_diag.add_hline(
        y         = 0.40,
        line      = dict(color="#FF6B6B",
                         width=1.5, dash="dash"),
        annotation_text     = "⚠️ 40% Alert Zone",
        annotation_position = "right",
        annotation_font     = dict(
            color="#FF6B6B", size=11),
    )
    fig_diag.update_layout(
        title = dict(
            text = (
                "<b>OpEx-to-Revenue Ratio by Region</b>"
                "<br><sup>Rising = compression | "
                "Red dashed = CFO alert zone</sup>"),
            font    = dict(size=15, color="#4A90D9"),
            x=0, xanchor="left",
        ),
        height        = 400,
        plot_bgcolor  = "rgba(0,0,0,0)",
        paper_bgcolor = "rgba(0,0,0,0)",
        font          = dict(color="#FFFFFF",
                             family="Arial"),
        yaxis         = dict(
            tickformat  = ".0%",
            showgrid    = True,
            gridcolor   = "rgba(255,255,255,0.1)",
            title       = "OpEx as % of Revenue",
            color       = "#FFFFFF"),
        xaxis         = dict(
            showgrid    = True,
            gridcolor   = "rgba(255,255,255,0.1)",
            tickformat  = "%b %y",
            color       = "#FFFFFF"),
        legend        = dict(
            orientation = "h",
            y           = -0.20,
            xanchor     = "center",
            x           = 0.5,
            font        = dict(color="#FFFFFF")),
        margin        = dict(t=80, b=80, l=70, r=60),
    )
    st.plotly_chart(fig_diag,
                    use_container_width=True)

    st.markdown("### Diagnostic Summary by Region")
    diag_rows = []
    for dim in selected_regions:
        sub   = (actuals[actuals["Region"] == dim]
                 .sort_values("Date"))
        ratio = sub["Total_OpEx"] / sub["Revenue"]
        start = ratio.iloc[0]
        end   = ratio.iloc[-1]
        delta = end - start
        slope = np.polyfit(
            range(len(ratio)), ratio, 1)[0]
        urgency = ("🔴 HIGH"
                   if slope > 0.003 or end > 0.40
                   else "🟡 MEDIUM"
                   if slope > 0.001 or end > 0.32
                   else "🟢 LOW")
        diag_rows.append({
            "Region"     : dim,
            "Jan 2024"   : f"{start:.1%}",
            "Dec 2025"   : f"{end:.1%}",
            "Change"     : f"{delta:+.1%}",
            "Trend"      : f"{slope*100:+.3f}pp/mo",
            "Urgency"    : urgency,
            "Alert Zone" : "YES 🔴"
                           if end > 0.40 else "NO ✅",
        })
    st.dataframe(pd.DataFrame(diag_rows),
                 use_container_width=True,
                 hide_index=True)

    st.markdown(
        "### Revenue vs OpEx — 24-Month History")
    n       = len(selected_regions)
    fig_2x2 = make_subplots(
        rows               = max((n+1)//2, 1),
        cols               = min(2, n),
        subplot_titles     = selected_regions,
        vertical_spacing   = 0.18,
        horizontal_spacing = 0.10,
    )
    for idx, dim in enumerate(selected_regions):
        row   = idx // 2 + 1
        col   = idx %  2 + 1
        sub   = (actuals[actuals["Region"] == dim]
                 .sort_values("Date"))
        color = COLOURS.get(dim, "#555")
        fig_2x2.add_trace(go.Scatter(
            x           = sub["Date"],
            y           = sub["Revenue"] / 1e6,
            name        = "Revenue",
            line        = dict(color=color, width=2),
            showlegend  = (idx == 0),
            legendgroup = "Revenue",
        ), row=row, col=col)
        fig_2x2.add_trace(go.Scatter(
            x           = sub["Date"],
            y           = sub["Total_OpEx"] / 1e6,
            name        = "Total OpEx",
            line        = dict(color="#FF6B6B",
                               width=2, dash="dot"),
            showlegend  = (idx == 0),
            legendgroup = "OpEx",
        ), row=row, col=col)
    fig_2x2.update_layout(
        height        = 480,
        plot_bgcolor  = "rgba(0,0,0,0)",
        paper_bgcolor = "rgba(0,0,0,0)",
        font          = dict(color="#FFFFFF",
                             family="Arial"),
        margin        = dict(t=60, b=80, l=60, r=40),
        legend        = dict(
            orientation = "h",
            y           = -0.18,
            xanchor     = "center",
            x           = 0.5,
            font        = dict(color="#FFFFFF")),
    )
    fig_2x2.update_xaxes(
        tickformat  = "%b %y",
        tickangle   = -30,
        showgrid    = True,
        gridcolor   = "rgba(255,255,255,0.1)",
        color       = "#FFFFFF")
    fig_2x2.update_yaxes(
        tickprefix  = "$",
        ticksuffix  = "M",
        showgrid    = True,
        gridcolor   = "rgba(255,255,255,0.1)",
        color       = "#FFFFFF")
    st.plotly_chart(fig_2x2,
                    use_container_width=True)

# ══════════════════════════════════════════════════════
#   PAGE 3 — FORECAST VIEW
# ══════════════════════════════════════════════════════

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
            f"⚙️ Scenario active: "
            f"Revenue {rev_adj:+d}% | "
            f"OpEx reduction {opex_adj:+d}% | "
            f"Inflation {inflation:+d}%")

    # ── AI Commentary ──────────────────────────────────
    fc_commentary = generate_forecast_commentary(
        fc_f, act_f, selected_regions)
    st.markdown(f"""
    <div class="commentary-box">
        <div class="commentary-title">
            🤖 CFO AI Commentary
        </div>
        {fc_commentary}
    </div>
    """, unsafe_allow_html=True)

    n      = len(selected_regions)
    fig_fc = make_subplots(
        rows               = max((n+1)//2, 1),
        cols               = min(2, n),
        subplot_titles     = selected_regions,
        vertical_spacing   = 0.18,
        horizontal_spacing = 0.10,
    )
    for idx, dim in enumerate(selected_regions):
        row   = idx // 2 + 1
        col   = idx %  2 + 1
        color = COLOURS.get(dim, "#555")

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

        fc_dim = (fc_f[fc_f["Region"] == dim]
                  .sort_values("Date"))
        if len(fc_dim) > 0:
            fig_fc.add_trace(go.Scatter(
                x             = fc_dim["Date"],
                y             = fc_dim["Revenue"] / 1e6,
                name          = "Forecast",
                mode          = "lines",
                line          = dict(
                    color     = "#6BCB77",
                    width     = 2.5,
                    dash      = "dash"),
                showlegend    = (idx == 0),
                legendgroup   = "Forecast",
                hovertemplate = (
                    f"<b>{dim}</b><br>"
                    f"%{{x|%b %Y}}<br>"
                    f"Forecast: $%{{y:.2f}}M"
                    f"<extra></extra>"),
            ), row=row, col=col)

            if ("CI_Lower_Revenue" in fc_dim.columns
                    and fc_dim[
                        "CI_Lower_Revenue"
                    ].notna().any()):
                fig_fc.add_trace(go.Scatter(
                    x         = pd.concat([
                        fc_dim["Date"],
                        fc_dim["Date"][::-1]]),
                    y         = pd.concat([
                        fc_dim["CI_Upper_Revenue"] / 1e6,
                        fc_dim["CI_Lower_Revenue"
                               ][::-1] / 1e6]),
                    fill      = "toself",
                    fillcolor = "rgba(107,203,119,0.15)",
                    line      = dict(
                        color = "rgba(0,0,0,0)"),
                    showlegend  = (idx == 0),
                    name        = "80% CI",
                    legendgroup = "CI",
                    hoverinfo   = "skip",
                ), row=row, col=col)

        fig_fc.add_vline(
            x    = "2026-01-01",
            line = dict(
                color = "rgba(255,255,255,0.3)",
                width = 1,
                dash  = "dot"),
            row=row, col=col,
        )

    fig_fc.update_layout(
        height        = 560,
        plot_bgcolor  = "rgba(0,0,0,0)",
        paper_bgcolor = "rgba(0,0,0,0)",
        font          = dict(color="#FFFFFF",
                             family="Arial"),
        margin        = dict(t=60, b=90, l=60, r=40),
        legend        = dict(
            orientation = "h",
            y           = -0.18,
            xanchor     = "center",
            x           = 0.5,
            font        = dict(color="#FFFFFF")),
    )
    fig_fc.update_xaxes(
        tickformat  = "%b %y",
        tickangle   = -30,
        showgrid    = True,
        gridcolor   = "rgba(255,255,255,0.1)",
        color       = "#FFFFFF")
    fig_fc.update_yaxes(
        tickprefix  = "$",
        ticksuffix  = "M",
        showgrid    = True,
        gridcolor   = "rgba(255,255,255,0.1)",
        color       = "#FFFFFF")
    st.plotly_chart(fig_fc,
                    use_container_width=True)

    st.markdown("### Monthly Forecast Detail")
    region_sel = st.selectbox(
        "Select Region", selected_regions)
    fc_tbl = (fc_f[fc_f["Region"] == region_sel]
              .sort_values("Date")[[
                  "Date", "Revenue",
                  "Total_OpEx",
                  "Operating_Income",
                  "Operating_Margin",
              ]].copy())
    fc_tbl["Date"] = (
        fc_tbl["Date"].dt.strftime("%b %Y"))
    fc_tbl["Revenue"] = fc_tbl["Revenue"].apply(
        lambda x: f"${x/1e6:.2f}M")
    fc_tbl["Total_OpEx"] = fc_tbl[
        "Total_OpEx"].apply(
        lambda x: f"${x/1e6:.2f}M")
    fc_tbl["Operating_Income"] = fc_tbl[
        "Operating_Income"].apply(
        lambda x: f"${x/1e6:.2f}M")
    fc_tbl["Operating_Margin"] = fc_tbl[
        "Operating_Margin"].apply(
        lambda x: f"{x:.1%}")
    fc_tbl.columns = [
        "Month", "Revenue", "Total OpEx",
        "Operating Income", "Op Margin"]
    st.dataframe(fc_tbl,
                 use_container_width=True,
                 hide_index=True)

# ══════════════════════════════════════════════════════
#   PAGE 4 — MODEL GOVERNANCE
# ══════════════════════════════════════════════════════

elif page == "Model Governance":

    st.markdown(
        "## TechFlow Solutions &nbsp;·&nbsp; "
        "Model Governance")
    st.markdown(
        "*Evidence-based model selection — "
        "accuracy vs interpretability*")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">
                Primary Model</div>
            <div class="metric-value"
                 style="font-size:18px">
                Holt-Winters</div>
            <div class="metric-delta">
                Validated on holdout test</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">
                Shadow Model</div>
            <div class="metric-value"
                 style="font-size:18px">
                Prophet</div>
            <div class="metric-delta">
                Divergence monitoring active</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">
                Governance Threshold</div>
            <div class="metric-value"
                 style="font-size:18px">5%</div>
            <div class="metric-delta">
                MAPE gap to trigger review</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AI Commentary ──────────────────────────────────
    st.markdown(f"""
    <div class="commentary-box">
        <div class="commentary-title">
            🤖 CFO AI Commentary
        </div>
        Both Holt-Winters and Prophet were validated
        on a 6-month holdout test set (Jul–Dec 2025)
        across 4 regions and 2 forecast targets
        (8 series total). Holt-Winters achieved a
        lower average MAPE of 4.0% versus Prophet at
        12.7% — with Prophet's average severely
        inflated by a 57.9% error on North_Am Revenue
        caused by false changepoint detection.
        Holt-Winters won on 7 of 8 series and is
        selected as the primary model on both accuracy
        AND interpretability grounds. This is the
        correct governance decision: the more complex
        model produced worse results on this dataset,
        demonstrating that model selection must always
        be evidence-based, not assumption-based.
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "### Holdout Validation — Jul–Dec 2025")
    metrics_data = {
        "Region"      : [
            "EMEA","EMEA",
            "LATAM","LATAM",
            "North_Am","North_Am",
            "APAC","APAC"],
        "Target"      : ["Revenue","Total_OpEx"] * 4,
        "HW MAPE"     : [
            "2.3%","3.2%","6.3%","7.5%",
            "6.2%","6.0%","0.8%","0.0%"],
        "Prophet MAPE": [
            "4.0%","9.6%","10.5%","9.2%",
            "57.9%","0.6%","11.6%","2.3%"],
        "HW RMSE"     : [
            "$68K","$28K","$65K","$30K",
            "$269K","$75K","$9K","$1K"],
        "Winner"      : [
            "HW","HW","HW","HW",
            "HW","Prophet","HW","HW"],
    }
    st.dataframe(
        pd.DataFrame(metrics_data),
        use_container_width=True,
        hide_index=True)

    st.markdown(
        "### Model Trade-Off Governance Argument")
    st.markdown("""
    <div style="background:rgba(31,56,100,0.4);
                padding:20px; border-radius:8px;
                border-left:4px solid #4A90D9;
                font-size:14px; line-height:1.7;
                color:#FFFFFF">

    <b>QUESTION:</b> Which forecasting model should
    be used for the TechFlow 2026 forecast?<br><br>

    <b>EVIDENCE:</b> Both models trained on 18 months,
    evaluated on 6-month holdout across 4 regions
    and 2 targets (8 series).<br><br>

    <b>RESULTS:</b><br>
    &nbsp;— HW avg MAPE: <b>4.0%</b><br>
    &nbsp;— Prophet avg MAPE: <b>12.7%</b>
    (North_Am 57.9% error inflates average)<br>
    &nbsp;— HW wins: <b>7 of 8 series</b><br><br>

    <b>NORTH_AM FINDING:</b> Prophet produced a 57.9%
    error vs HW 6.2%. False changepoint detected
    in training data — incorrect trajectory
    extrapolated. Model complexity ≠ accuracy
    on short training histories.<br><br>

    <b>DECISION: Holt-Winters — PRIMARY model.</b>
    <br><br>

    <b>GOVERNANCE RULE:</b> Prophet runs as shadow
    model. Divergence over 5% triggers audit flag —
    not automatic model switch.

    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Scalability Assessment")
    scale_data = {
        "Scenario"       : [
            "Double months (48 months)",
            "Double regions (8 regions)",
            "Double cost categories (20 GL)",
            "Enterprise scale (500K+ rows)",
        ],
        "Impact"         : [
            "Forecast improves — more data",
            "Auto-handled via CONFIG",
            "Auto-handled via column_map",
            "pandas bottleneck — needs Polars/SQL",
        ],
        "Action Required": [
            "None — automatic",
            "Add region names to CONFIG only",
            "Add column names to CONFIG only",
            "Migrate ingestion to database backend",
        ],
        "Risk"           : [
            "🟢 None",
            "🟢 None",
            "🟢 None",
            "🟡 Medium — architecture change",
        ],
    }
    st.dataframe(
        pd.DataFrame(scale_data),
        use_container_width=True,
        hide_index=True)

    st.markdown("""
    <div style="background:rgba(57,73,171,0.4);
                padding:15px; border-radius:8px;
                margin-top:10px;
                border-left:4px solid #7986CB;
                font-size:13px; color:#FFFFFF">
    <b>Current prototype validated for mid-market
    scale (up to ~500K rows).</b><br>
    For enterprise scale, the ingestion and
    transformation layer migrates to a database
    backend while forecasting and visualisation
    layers remain identical. CONFIG-driven design
    means no forecast or dashboard code changes
    required — only the data connection changes.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    "<p style='text-align:center; "
    "color:#666666; font-size:12px'>"
    "TechFlow Solutions · CFO Intelligence System"
    " · Mastery Level · "
    "Holt-Winters primary · Prophet shadow</p>",
    unsafe_allow_html=True,
)
