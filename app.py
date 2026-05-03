from datetime import date, datetime, timedelta
import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='Biorritmos exactos y luna', layout='wide')
PHASE_EMOJI={'Luna nueva':'●','Cuarto creciente':'◐','Luna llena':'○','Cuarto menguante':'◑'}
CYCLES={'Físico':23,'Emocional':28,'Intelectual':33}


def julian_day(dt: datetime) -> float:
    y,m=dt.year,dt.month
    d=dt.day+(dt.hour+dt.minute/60+dt.second/3600)/24
    if m<=2:
        y-=1
        m+=12
    a=y//100
    b=2-a+a//4
    return int(365.25*(y+4716))+int(30.6001*(m+1))+d+b-1524.5


def moon_phase_name(dt: datetime) -> str:
    synodic_month=29.53058867
    known_new_moon=2451550.1
    age=(julian_day(dt)-known_new_moon)%synodic_month
    if age<1.84566 or age>=27.68493:
        return 'Luna nueva'
    if age<9.22831:
        return 'Cuarto creciente'
    if age<16.61096:
        return 'Luna llena'
    return 'Cuarto menguante'


def days_lived(birth_date: date, current_date: date) -> int:
    return (current_date-birth_date).days


def cycle_position(days: int, period: int):
    quotient = days / period
    whole = math.floor(quotient)
    frac = quotient - whole
    day_in_cycle = frac * period
    return quotient, whole, frac, day_in_cycle


def exact_percent(days: int, period: int) -> float:
    return 100 * math.sin(2 * math.pi * days / period)


def visual_percent(days: int, period: int) -> float:
    frac = (days / period) % 1.0
    if frac < 0.25:
        y = -1 + 4 * (frac / 0.25) ** 2
    elif frac < 0.5:
        t = (frac - 0.25) / 0.25
        y = 0.0 + 0.95 * (1 - (1 - t) ** 1.6)
    elif frac < 0.75:
        t = (frac - 0.5) / 0.25
        y = 0.95 - 0.95 * (t ** 0.8)
    else:
        t = (frac - 0.75) / 0.25
        y = -1.0 * (t ** 0.55)
    return 100 * y


def build_df(birth_date: date, start_date: date, horizon_days: int) -> pd.DataFrame:
    rows=[]
    for offset in range(horizon_days+1):
        current = start_date + timedelta(days=offset)
        lived = days_lived(birth_date, current)
        qf,wf,ff,df = cycle_position(lived, CYCLES['Físico'])
        qe,we,fe,de = cycle_position(lived, CYCLES['Emocional'])
        qi,wi,fi,di = cycle_position(lived, CYCLES['Intelectual'])
        pf = exact_percent(lived, CYCLES['Físico'])
        pe = exact_percent(lived, CYCLES['Emocional'])
        pi = exact_percent(lived, CYCLES['Intelectual'])
        vf = visual_percent(lived, CYCLES['Físico'])
        ve = visual_percent(lived, CYCLES['Emocional'])
        vi = visual_percent(lived, CYCLES['Intelectual'])
        balance = (pf + pe + pi) / 3
        state = 'Bueno' if balance >= 35 else 'Bajo' if balance <= -35 else 'Neutro'
        rows.append({
            'fecha': current,
            'dias_vividos': lived,
            'fisico_cociente': qf, 'emocional_cociente': qe, 'intelectual_cociente': qi,
            'fisico_fraccion': ff, 'emocional_fraccion': fe, 'intelectual_fraccion': fi,
            'fisico_dia_ciclo': df, 'emocional_dia_ciclo': de, 'intelectual_dia_ciclo': di,
            'fisico_pct': pf, 'emocional_pct': pe, 'intelectual_pct': pi,
            'fisico_vis': vf, 'emocional_vis': ve, 'intelectual_vis': vi,
            'balance': balance, 'estado': state,
            'luna': moon_phase_name(datetime.combine(current, datetime.min.time()))
        })
    return pd.DataFrame(rows)


def indicator(v: float) -> str:
    return '▲' if v >= 35 else '▼' if v <= -35 else '•'


st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.hero {padding: 1rem 1.2rem; border: 1px solid rgba(120,120,120,.18); border-radius: 18px; background: linear-gradient(180deg, rgba(255,255,255,.65), rgba(255,255,255,.28));}
.mini {font-size: .9rem; opacity: .78}
.metric-card {padding: .9rem 1rem; border-radius: 16px; border: 1px solid rgba(120,120,120,.18); background: rgba(250,250,250,.55)}
.chip {display:inline-block; padding:.25rem .6rem; border-radius:999px; margin:.15rem .2rem .15rem 0; border:1px solid rgba(120,120,120,.2); font-size:.82rem}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='hero'><h1 style='margin:0'>Biorritmos exactos y calendario lunar</h1><div class='mini'>Los porcentajes teóricos se calculan estrictamente con días vividos y ciclos de 23, 28 y 33 días. La curva mostrada puede suavizarse sólo como representación visual.</div></div>", unsafe_allow_html=True)

with st.sidebar:
    st.subheader('Configuración')
    birth_date = st.date_input('Fecha de nacimiento', value=date(1990,11,15), format='DD/MM/YYYY')
    consult_date = st.date_input('Día de consulta', value=date(2026,5,3), format='DD/MM/YYYY')
    weeks = st.slider('Semanas a mostrar', min_value=2, max_value=8, value=6)
    curve_mode = st.radio('Curva del gráfico', ['Teórica exacta', 'Visual aproximada'], index=1)
    st.caption('La tabla y las métricas usan siempre el cálculo exacto. Sólo la forma de la curva puede cambiar.')

df = build_df(birth_date, consult_date, horizon_days=weeks*7)
today = df.iloc[0]
age_years = consult_date.year - birth_date.year - ((consult_date.month, consult_date.day) < (birth_date.month, birth_date.day))

st.subheader('Resultado del día')
colA, colB, colC, colD = st.columns(4)
colA.markdown(f"<div class='metric-card'><div class='mini'>Días vividos</div><div style='font-size:2rem;font-weight:700'>{int(today['dias_vividos']):,}</div><div>{age_years} años</div></div>", unsafe_allow_html=True)
for col, key, label in [(colB,'fisico_pct','Físico'), (colC,'emocional_pct','Emocional'), (colD,'intelectual_pct','Intelectual')]:
    val = float(today[key])
    desc = 'Positivo' if val > 0 else 'Negativo' if val < 0 else 'Cero'
    col.markdown(f"<div class='metric-card'><div class='mini'>{label}</div><div style='font-size:2rem;font-weight:700'>{val:.1f}%</div><div>{indicator(val)} {desc}</div></div>", unsafe_allow_html=True)

st.markdown(f"<div class='chip'>{PHASE_EMOJI[today['luna']]} {today['luna']}</div>", unsafe_allow_html=True)

st.subheader('Ciclos calculados')
calc_df = pd.DataFrame([
    {'Ritmo':'Físico','Cálculo':f"{int(today['dias_vividos'])} / 23",'Valor':f"{today['fisico_cociente']:.3f}",'Parte decimal':f"{today['fisico_fraccion']:.3f}",'Día de ciclo':f"{today['fisico_dia_ciclo']:.1f}",'% teórico':f"{today['fisico_pct']:.1f}%"},
    {'Ritmo':'Emocional','Cálculo':f"{int(today['dias_vividos'])} / 28",'Valor':f"{today['emocional_cociente']:.3f}",'Parte decimal':f"{today['emocional_fraccion']:.3f}",'Día de ciclo':f"{today['emocional_dia_ciclo']:.1f}",'% teórico':f"{today['emocional_pct']:.1f}%"},
    {'Ritmo':'Intelectual','Cálculo':f"{int(today['dias_vividos'])} / 33",'Valor':f"{today['intelectual_cociente']:.3f}",'Parte decimal':f"{today['intelectual_fraccion']:.3f}",'Día de ciclo':f"{today['intelectual_dia_ciclo']:.1f}",'% teórico':f"{today['intelectual_pct']:.1f}%"},
])
st.dataframe(calc_df, use_container_width=True, hide_index=True)

st.subheader('Gráfico de evolución')
fig = go.Figure()
if curve_mode == 'Teórica exacta':
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['fisico_pct'], mode='lines+markers', name='Físico', line=dict(width=3)))
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['emocional_pct'], mode='lines+markers', name='Emocional', line=dict(width=2, dash='dot')))
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['intelectual_pct'], mode='lines+markers', name='Intelectual', line=dict(width=2, dash='dash')))
else:
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['fisico_vis'], mode='lines+markers', name='Físico (visual)', line=dict(width=3)))
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['emocional_vis'], mode='lines+markers', name='Emocional (visual)', line=dict(width=2, dash='dot')))
    fig.add_trace(go.Scatter(x=df['fecha'], y=df['intelectual_vis'], mode='lines+markers', name='Intelectual (visual)', line=dict(width=2, dash='dash')))
fig.add_hline(y=0, line_dash='dash', line_color='rgba(120,120,120,.5)')
fig.update_layout(title='Próximas semanas', height=520, hovermode='x unified', legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5), margin=dict(l=20, r=20, t=60, b=20))
fig.update_yaxes(title='Porcentaje', range=[-105, 105])
fig.update_xaxes(title='Fecha')
st.plotly_chart(fig, use_container_width=True)

st.subheader('Próximos días')
preview = df[['fecha','fisico_pct','emocional_pct','intelectual_pct','estado','luna']].copy()
preview['fecha'] = pd.to_datetime(preview['fecha']).dt.strftime('%d/%m/%Y')
preview['fisico_pct'] = preview['fisico_pct'].map(lambda x: f'{x:.1f}%')
preview['emocional_pct'] = preview['emocional_pct'].map(lambda x: f'{x:.1f}%')
preview['intelectual_pct'] = preview['intelectual_pct'].map(lambda x: f'{x:.1f}%')
preview.columns = ['Fecha','Físico','Emocional','Intelectual','Estado','Luna']
st.dataframe(preview, use_container_width=True, hide_index=True)

st.subheader('Calendario lunar minimalista')
moon_df = df[['fecha','luna']].copy()
moon_df['etiqueta'] = moon_df['luna'].map(lambda x: f"{PHASE_EMOJI[x]} {x}")
moon_df['semana'] = ((pd.to_datetime(moon_df['fecha']) - pd.to_datetime(moon_df['fecha']).min()).dt.days // 7) + 1
for week, chunk in moon_df.groupby('semana'):
    labels = ' · '.join([f"{pd.to_datetime(r.fecha).strftime('%d %b')}: {r.etiqueta}" for r in chunk.itertuples() if pd.to_datetime(r.fecha).day_name() in ['Monday','Thursday','Sunday']])
    st.markdown(f"**Semana {week}** — {labels}")

st.caption('Cálculo exacto: días vividos / periodo y porcentaje sinusoidal. Visualización: exacta o aproximada.')
