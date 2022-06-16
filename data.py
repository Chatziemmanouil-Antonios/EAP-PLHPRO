
# ------------------------------------------------------ import libraries -------------------------------------------------
import numpy as np
import pandas as pd
from scipy import signal

#from datetime import time
#from datetime import date
import matplotlib.pyplot as plt
import seaborn as sns
#import plotly.figure_factory as ff
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
#from math import sqrt
#from sklearn import preprocessing

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# create the dataframe
df=pd.read_csv("https://raw.githubusercontent.com/Sandbird/covid19-Greece/master/cases.csv",parse_dates=["date"])
df=df.set_index("date")
df=df.drop(["id"],axis=1)
df["new_positive_tests"]=df.positive_tests.diff()
df["new_vaccinations"]=df['total_vaccinations'].diff()


# calculate the epidemiologic factors
CFR=np.nansum(df["new_deaths"])/np.nansum(df["new_cases"])
R0=2.79
m=0.0013
m_global=0.0012

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
    

# ------------------------------------------------------ streamlit page layout -------------------------------------------------
# Use the full page instead of a narrow central column
st.set_page_config(layout="wide")

# display title
st.title('Greece covid analytics Dashboard')
st.subheader('Daily Report')



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
      "Vaccinations":["Total Vaccinations",'','','']
     }


for Row in Rows: #Row is every key in dictionary Rows 
    # loop 0: Row="Cases and Testing" , Rows[Row]=["New Cases","Rt","New Tests","New Positive Tests"]
    cols = st.columns(tuple([0.5]+[1]*len(Rows[Row]))) #tuple([0.5]+[1]*len(Rows[Row]))= (0.5,1,1,1,1)
    
    with cols[0]:
        st.markdown(Row)
        
    #zip
    #for i,j,k in zip(['a','b','c'],[1,2,3],[7,8,9]):
    #i='a',j=1,k=7
    #'b',2,8
    #'c',3,9
    
    for ci,label in zip(cols[1:],Rows[Row]):
        #loop 0: ci = cols[1], label="New Cases"
        if label != '':
            info=value_labels[label] #name of the corresponding column in dataframe
            if np.isfinite(df.iloc[-1][info]) and np.isfinite(df.iloc[-2][info]):
                val=df.iloc[-1][info]
                dif=df.iloc[-1][info]-df.iloc[-2][info]
            else: 
                
                #it is only about Hospitalizations, which is around one day before
                notna=df[~pd.isna(df[info])] #temporary dataframe (with random name notna), without nan values
                #pd.isna(df[info]) is True where the dataframe is NaN
                #~pd.isna(df[info]) is True where the dataframe is NOT NaN

                val=notna.iloc[-1][info] #last not NaN value (not latest day!)
                dif=notna.iloc[-1][info]-notna.iloc[-2][info] # last not NaN value - second last not NaN value

            if label != "Rt":
                # Show the values as integers
                ci.metric(label=label,value= int(val), delta = str(int(dif)), delta_color = 'inverse')
            elif label == "New Tests":
                # If is lower make it red!
                ci.metric(label=label,value= round(val,2), delta = str(round(dif,2)), delta_color = 'normal')
            else:
                ci.metric(label=label,value= round(val,2), delta = str(round(dif,2)), delta_color = 'inverse')

                
# ----------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------- page row 1 ---------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------------------------
row_spacer_start, R0_, m_,m_global_, CFR_  = st.columns((0.5,1.0,1.0,1.0,1.0)) 
with row_spacer_start:
    st.markdown("Epidemiological Indicators")
R0_.metric(label="Basic Reproduction Number - Ro",value= R0)
m_.metric(label="Mortality (Greece)",value= m)
m_global_.metric(label="Mortality (Global)",value= m_global)
CFR_.metric(label="Case Fatality Rate",value= round(CFR,3))
                
row_spacer_start, row1, row2, row_spacer_end  = st.columns((0.1, 1.0, 6.4, 0.1))

with row1:
    #add here everything you want in first column
    plot_value = st.selectbox ("Variable", list(value_labels.keys()), key = 'value_key') #take all the keys from value_labels dictionary
    plot_value2 = st.selectbox ("Second Variable", [None]+list(value_labels.keys()), key = 'value_key')
    smooth = st.checkbox("Add smooth curve")
   
    
with row2:    
    sec= not (plot_value2 is None) #True or False if there is a second plot
    
    fig = make_subplots(specs=[[{"secondary_y": sec}]]) #plotly function, define fig which will be show at user
    
    x1=df.index #abbreviation for dates
    y1=df[value_labels[plot_value]] #abbreviation for ploting values, translate from shown names to column names (from value_labels dictionary)
    
    #fig1= px.bar(df,x = x1, y=value_labels[plot_value])
    
    fig1= px.bar(df,x = x1, y=y1) #bar plot named as fig1
    
    fig.add_traces(fig1.data) #add to the fig (what is going to be show to the user) the fig1
    
    
    #fig.layout.yaxis.title=plot_value #add label
    
    if smooth:
        # Create temprary rolling average dataframe
        ys1= df.rolling("7D").mean()[value_labels[plot_value]]
        figs=px.line(x = x1, y=ys1)
        fig.add_traces(figs.data)   #add figs to the fig (what we will show at the end)     
        
    if sec:
        x2=df.index
        y2=df[value_labels[plot_value2]]
        figsec=px.line(x = x2, y=y2)
        figsec.update_traces(yaxis="y2")
        
        fig.add_traces(figsec.data) #add figsec to the fig (what we will show at the end) 
        fig.layout.yaxis2.title=plot_value2

    fig.update_layout(title_x=0,margin= dict(l=0,r=10,b=10,t=30), yaxis_title=plot_value, xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True) 


# ----------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------- page row 2 ---------------------------------------------------------------------  
# ----------------------------------------------------------------------------------------------------------------------------------------
row_spacer_start_row2, dependent_variable  = st.columns((0.1,4.0)) 
                
row_spacer_start, row1, row2, row_spacer_end  = st.columns((0.1, 1.0, 6.4, 0.1))

with row1:
    #add here everything you want in first column
    #plot_value = st.selectbox ("Linear regression", list(value_labels.keys()), key = 'value_key') #take all the keys from value_labels dictionary
    st.subheader("Near Future Projection")

if st.checkbox("Display dataset", False):
    st.subheader("COVID Greece dataset")
    st.write(df) 
    
# ----------------------------------------- linear regression -----------------------------------------#
# input arrays
#x = np.array(df[['id']])
#y = np.array(df['new_cases'])

# Create an instance of liner regression
#lm = LinearRegression()
#model = lm.fit(x, y)

#y_pred = lm.predict(x)
#r_squared = lm.r2_score(x, y)

#figline = sns.regplot(x='dates', y='new_cases', data=df)
#st.pyplot(figline)

### Accuracy of the model
#"""
#R2 = r2_score(Y_val, Y_pred_val)
#st.write(f'R2 value: {R2:.2f}')

# Plot
#with row2: 
#fig, ax = plt.subplots(figsize=(5, 3))
#ax.scatter(x=df['id'], y=df['new_cases'])
#sns.regplot(x='date', y='new_cases', data=df)
#plt.xlabel('date')
#plt.ylabel('new_cases')
#st.pyplot(fig)

#fig_LR = px.scatter(df, x=df["date"], y=df["new_cases"], trendline='ols', title='Ordinary Least Squares Regression') 


# -----------------------------------------------------------------------------------------------------#

with row2:      
    #sec= not (plot_value2 is None) #True or False if there is a second plot
        
    x_LR = df.index #abbreviation for dates
    y_LR = df["new_cases"] #abbreviation for ploting values, translate from shown names to column names (from value_labels dictionary)
    
    fig = px.scatter(df, x=x_LR, y=y_LR, trendline="ols")
    fig.show()
    
    #fig1= px.bar(df,x = x1, y=value_labels[plot_value])#,log_y=log)
    #fig_LR= px.bar(df,x = x_LR, y=y_LR) #bar plot named as fig1
    
    fig.update_layout(title_x=0,margin= dict(l=0,r=10,b=10,t=30), yaxis_title=plot_value, xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True) 
