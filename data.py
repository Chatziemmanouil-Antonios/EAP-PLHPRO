
import numpy as np
import pandas as pd
#from scipy.interpolate import interp1d,pchip
#from scipy.integrate import odeint, solve_ivp, solve_bvp
#from scipy.optimize import differential_evolution, minimize
from scipy import signal

df=pd.read_csv("https://raw.githubusercontent.com/Sandbird/covid19-Greece/master/cases.csv",parse_dates=["date"])
df=df.set_index("date")
df=df.drop(["id"],axis=1)
df["new_positive_tests"]=df.positive_tests.diff()
df["new_vaccinations"]=df['total_vaccinations'].diff()
from scipy.stats import gamma
k=2209/290
t=(29/47)
dist=gamma(k,scale=t)

def Rt(df,ix0=-1,smooth="10D",k=2209/290,t=29/47):
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
from plotly.subplots import make_subplots


st.set_page_config(layout="wide")
st.title('Greece covid analytics Dashboard')

#r1, r_cases, r_deaths, r_hostpital, r_Rt, r2 = st.columns((1,1,1,1,1,1))

# Index(['new_cases', 'confirmed', 'new_deaths', 'total_deaths', 'new_tests',
#        'positive_tests', 'new_selftest', 'total_selftest', 'new_ag_tests',
#        'ag_tests', 'total_tests', 'new_critical', 'total_vaccinated_crit',
#        'total_unvaccinated_crit', 'total_critical', 'hospitalized',
#        'discharged', 'icu_out', 'icu_percent', 'beds_percent', 'new_active',
#        'active', 'recovered', 'total_foreign', 'total_domestic',
#        'total_unknown', 'total_vaccinations', 'reinfections'],
#       dtype='object')

value_labels={"New Cases":'new_cases',"Rt":"Rt","New Tests":'new_tests',"New Positive Tests":"new_positive_tests",
              "New Deaths":'new_deaths',"New Hospitalizations":"hospitalized","New Critical":"new_critical","ICU out":"icu_out",
             "New Vaccinations":"new_vaccinations","Total Vaccinations":"total_vaccinations"}


Rows={"Cases and Testing":["New Cases","Rt","New Tests","New Positive Tests"],
     "Hospitalization and Mortallity":["New Hospitalizations","New Critical","New Deaths","ICU out"],
      "Vaccinations":["Total Vaccinations"]
     }


for Row in Rows:
    cols = st.columns(tuple([0.5]+[1]*len(Rows[Row])))
    with cols[0]:
        st.markdown(Row)
    for ci,label in zip(cols[1:],Rows[Row]):
        info=value_labels[label]
        if np.isfinite(df.iloc[-1][info]) and np.isfinite(df.iloc[-2][info]):
            val=df.iloc[-1][info]
            dif=df.iloc[-1][info]-df.iloc[-2][info]
        else:
            notna=df[~pd.isna(df[info])]
            val=notna.iloc[-1][info]
            dif=notna.iloc[-1][info]-notna.iloc[-2][info]
        if label != "Rt":
            ci.metric(label=label,value= int(val), delta = str(int(dif)), delta_color = 'inverse')
        else:
            ci.metric(label=label,value= round(val,2), delta = str(round(dif,2)), delta_color = 'inverse')

# r1.write('')
# info='new_cases'
# r_cases.metric(label ='New Cases',value = int(df.iloc[-1][info]), delta = str(int(df.iloc[-1][info]-df.iloc[-2][info]))+' Compared to yesterday', delta_color = 'inverse')
# info='new_deaths'
# r_deaths.metric(label ='New Deaths',value = int(df.iloc[-1][info]), delta = str(int(df.iloc[-1][info]-df.iloc[-2][info]))+' Compared to yesterday', delta_color = 'inverse')

# info='hospitalized'
# r_hostpital.metric(label ='New Hospitalizations',value = int(df.iloc[-1][info]), delta = str(int(df.iloc[-1][info]-df.iloc[-2][info]))+' Compared to yesterday', delta_color = 'inverse')

# info='Rt'
# r_Rt.metric(label ='Rt',value = round(df.iloc[-1][info]), delta = str(round(df.iloc[-1][info]-df.iloc[-2][info]))+' Compared to yesterday', delta_color = 'inverse')
# r2.write('')

row_spacer_start, row1, row2, row_spacer_end  = st.columns((0.1, 1.0, 6.4, 0.1))

with row1:
    #st.markdown('Select value')    
    plot_value = st.selectbox ("Variable", list(value_labels.keys()), key = 'value_key')
    plot_value2 = st.selectbox ("Second Variable", [None]+list(value_labels.keys()), key = 'value_key')
    smooth = st.checkbox("Add smooth curve")
    log = st.checkbox("Use log scale")
    
with row2:    
    sec= not (plot_value2 is None)
    fig = make_subplots(specs=[[{"secondary_y": sec}]])
    x1=df.index
    y1=df[value_labels[plot_value]]
    
    fig1= px.bar(df,x = x1, y=value_labels[plot_value])#,log_y=log)#, template = 'seaborn')
    fig.add_traces(fig1.data)
    fig.layout.yaxis.title=plot_value
    if smooth:
        #xs1= df.rolling("7D").mean()[value_labels[plot_value]]
        ys1= df.rolling("7D").mean()[value_labels[plot_value]]
        figs=px.line(x = x1, y=ys1)#,log_y=log)
        fig.add_traces(figs.data)        
        
    if sec:
        x2=df.index
        y2=df[value_labels[plot_value2]]
        figs=px.line(x = x2, y=y2)#,log_y=log)
        figs.update_traces(yaxis="y2")
        
        fig.add_traces(figs.data)
        fig.layout.yaxis2.title=plot_value2
      
    #fig.update_traces(marker_color='#264653')
    #fig.for_each_trace(lambda t: t.update(line=dict(color=t.marker.color)))

    fig.update_layout(title_x=0,margin= dict(l=0,r=10,b=10,t=30), yaxis_title=None, xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True) 

# #g1 = st.columns((1))
# figC = px.bar(df, x = df.index, y='new_cases', template = 'seaborn')
# figC.update_traces(marker_color='#264653')
# figC.update_layout(title_text="New Cases",title_x=0,margin= dict(l=0,r=10,b=10,t=30), yaxis_title=None, xaxis_title=None)
# st.plotly_chart(figC, use_container_width=True) 

# #g2 = st.columns((1))
# figD = px.bar(df, x = df.index, y='new_deaths', template = 'seaborn')
# figD.update_traces(marker_color='#264653')
# figD.update_layout(title_text="New Cases",title_x=0,margin= dict(l=0,r=10,b=10,t=30), yaxis_title=None, xaxis_title=None)
# st.plotly_chart(figD, use_container_width=True) 

# #g3 = st.columns((1))
# figR = px.line(df, x = df.index, y='Rt', template = 'seaborn')
# figR.update_traces(marker_color='#264653')
# figR.update_layout(title_text="Rt",title_x=0,margin= dict(l=0,r=10,b=10,t=30), yaxis_title=None, xaxis_title=None)
# st.plotly_chart(figR, use_container_width=True) 
