
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d,pchip
from scipy.integrate import odeint, solve_ivp, solve_bvp
from scipy.optimize import differential_evolution, minimize

df=pd.read_csv("https://raw.githubusercontent.com/Sandbird/covid19-Greece/master/cases.csv",parse_dates=["date"])
df=df.set_index("date")
df=df.drop(["id"],axis=1)

from scipy.stats import gamma
k=2209/290
t=(29/47)
dist=gamma(k,scale=t)

def Rt(df,ix0=-1,smooth="7D",k=2209/290,t=29/47):
    Irm=df.rolling(smooth).mean().new_cases
    s=0
    dist=gamma(k,scale=t)
    for ix in range(0,15):    
        s+=dist.pdf(ix)*Irm[ix0-ix]
        #print(ix,ix0-ix,Irm[ix0-ix],Irm[ix0]/s) 
    return Irm[ix0]/s
  
df["Rt"]=np.nan
for i in range(len(df)):
    df["Rt"].iloc[i]=Rt(df,i)
    
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
st.set_page_config(layout="wide")
m1, m2, m3, m4, m5 = st.columns((1,1,1,1,1))
m1.write('')
info='new_cases'
m2.metric(label ='New Cases',value = df.iloc[-1][info], delta = str(int(df.iloc[-1][info]-df.iloc[-2][info]))+' Compared to yesterday', delta_color = 'inverse')
info='new_deaths'
m3.metric(label ='New Deaths',value = df.iloc[-1][info], delta = str(int(df.iloc[-1][info]-df.iloc[-2][info]))+' Compared to yesterday', delta_color = 'inverse')
info='Rt'
m4.metric(label ='Rt',value = df.iloc[-1][info], delta = str(int(df.iloc[-1][info]-df.iloc[-2][info]))+' Compared to yesterday', delta_color = 'inverse')
m1.write('')


#g1 = st.columns((1))
figC = px.bar(df, x = df.index, y='new_cases', template = 'seaborn')
figC.update_traces(marker_color='#264653')
figC.update_layout(title_text="New Cases",title_x=0,margin= dict(l=0,r=10,b=10,t=30), yaxis_title=None, xaxis_title=None)
st.plotly_chart(figC, use_container_width=True) 

#g2 = st.columns((1))
figD = px.bar(df, x = df.index, y='new_deaths', template = 'seaborn')
figD.update_traces(marker_color='#264653')
figD.update_layout(title_text="New Cases",title_x=0,margin= dict(l=0,r=10,b=10,t=30), yaxis_title=None, xaxis_title=None)
st.plotly_chart(figD, use_container_width=True) 

#g3 = st.columns((1))
figR = px.line(df, x = df.index, y='Rt', template = 'seaborn')
figR.update_traces(marker_color='#264653')
figR.update_layout(title_text="Rt",title_x=0,margin= dict(l=0,r=10,b=10,t=30), yaxis_title=None, xaxis_title=None)
st.plotly_chart(figR, use_container_width=True) 
