import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import os
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title='TechFlow CFO Intelligence System',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded',
)

st.markdown('''
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
    .agent-box {
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        font-size: 14px;
        line-height: 1.7;
        color: #FFFFFF;
    }
    .agent-a { background: rgba(31,56,100,0.4); border-left: 4px solid #4A90D9; }
    .agent-b { background: rgba(198,40,40,0.2); border-left: 4px solid #FF6B6B; }
    .agent-c { background: rgba(46,125,50,0.2); border-left: 4px solid #6BCB77; }
    .agent-title { font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
</style>
''', unsafe_allow_html=True)

COLOURS = {
    'EMEA'    : '#4A90D9',
    'LATAM'   : '#E05C5C',
    'North_Am': '#4CAF50',
    'APAC'    : '#FF9800',
}

@st.cache_data
def load_data(path):
    df = pd.read_excel(path)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

search_paths = [
    'forecast_results_2026.xlsx',
    './forecast_results_2026.xlsx',
    '/content/drive/MyDrive/TechFlow_CFO_System/data/output/forecast_results_2026.xlsx',
]
data_file = None
for p in search_paths:
    if os.path.exists(p):
        data_file = p
        break
if data_file is None:
    st.error('forecast_results_2026.xlsx not found.')
    st.stop()

df        = load_data(data_file)
actuals   = df[df['Type'] == 'Actual'].copy()
forecasts = df[df['Type'] == 'Forecast'].copy()
regions   = sorted(df['Region'].unique().tolist())

st.sidebar.markdown('''
<div style='background:#1F3864; padding:12px; border-radius:8px; margin-bottom:15px'>
    <p style='color:#FFFFFF; margin:0; font-size:13px; font-weight:bold'>📊 TechFlow Solutions</p>
    <p style='color:#AABBDD; margin:3px 0 0 0; font-size:11px'>CFO Intelligence System</p>
</div>
''', unsafe_allow_html=True)

page = st.sidebar.radio('Navigation', [
    'Executive Scorecard',
    'Regional Diagnostic',
    'Forecast View',
    'Model Governance',
    'Strategic Advisor',
], index=0)

st.sidebar.markdown('---')
st.sidebar.markdown('### ⚙️ Assumptions')
rev_adj = st.sidebar.slider('Revenue Growth Adjustment (%)', -20, 20, 0, 1)
opex_adj = st.sidebar.slider('OpEx Reduction Target (%)', -20, 20, 0, 1)
inflation = st.sidebar.slider('Inflation Adjustment (%)', 0, 10, 0, 1)
st.sidebar.markdown('---')
st.sidebar.markdown('### 🗺️ Region Filter')
selected_regions = st.sidebar.multiselect('Select Regions', options=regions, default=regions)

fc_adj = forecasts.copy()
fc_adj['Revenue']    = fc_adj['Revenue'] * (1 + rev_adj / 100)
fc_adj['Total_OpEx'] = fc_adj['Total_OpEx'] * (1 - opex_adj / 100) * (1 + inflation / 100)
fc_adj['Operating_Income'] = fc_adj['Revenue'] * 0.62 - fc_adj['Total_OpEx']
fc_adj['Operating_Margin'] = fc_adj['Operating_Income'] / fc_adj['Revenue']
act_f = actuals[actuals['Region'].isin(selected_regions)]
fc_f  = fc_adj[fc_adj['Region'].isin(selected_regions)]

def generate_scorecard_commentary(rev_fc, opex_fc, margin_fc, rev_growth, margin_change, rev_adj, opex_adj, inflation):
    parts = []
    if rev_growth > 0.15:
        parts.append(f'TechFlow is forecast to deliver ${rev_fc/1e6:.1f}M in 2026 revenue — strong {rev_growth:+.1%} growth versus prior year.')
    elif rev_growth > 0:
        parts.append(f'TechFlow is forecast to deliver ${rev_fc/1e6:.1f}M in 2026 — modest {rev_growth:+.1%} growth, indicating stabilisation rather than acceleration.')
    else:
        parts.append(f'TechFlow 2026 revenue forecast ${rev_fc/1e6:.1f}M — {rev_growth:+.1%} decline versus prior year requiring immediate commercial attention.')
    or_ratio = opex_fc / rev_fc if rev_fc > 0 else 0
    if or_ratio > 0.40:
        parts.append(f'OpEx ratio {or_ratio:.1%} breaches the 40% CFO alert threshold. Operating margin {margin_fc:.1%} is unsustainable without intervention.')
    elif or_ratio > 0.32:
        parts.append(f'OpEx ratio {or_ratio:.1%} is within range but trending toward the alert zone. Margin {margin_fc:.1%} requires active cost discipline.')
    else:
        parts.append(f'OpEx ratio {or_ratio:.1%} is healthy. Operating margin {margin_fc:.1%} demonstrates strong cost discipline.')
    if rev_adj != 0 or opex_adj != 0 or inflation != 0:
        parts.append(f'Scenario active: Revenue {rev_adj:+d}%, OpEx reduction {opex_adj:+d}%, Inflation {inflation}%. Stress-test against Q1 actuals before committing.')
    return ' '.join(parts)

def generate_diagnostic_commentary(actuals_df, regions):
    high_risk, medium_risk, healthy = [], [], []
    for dim in regions:
        sub = actuals_df[actuals_df['Region'] == dim].sort_values('Date')
        if len(sub) < 2: continue
        ratio = sub['Total_OpEx'] / sub['Revenue']
        end = ratio.iloc[-1]
        slope = np.polyfit(range(len(ratio)), ratio, 1)[0]
        if end > 0.40 or slope > 0.003: high_risk.append(dim)
        elif end > 0.32 or slope > 0.001: medium_risk.append(dim)
        else: healthy.append(dim)
    parts = []
    if high_risk: parts.append(f'🔴 HIGH URGENCY — {", ".join(high_risk)}: OpEx ratio above or approaching 40% alert zone. Immediate cost review recommended.')
    if medium_risk: parts.append(f'🟡 MEDIUM — {", ".join(medium_risk)}: Rising but below threshold. Monitor monthly and pre-approve cost reduction actions.')
    if healthy: parts.append(f'🟢 HEALTHY — {", ".join(healthy)}: Cost discipline confirmed. Stable or declining OpEx ratio.')
    return ' '.join(parts) if parts else 'Select at least one region.'

def generate_forecast_commentary(fc_df, act_df, regions):
    growing, declining, stable = [], [], []
    for dim in regions:
        fc_dim = fc_df[fc_df['Region'] == dim]
        act_dim = act_df[act_df['Region'] == dim]
        if len(fc_dim) == 0 or len(act_dim) == 0: continue
        growth = (fc_dim['Revenue'].sum() - act_dim['Revenue'].sum()/2) / (act_dim['Revenue'].sum()/2)
        if growth > 0.10: growing.append(f'{dim} ({growth:+.0%})')
        elif growth < -0.05: declining.append(f'{dim} ({growth:+.0%})')
        else: stable.append(dim)
    parts = []
    if growing: parts.append(f'Growth engines: {", ".join(growing)}. These regions expand revenue meaningfully above prior year.')
    if declining: parts.append(f'Revenue headwinds: {", ".join(declining)}. Commercial intervention or restructuring required.')
    if stable: parts.append(f'Stable: {", ".join(stable)} — in line with prior year, providing reliable base.')
    parts.append('80% confidence intervals shown. Months where lower band approaches zero operating income are high-risk periods.')
    return ' '.join(parts)

def build_data_summary(actuals_df, forecasts_df):
    out = ['TECHFLOW SOLUTIONS — FORECAST DATA SUMMARY', '='*50]
    out.append('\nACTUALS (Jan 2024 – Dec 2025):')
    for dim in sorted(actuals_df['Region'].unique()):
        sub = actuals_df[actuals_df['Region'] == dim]
        rev = sub['Revenue'].sum() / 1e6
        opex = sub['Total_OpEx'].sum() / 1e6
        ratio = opex / rev if rev > 0 else 0
        s = sub.sort_values('Date')
        or_start = s['Total_OpEx'].iloc[0] / s['Revenue'].iloc[0]
        or_end   = s['Total_OpEx'].iloc[-1] / s['Revenue'].iloc[-1]
        out.append(f'  {dim}: Rev ${rev:.1f}M | OpEx ${opex:.1f}M | Ratio {ratio:.1%} | Trend {or_start:.1%}→{or_end:.1%}')
    out.append('\nFORECAST 2026:')
    for dim in sorted(forecasts_df['Region'].unique()):
        sub = forecasts_df[forecasts_df['Region'] == dim]
        rev = sub['Revenue'].sum() / 1e6
        opex = sub['Total_OpEx'].sum() / 1e6
        ratio = opex / rev if rev > 0 else 0
        margin = sub['Operating_Margin'].mean() if 'Operating_Margin' in sub else 0
        out.append(f'  {dim}: Rev ${rev:.1f}M | OpEx ${opex:.1f}M | Ratio {ratio:.1%} | Margin {margin:.1%}')
    g_rev = forecasts_df['Revenue'].sum() / 1e6
    g_opex = forecasts_df['Total_OpEx'].sum() / 1e6
    act_rev = actuals_df['Revenue'].sum() / 1e6
    out.append(f'\nGROUP 2026: Rev ${g_rev:.1f}M | OpEx ${g_opex:.1f}M | Ratio {g_opex/g_rev:.1%}')
    out.append(f'PRIOR YEAR ANNUALISED: ${act_rev/2:.1f}M | GROWTH: {(g_rev/(act_rev/2)-1):+.1%}')
    out.append('PRIMARY MODEL: Holt-Winters (avg MAPE 4.0%)')
    out.append('SHADOW MODEL: Prophet (avg MAPE 12.7%, North_Am error 57.9%)')
    out.append('CFO ALERT THRESHOLD: OpEx/Revenue > 40%')
    return '\n'.join(out)

def call_anthropic(system_prompt, user_prompt, api_key, max_tokens=2500):
    headers = {'x-api-key': api_key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}
    payload = {'model': 'claude-opus-4-5', 'max_tokens': max_tokens, 'system': system_prompt, 'messages': [{'role': 'user', 'content': user_prompt}]}
    resp = requests.post('https://api.anthropic.com/v1/messages', headers=headers, json=payload, timeout=60)
    if resp.status_code == 200:
        import re
        text = resp.json()['content'][0]['text']
        text = re.sub(r'#{1,3}\s+(.*?)(<br>|$)', r'<b>\1</b>\2', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        text = text.replace('---', '<hr>')
        return text
    return f'API Error {resp.status_code}: {resp.text[:200]}'

if page == 'Executive Scorecard':
    st.markdown('## TechFlow Solutions &nbsp;·&nbsp; Executive Scorecard 2026')
    st.markdown('*Adjust sliders in the sidebar to stress-test assumptions in real time*')
    if rev_adj != 0 or opex_adj != 0 or inflation != 0:
        st.info(f'⚙️ Active: Revenue {rev_adj:+d}% | OpEx reduction {opex_adj:+d}% | Inflation {inflation:+d}%')
    fc_2026_rev   = fc_f['Revenue'].sum()
    fc_2026_opex  = fc_f['Total_OpEx'].sum()
    fc_2026_oi    = fc_f['Operating_Income'].sum()
    fc_2026_margin= fc_2026_oi / fc_2026_rev if fc_2026_rev > 0 else 0
    act_rev_total = act_f['Revenue'].sum()
    act_oi_total  = act_f['Operating_Income'].sum() if 'Operating_Income' in act_f else 0
    act_rev_annual= act_rev_total / 2
    act_oi_annual = act_oi_total  / 2
    act_margin    = act_oi_total / act_rev_total if act_rev_total > 0 else 0
    rev_growth    = (fc_2026_rev - act_rev_annual) / act_rev_annual if act_rev_annual > 0 else 0
    margin_change = fc_2026_margin - act_margin
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'''<div class="metric-card"><div class="metric-label">2026 Forecast Revenue</div><div class="metric-value">${fc_2026_rev/1e6:.1f}M</div><div class="metric-delta">{rev_growth:+.1%} vs prior year</div></div>''', unsafe_allow_html=True)
    with c2:
        or_ratio = fc_2026_opex / fc_2026_rev if fc_2026_rev > 0 else 0
        oc = '#FF6B6B' if or_ratio > 0.40 else '#FFD93D' if or_ratio > 0.32 else '#6BCB77'
        st.markdown(f'''<div class="metric-card"><div class="metric-label">2026 Forecast OpEx</div><div class="metric-value">${fc_2026_opex/1e6:.1f}M</div><div class="metric-delta" style="color:{oc}">{or_ratio:.1%} of Revenue</div></div>''', unsafe_allow_html=True)
    with c3:
        st.markdown(f'''<div class="metric-card"><div class="metric-label">2026 Operating Income</div><div class="metric-value">${fc_2026_oi/1e6:.1f}M</div><div class="metric-delta">vs ${act_oi_annual/1e6:.1f}M prior yr</div></div>''', unsafe_allow_html=True)
    with c4:
        mc = '#6BCB77' if fc_2026_margin > 0.20 else '#FFD93D' if fc_2026_margin > 0.10 else '#FF6B6B'
        st.markdown(f'''<div class="metric-card"><div class="metric-label">Operating Margin</div><div class="metric-value" style="color:{mc}">{fc_2026_margin:.1%}</div><div class="metric-delta">{margin_change:+.1%} vs prior year</div></div>''', unsafe_allow_html=True)
    commentary = generate_scorecard_commentary(fc_2026_rev, fc_2026_opex, fc_2026_margin, rev_growth, margin_change, rev_adj, opex_adj, inflation)
    st.markdown(f'<div class="commentary-box"><div class="commentary-title">🤖 CFO AI Commentary</div>{commentary}</div>', unsafe_allow_html=True)
    st.markdown('### Revenue Bridge — Prior Year vs 2026')
    abr = act_f.groupby('Region')['Revenue'].sum() / 2
    fbr = fc_f.groupby('Region')['Revenue'].sum()
    fig = go.Figure()
    for dim in selected_regions:
        a = abr.get(dim, 0) / 1e6
        f = fbr.get(dim, 0) / 1e6
        fig.add_trace(go.Bar(name=dim, x=[f'Prior Yr {dim}', f'2026 FC {dim}'], y=[a, f], marker=dict(color=COLOURS.get(dim,'#555')), text=[f'${a:.1f}M', f'${f:.1f}M'], textposition='outside', textfont=dict(color='#FFFFFF')))
    fig.update_layout(height=350, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', barmode='group', font=dict(color='#FFFFFF', family='Arial'), legend=dict(orientation='h', y=-0.25, xanchor='center', x=0.5, font=dict(color='#FFFFFF')), margin=dict(t=20,b=80,l=60,r=20), yaxis=dict(tickprefix='$', ticksuffix='M', showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='#FFFFFF'), xaxis=dict(showgrid=False, color='#FFFFFF'))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('### 2026 Regional Scorecard')
    rows = []
    for dim in selected_regions:
        fd = fc_f[fc_f['Region']==dim]; ad = act_f[act_f['Region']==dim]
        rv = fd['Revenue'].sum(); ox = fd['Total_OpEx'].sum(); oi = fd['Operating_Income'].sum()
        mg = oi/rv if rv>0 else 0; ra = ad['Revenue'].sum()/2; rg = (rv-ra)/ra if ra>0 else 0; orr = ox/rv if rv>0 else 0
        al = '🔴 Alert' if orr>0.40 else '🟡 Watch' if orr>0.32 else '🟢 Healthy'
        rows.append({'Region':dim,'2026 Revenue':f'${rv/1e6:.1f}M','2026 OpEx':f'${ox/1e6:.1f}M','OpEx/Rev':f'{orr:.1%}','Op Margin':f'{mg:.1%}','Rev Growth':f'{rg:+.1%}','Status':al})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == 'Regional Diagnostic':
    st.markdown('## TechFlow Solutions &nbsp;·&nbsp; Regional Diagnostic')
    st.markdown('*OpEx-to-Revenue ratio — the margin compression detector*')
    dc = generate_diagnostic_commentary(act_f, selected_regions)
    st.markdown(f'<div class="commentary-box"><div class="commentary-title">🤖 CFO AI Commentary</div>{dc}</div>', unsafe_allow_html=True)
    fig = go.Figure()
    for dim in selected_regions:
        sub = actuals[actuals['Region']==dim].sort_values('Date')
        ratio = sub['Total_OpEx'] / sub['Revenue']
        fig.add_trace(go.Scatter(x=sub['Date'], y=ratio, name=dim, mode='lines+markers', line=dict(color=COLOURS.get(dim,'#555'), width=2.5), marker=dict(size=5), hovertemplate=f'<b>{dim}</b><br>%{{x|%b %Y}}<br>OpEx/Rev: %{{y:.1%}}<extra></extra>'))
    fig.add_hline(y=0.40, line=dict(color='#FF6B6B', width=1.5, dash='dash'), annotation_text='⚠️ 40% Alert Zone', annotation_position='right', annotation_font=dict(color='#FF6B6B', size=11))
    fig.update_layout(title=dict(text='<b>OpEx-to-Revenue Ratio by Region</b><br><sup>Rising = compression | Red dashed = CFO alert zone</sup>', font=dict(size=15, color='#4A90D9'), x=0, xanchor='left'), height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF', family='Arial'), yaxis=dict(tickformat='.0%', showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='OpEx as % of Revenue', color='#FFFFFF'), xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickformat='%b %y', color='#FFFFFF'), legend=dict(orientation='h', y=-0.20, xanchor='center', x=0.5, font=dict(color='#FFFFFF')), margin=dict(t=80,b=80,l=70,r=60))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('### Diagnostic Summary')
    dr = []
    for dim in selected_regions:
        sub = actuals[actuals['Region']==dim].sort_values('Date')
        ratio = sub['Total_OpEx'] / sub['Revenue']
        start=ratio.iloc[0]; end=ratio.iloc[-1]; delta=end-start
        slope=np.polyfit(range(len(ratio)),ratio,1)[0]
        urg='🔴 HIGH' if slope>0.003 or end>0.40 else '🟡 MEDIUM' if slope>0.001 or end>0.32 else '🟢 LOW'
        dr.append({'Region':dim,'Jan 2024':f'{start:.1%}','Dec 2025':f'{end:.1%}','Change':f'{delta:+.1%}','Trend':f'{slope*100:+.3f}pp/mo','Urgency':urg,'Alert Zone':'YES 🔴' if end>0.40 else 'NO ✅'})
    st.dataframe(pd.DataFrame(dr), use_container_width=True, hide_index=True)
    st.markdown('### Revenue vs OpEx — 24-Month History')
    n=len(selected_regions)
    fig2=make_subplots(rows=max((n+1)//2,1), cols=min(2,n), subplot_titles=selected_regions, vertical_spacing=0.18, horizontal_spacing=0.10)
    for i,dim in enumerate(selected_regions):
        r=i//2+1; c=i%2+1
        sub=actuals[actuals['Region']==dim].sort_values('Date')
        fig2.add_trace(go.Scatter(x=sub['Date'],y=sub['Revenue']/1e6,name='Revenue',line=dict(color=COLOURS.get(dim,'#555'),width=2),showlegend=(i==0),legendgroup='Revenue'),row=r,col=c)
        fig2.add_trace(go.Scatter(x=sub['Date'],y=sub['Total_OpEx']/1e6,name='Total OpEx',line=dict(color='#FF6B6B',width=2,dash='dot'),showlegend=(i==0),legendgroup='OpEx'),row=r,col=c)
    fig2.update_layout(height=480,plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#FFFFFF',family='Arial'),margin=dict(t=60,b=80,l=60,r=40),legend=dict(orientation='h',y=-0.18,xanchor='center',x=0.5,font=dict(color='#FFFFFF')))
    fig2.update_xaxes(tickformat='%b %y',tickangle=-30,showgrid=True,gridcolor='rgba(255,255,255,0.1)',color='#FFFFFF')
    fig2.update_yaxes(tickprefix='$',ticksuffix='M',showgrid=True,gridcolor='rgba(255,255,255,0.1)',color='#FFFFFF')
    st.plotly_chart(fig2, use_container_width=True)

elif page == 'Forecast View':
    st.markdown('## TechFlow Solutions &nbsp;·&nbsp; 2026 Forecast View')
    st.markdown('*Actuals Jan 2024 – Dec 2025 | Forecast Jan – Dec 2026*')
    if rev_adj!=0 or opex_adj!=0 or inflation!=0:
        st.info(f'⚙️ Scenario: Revenue {rev_adj:+d}% | OpEx {opex_adj:+d}% | Inflation {inflation:+d}%')
    fc = generate_forecast_commentary(fc_f, act_f, selected_regions)
    st.markdown(f'<div class="commentary-box"><div class="commentary-title">🤖 CFO AI Commentary</div>{fc}</div>', unsafe_allow_html=True)
    n=len(selected_regions)
    fig=make_subplots(rows=max((n+1)//2,1),cols=min(2,n),subplot_titles=selected_regions,vertical_spacing=0.18,horizontal_spacing=0.10)
    for i,dim in enumerate(selected_regions):
        r=i//2+1; c=i%2+1
        ad=actuals[actuals['Region']==dim].sort_values('Date')
        fig.add_trace(go.Scatter(x=ad['Date'],y=ad['Revenue']/1e6,name='Actuals',mode='lines',line=dict(color=COLOURS.get(dim,'#555'),width=2.5),showlegend=(i==0),legendgroup='Actuals'),row=r,col=c)
        fd=fc_f[fc_f['Region']==dim].sort_values('Date')
        if len(fd)>0:
            fig.add_trace(go.Scatter(x=fd['Date'],y=fd['Revenue']/1e6,name='Forecast',mode='lines',line=dict(color='#6BCB77',width=2.5,dash='dash'),showlegend=(i==0),legendgroup='Forecast'),row=r,col=c)
            if 'CI_Lower_Revenue' in fd.columns and fd['CI_Lower_Revenue'].notna().any():
                fig.add_trace(go.Scatter(x=pd.concat([fd['Date'],fd['Date'][::-1]]),y=pd.concat([fd['CI_Upper_Revenue']/1e6,fd['CI_Lower_Revenue'][::-1]/1e6]),fill='toself',fillcolor='rgba(107,203,119,0.15)',line=dict(color='rgba(0,0,0,0)'),showlegend=(i==0),name='80% CI',legendgroup='CI',hoverinfo='skip'),row=r,col=c)
        fig.add_vline(x='2026-01-01',line=dict(color='rgba(255,255,255,0.3)',width=1,dash='dot'),row=r,col=c)
    fig.update_layout(height=560,plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#FFFFFF',family='Arial'),margin=dict(t=60,b=90,l=60,r=40),legend=dict(orientation='h',y=-0.18,xanchor='center',x=0.5,font=dict(color='#FFFFFF')))
    fig.update_xaxes(tickformat='%b %y',tickangle=-30,showgrid=True,gridcolor='rgba(255,255,255,0.1)',color='#FFFFFF')
    fig.update_yaxes(tickprefix='$',ticksuffix='M',showgrid=True,gridcolor='rgba(255,255,255,0.1)',color='#FFFFFF')
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('### Monthly Forecast Detail')
    rs=st.selectbox('Select Region', selected_regions)
    ft=fc_f[fc_f['Region']==rs].sort_values('Date')[['Date','Revenue','Total_OpEx','Operating_Income','Operating_Margin']].copy()
    ft['Date']=ft['Date'].dt.strftime('%b %Y')
    ft['Revenue']=ft['Revenue'].apply(lambda x:f'${x/1e6:.2f}M')
    ft['Total_OpEx']=ft['Total_OpEx'].apply(lambda x:f'${x/1e6:.2f}M')
    ft['Operating_Income']=ft['Operating_Income'].apply(lambda x:f'${x/1e6:.2f}M')
    ft['Operating_Margin']=ft['Operating_Margin'].apply(lambda x:f'{x:.1%}')
    ft.columns=['Month','Revenue','Total OpEx','Operating Income','Op Margin']
    st.dataframe(ft, use_container_width=True, hide_index=True)

elif page == 'Model Governance':
    st.markdown('## TechFlow Solutions &nbsp;·&nbsp; Model Governance')
    st.markdown('*Evidence-based model selection — accuracy vs interpretability*')
    c1,c2,c3=st.columns(3)
    with c1: st.markdown('<div class="metric-card"><div class="metric-label">Primary Model</div><div class="metric-value" style="font-size:18px">Holt-Winters</div><div class="metric-delta">Validated on holdout test</div></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="metric-card"><div class="metric-label">Shadow Model</div><div class="metric-value" style="font-size:18px">Prophet</div><div class="metric-delta">Divergence monitoring active</div></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="metric-card"><div class="metric-label">Governance Threshold</div><div class="metric-value" style="font-size:18px">5%</div><div class="metric-delta">MAPE gap to trigger review</div></div>', unsafe_allow_html=True)
    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown('<div class="commentary-box"><div class="commentary-title">🤖 CFO AI Commentary</div>Both models validated on 6-month holdout (Jul–Dec 2025) across 4 regions and 2 targets. Holt-Winters avg MAPE 4.0% vs Prophet 12.7%. HW wins 7 of 8 series. North_Am Prophet error 57.9% vs HW 6.2% — false changepoint detected. Model complexity does not guarantee accuracy. Selection must be evidence-based.</div>', unsafe_allow_html=True)
    st.markdown('### Holdout Validation — Jul–Dec 2025')
    md={'Region':['EMEA','EMEA','LATAM','LATAM','North_Am','North_Am','APAC','APAC'],'Target':['Revenue','Total_OpEx']*4,'HW MAPE':['2.3%','3.2%','6.3%','7.5%','6.2%','6.0%','0.8%','0.0%'],'Prophet MAPE':['4.0%','9.6%','10.5%','9.2%','57.9%','0.6%','11.6%','2.3%'],'HW RMSE':['$68K','$28K','$65K','$30K','$269K','$75K','$9K','$1K'],'Winner':['HW','HW','HW','HW','HW','Prophet','HW','HW']}
    st.dataframe(pd.DataFrame(md), use_container_width=True, hide_index=True)
    st.markdown('### Model Trade-Off Governance Argument')
    st.markdown('<div style="background:rgba(31,56,100,0.4);padding:20px;border-radius:8px;border-left:4px solid #4A90D9;font-size:14px;line-height:1.7;color:#FFFFFF"><b>QUESTION:</b> Which model for TechFlow 2026?<br><br><b>RESULTS:</b> HW avg MAPE 4.0% vs Prophet 12.7%. HW wins 7 of 8 series. North_Am Prophet error 57.9% vs HW 6.2% — false changepoint detected.<br><br><b>DECISION: Holt-Winters — PRIMARY model.</b><br><br><b>GOVERNANCE:</b> Prophet runs as shadow model. Divergence over 5% triggers audit flag — not automatic model switch.</div>', unsafe_allow_html=True)
    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown('### Scalability Assessment')
    sd={'Scenario':['Double months (48mo)','Double regions (8)','Double GL lines (20)','Enterprise (500K+ rows)'],'Impact':['Forecast improves','Auto via CONFIG','Auto via column_map','pandas bottleneck'],'Action Required':['None — automatic','Add to CONFIG only','Add to CONFIG only','Migrate to database'],'Risk':['🟢 None','🟢 None','🟢 None','🟡 Medium']}
    st.dataframe(pd.DataFrame(sd), use_container_width=True, hide_index=True)
    st.markdown('<div style="background:rgba(57,73,171,0.4);padding:15px;border-radius:8px;margin-top:10px;border-left:4px solid #7986CB;font-size:13px;color:#FFFFFF"><b>Current prototype validated for mid-market scale (up to ~500K rows).</b> For enterprise scale, ingestion migrates to database backend while forecasting and visualisation layers remain identical. CONFIG-driven design means no forecast or dashboard code changes required.</div>', unsafe_allow_html=True)

elif page == 'Strategic Advisor':
    st.markdown('## TechFlow Solutions &nbsp;·&nbsp; Strategic Advisor Agent')
    st.markdown('*Three-agent AI workflow — Analyst → Skeptic → CFO Memo. Reads live forecast data. No file upload required.*')
    st.markdown('<div style="background:rgba(31,56,100,0.4);padding:15px;border-radius:8px;border-left:4px solid #4A90D9;margin-bottom:20px;color:#FFFFFF;font-size:13px"><b>How this works:</b><br>🔵 <b>Agent A — The Analyst</b> surfaces top 3 findings with specific numbers.<br>🔴 <b>Agent B — The Skeptic</b> challenges each finding and stress-tests assumptions.<br>🟢 <b>Agent C — The CFO Memo Writer</b> synthesises both into a board-ready memo under 300 words.<br><br>Click <b>Generate Strategic Memo</b> to run the full workflow. Takes ~30 seconds.</div>', unsafe_allow_html=True)
    api_key = None
    try: api_key = st.secrets['ANTHROPIC_API_KEY']
    except: pass
    if not api_key:
        st.warning('⚠️ Anthropic API key not configured. Go to Streamlit Cloud → Settings → Secrets and add: ANTHROPIC_API_KEY = sk-ant-...')
        st.stop()
    if st.button('🤖 Generate Strategic Memo', type='primary', use_container_width=True):
        data_summary = build_data_summary(actuals, forecasts)
        sys_prompt = '''You are the TechFlow CFO Intelligence System — a three-agent strategic advisor.
COMPANY: TechFlow Solutions — SaaS, 4 regions: EMEA, LATAM, North_Am, APAC.
CORE PROBLEM: OpEx deterioration hidden beneath stable revenue aggregates.
AGENT A — THE ANALYST: Surface top 3 findings with exact numbers.
AGENT B — THE SKEPTIC: Challenge each Agent A finding directly. What is fragile?
AGENT C — CFO MEMO WRITER: Board-ready memo under 300 words. Include: situation, findings, risks, three time-bound recommended actions, bottom line.
RULES: Only cite numbers from the data. Agent B must genuinely challenge. Every action must be specific and time-bound.'''
        usr_prompt = f'''Run the full three-agent analysis on this TechFlow forecast data.

{data_summary}

Label each section clearly:
AGENT A — THE ANALYST
AGENT B — THE SKEPTIC
AGENT C — CFO STRATEGIC MEMO

Generate all three agents in one response.'''
        with st.spinner('🤖 Running three-agent analysis... ~30 seconds'):
            result = call_anthropic(sys_prompt, usr_prompt, api_key, 2500)
        if 'API Error' in result:
            st.error(result)
        else:
            ru = result.upper()
            a_s = result.upper().find('AGENT A')
            b_s = result.upper().find('AGENT B')
            c_s = result.upper().find('AGENT C')
            if a_s >= 0 and b_s > a_s and c_s > b_s:
                ag_a = result[a_s:b_s].strip()
                ag_b = result[b_s:c_s].strip()
                ag_c = result[c_s:].strip()
            else:
                ag_a = result; ag_b = ''; ag_c = ''
            import re
            def md_to_html(text):
                text = re.sub(r'#{1,3}\s+(.*)', r'<b>\1</b>', text)
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                text = text.replace('---', '<hr style="border-color:rgba(255,255,255,0.2)">')
                text = text.replace(chr(10), '<br>')
                return text
            st.markdown(f'<div class="agent-box agent-a"><div class="agent-title" style="color:#4A90D9">🔵 AGENT A — THE ANALYST</div>{md_to_html(ag_a)}</div>', unsafe_allow_html=True)
            if ag_b: st.markdown(f'<div class="agent-box agent-b"><div class="agent-title" style="color:#FF6B6B">🔴 AGENT B — THE SKEPTIC</div>{md_to_html(ag_b)}</div>', unsafe_allow_html=True)
            if ag_c: st.markdown(f'<div class="agent-box agent-c"><div class="agent-title" style="color:#6BCB77">🟢 AGENT C — CFO STRATEGIC MEMO</div>{md_to_html(ag_c)}</div>', unsafe_allow_html=True)
            memo_html = f'<html><body style="font-family:Arial;padding:40px;max-width:800px;margin:auto"><h1>TechFlow Solutions</h1><h2>CFO Strategic Memo — 2026</h2><hr><h3>Agent A — The Analyst</h3><p>{md_to_html(ag_a)}</p><hr><h3>Agent B — The Skeptic</h3><p>{md_to_html(ag_b)}</p><hr><h3>Agent C — CFO Strategic Memo</h3><p>{md_to_html(ag_c)}</p></body></html>'
            st.download_button(label='📥 Download Full Memo', data=memo_html, file_name='techflow_cfo_memo_2026.html', mime='text/html', use_container_width=True)
            st.success('✅ Strategic memo generated. Download above to save.')

st.markdown('---')
st.markdown('<p style="text-align:center;color:#666666;font-size:12px">TechFlow Solutions · CFO Intelligence System · Mastery Level · Holt-Winters primary · Prophet shadow · Strategic Advisor powered by Claude</p>', unsafe_allow_html=True)