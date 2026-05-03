import math
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Biorritmos y Luna", layout="wide")
PHASE_EMOJI={"Luna nueva":"●","Cuarto creciente":"◐","Luna llena":"○","Cuarto menguante":"◑"}

def julian_day(dt: datetime) -> float:
    y,m=dt.year,dt.month
    d=dt.day+(dt.hour+dt.minute/60+dt.second/3600)/24
    if m<=2:
        y-=1;m+=12
    a=y//100;b=2-a+a//4
    return int(365.25*(y+4716))+int(30.6001*(m+1))+d+b-1524.5

def moon_phase_name(dt: datetime) -> str:
    synodic_month=29.53058867
    known_new_moon=2451550.1
    age=(julian_day(dt)-known_new_moon)%synodic_month
    if age<1.84566 or age>=27.68493:return "Luna nueva"
    if age<9.22831:return "Cuarto creciente"
    if age<16.61096:return "Luna llena"
    return "Cuarto menguante"

def bio_piece(x: float) -> float:
    x=x%1.0
    if x<0.25:return -1+4*(x/0.25)**2
    if x<0.5:
        t=(x-0.25)/0.25
        return 0+0.95*(1-(1-t)**1.8)
    if x<0.75:
        t=(x-0.5)/0.25
        return 0.95-0.95*(t**0.7)
    t=(x-0.75)/0.25
    return 0-1.0*(t**0.55)

def biorhythm_value(days_since_birth: float, period: int) -> float:
    return 100*bio_piece((days_since_birth%period)/period)

def build_df(birth_date: date, start_day: date, horizon_days: int=42) -> pd.DataFrame:
    rows=[]
    for i in range(horizon_days+1):
        current=start_day+timedelta(days=i)
        days=(current-birth_date).days
        fis=biorhythm_value(days,23)
        emo=biorhythm_value(days,28)
        inte=biorhythm_value(days,33)
        score=(fis+emo+inte)/3
        state='Bueno' if score>=35 else 'Bajo' if score<=-35 else 'Neutro'
        rows.append({'fecha':current,'físico':fis,'emocional':emo,'intelectual':inte,'balance':score,'estado':state,'luna':moon_phase_name(datetime.combine(current, datetime.min.time()))})
    return pd.DataFrame(rows)

def indicator(v: float) -> str:
    return '▲' if v>=35 else '▼' if v<=-35 else '•'

st.markdown("""<style>.block-container{padding-top:1.2rem;padding-bottom:2rem}.hero{padding:1rem 1.2rem;border:1px solid rgba(120,120,120,.18);border-radius:18px;background:linear-gradient(180deg,rgba(255,255,255,.55),rgba(255,255,255,.22))}.mini{font-size:.9rem;opacity:.75}.chip{display:inline-block;padding:.25rem .6rem;border-radius:999px;margin:.15rem .2rem .15rem 0;border:1px solid rgba(120,120,120,.2);font-size:.82rem}.metric-card{padding:.9rem 1rem;border-radius:16px;border:1px solid rgba(120,120,120,.18);background:rgba(250,250,250,.55)}</style>""",unsafe_allow_html=True)
st.markdown("<div class='hero'><h1 style='margin:0'>Biorritmos y calendario lunar</h1><div class='mini'>Curva inspirada en la figura aportada: ascensos y descensos por tramos, no sinusoidales.</div></div>",unsafe_allow_html=True)
with st.sidebar:
    st.subheader('Configuración')
    birth_date=st.date_input('Fecha de nacimiento',value=date(1990,1,1),format='DD/MM/YYYY')
    consult_date=st.date_input('Día de consulta',value=date.today(),format='DD/MM/YYYY')
    weeks=st.slider('Semanas a mostrar',min_value=2,max_value=8,value=6)
    st.caption('Modelo visual segmentado para aproximarse al ritmo de la figura de referencia.')

df=build_df(birth_date,consult_date,horizon_days=weeks*7)
today_row=df.iloc[0]
c1,c2,c3,c4=st.columns(4)
for col,key,label in [(c1,'físico','Físico'),(c2,'emocional','Emocional'),(c3,'intelectual','Intelectual'),(c4,'balance','Balance')]:
    val=float(today_row[key])
    desc=today_row['estado'] if key=='balance' else ('Alto' if val>=35 else 'Bajo' if val<=-35 else 'Intermedio')
    col.markdown(f"<div class='metric-card'><div class='mini'>{label}</div><div style='font-size:2rem;font-weight:700'>{val:,.0f}%</div><div>{indicator(val)} {desc}</div></div>",unsafe_allow_html=True)
st.markdown(f"<div class='chip'>{PHASE_EMOJI[today_row['luna']]} {today_row['luna']}</div>",unsafe_allow_html=True)
fig=go.Figure()
fig.add_trace(go.Scatter(x=df['fecha'],y=df['físico'],mode='lines+markers',name='Físico',line=dict(width=3)))
fig.add_trace(go.Scatter(x=df['fecha'],y=df['emocional'],mode='lines+markers',name='Emocional',line=dict(width=2,dash='dot')))
fig.add_trace(go.Scatter(x=df['fecha'],y=df['intelectual'],mode='lines+markers',name='Intelectual',line=dict(width=2,dash='dash')))
fig.add_hline(y=35,line_dash='dot',line_color='rgba(34,139,34,.6)')
fig.add_hline(y=-35,line_dash='dot',line_color='rgba(178,34,34,.6)')
fig.update_layout(title='Evolución próxima de los biorritmos',height=520,hovermode='x unified',legend=dict(orientation='h',yanchor='bottom',y=1.02,xanchor='center',x=0.5),margin=dict(l=20,r=20,t=60,b=20))
fig.update_yaxes(title='Porcentaje',range=[-105,105])
fig.update_xaxes(title='Fecha')
st.plotly_chart(fig,use_container_width=True)
st.subheader('Próximos días')
preview=df[['fecha','físico','emocional','intelectual','estado','luna']].copy()
preview['fecha']=pd.to_datetime(preview['fecha']).dt.strftime('%d/%m/%Y')
for col in ['físico','emocional','intelectual']:
    preview[col]=preview[col].map(lambda x:f'{x:.0f}%')
st.dataframe(preview,use_container_width=True,hide_index=True)
st.subheader('Calendario lunar minimalista')
moon_df=df[['fecha','luna']].copy()
moon_df['etiqueta']=moon_df['luna'].map(lambda x:f"{PHASE_EMOJI[x]} {x}")
moon_df['semana']=((pd.to_datetime(moon_df['fecha'])-pd.to_datetime(moon_df['fecha']).min()).dt.days//7)+1
for week,chunk in moon_df.groupby('semana'):
    labels=' · '.join([f"{pd.to_datetime(r.fecha).strftime('%d %b')}: {r.etiqueta}" for r in chunk.itertuples() if pd.to_datetime(r.fecha).day_name() in ['Monday','Thursday','Sunday']])
    st.markdown(f"**Semana {week}** — {labels}")
st.caption('Ejecuta con streamlit run app.py. Para PDF, usa imprimir del navegador.')
