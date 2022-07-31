#!/usr/bin/env python
# coding: utf-8

# In[288]:


import numpy as np #The Numpy numerical computing library for numerical calculations
import pandas as pd #The Pandas data science library
import requests #The requests library for HTTP requests in Python
import xlsxwriter #The XlsxWriter libarary for 
import math #The Python math module
from scipy import stats #The SciPy stats modules
import os
import streamlit.bootstrap
from streamlit import config as _config
import streamlit as st
import sys
import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image


st.set_page_config(page_title='Stock Price Visualization')
st.header('Stock Prices 2022')
st.subheader('Observe the Stocks')
# In[289]:

#user_input = st.text_input("Enter portfio size", key=int)
user_input = st.number_input('Enter portfio size: ', min_value=1000, value=5000, step=5000)
#portfolio_size = user_input.astype(float)
#a_list = ["portfolio_size"]
#a_list = list(map(int, a_list)



stocks = pd.read_csv('sp_500_stocks.csv')
stocks = stocks[~stocks['Ticker'].isin(['DISCA', 'HFC','VIAC','WLTW'])]

from iexcreds import IEX_CLOUD_API_TOKEN


# In[290]:


symbol = 'AAPL'
api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote?token={IEX_CLOUD_API_TOKEN}'
data = requests.get(api_url).json()
#data


# In[291]:


pe_ratio = data['peRatio']
#pe_ratio


# In[292]:


# Function sourced from 
# https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]   
        
symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))


my_columns = ['Ticker', 'Price', 'Price-to-Earnings Ratio', 'Number of Shares to Buy']


# In[293]:


final_dataframe = pd.DataFrame(columns = my_columns)

for symbol_string in symbol_strings:
#     print(symbol_strings)
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        final_dataframe = final_dataframe.append(
                                        pd.Series([symbol, 
                                                   data[symbol]['quote']['latestPrice'],
                                                   data[symbol]['quote']['peRatio'],
                                                   'N/A'
                                                   ], 
                                                  index = my_columns), 
                                        ignore_index = True)
        
    
#final_dataframe


# In[294]:


final_dataframe.sort_values('Price-to-Earnings Ratio', inplace = True)
final_dataframe = final_dataframe[final_dataframe['Price-to-Earnings Ratio'] > 0]
final_dataframe = final_dataframe[:20]
final_dataframe.reset_index(inplace = True)
final_dataframe.drop('index', axis=1, inplace = True)


# In[295]:


#def portfolio_input():
#    global portfolio_size
#    portfolio_size = input("Enter the value of your portfolio:")
#
#    try:
#        val = float(portfolio_size)
#    except ValueError:
#        print("That's not a number! \n Try again:")
#        portfolio_size = input("Enter the value of your portfolio:")
#
#
## In[296]:
#
#
#portfolio_input()

#portfolio_size = value

#a_list = ["portfolio_size"]
#float_list = list(map(float, a_list))
#portfolio_size=float_list
# In[297]:
#a_list = ["user_input"]
#float_list = str(map(float, a_list))
#portfolio_size=float_list


portfolio_size = float(user_input)
position_size = portfolio_size/ len(final_dataframe.index)
for i in range(0, len(final_dataframe['Ticker'])):
    final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size / final_dataframe['Price'][i])
#final_dataframe


# In[298]:


symbol = 'AAPL'
batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=advanced-stats,quote&symbols={symbol}&token={IEX_CLOUD_API_TOKEN}'
data = requests.get(batch_api_call_url).json()

# P/E Ratio
pe_ratio = data[symbol]['quote']['peRatio']

# P/B Ratio
pb_ratio = data[symbol]['advanced-stats']['priceToBook']

#P/S Ratio
ps_ratio = data[symbol]['advanced-stats']['priceToSales']

# EV/EBITDA
enterprise_value = data[symbol]['advanced-stats']['enterpriseValue']
ebitda = data[symbol]['advanced-stats']['EBITDA']
ev_to_ebitda = enterprise_value/ebitda

# EV/GP
gross_profit = data[symbol]['advanced-stats']['grossProfit']
ev_to_gross_profit = enterprise_value/gross_profit


# In[299]:


rv_columns = [
    'Ticker',
    'Price',
    'Number of Shares to Buy', 
    'Price-to-Earnings Ratio',
    'PE Percentile',
    'Price-to-Book Ratio',
    'PB Percentile',
    'Price-to-Sales Ratio',
    'PS Percentile',
    'EV/EBITDA',
    'EV/EBITDA Percentile',
    'EV/GP',
    'EV/GP Percentile',
    'RV Score'
]

rv_dataframe = pd.DataFrame(columns = rv_columns)

for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote,advanced-stats&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        enterprise_value = data[symbol]['advanced-stats']['enterpriseValue']
        ebitda = data[symbol]['advanced-stats']['EBITDA']
        gross_profit = data[symbol]['advanced-stats']['grossProfit']
        
        try:
            ev_to_ebitda = enterprise_value/ebitda
        except TypeError:
            ev_to_ebitda = np.NaN
        
        try:
            ev_to_gross_profit = enterprise_value/gross_profit
        except TypeError:
            ev_to_gross_profit = np.NaN
            
        rv_dataframe = rv_dataframe.append(
            pd.Series([
                symbol,
                data[symbol]['quote']['latestPrice'],
                'N/A',
                data[symbol]['quote']['peRatio'],
                'N/A',
                data[symbol]['advanced-stats']['priceToBook'],
                'N/A',
                data[symbol]['advanced-stats']['priceToSales'],
                'N/A',
                ev_to_ebitda,
                'N/A',
                ev_to_gross_profit,
                'N/A',
                'N/A'
        ],
        index = rv_columns),
            ignore_index = True
        )


# In[300]:


#rv_dataframe[rv_dataframe.isnull().any(axis=1)]


# In[301]:


for column in ['Price-to-Earnings Ratio', 'Price-to-Book Ratio','Price-to-Sales Ratio',  'EV/EBITDA','EV/GP']:
    rv_dataframe[column].fillna(rv_dataframe[column].mean(), inplace = True)


# In[302]:


#rv_dataframe[rv_dataframe.isnull().any(axis=1)]


# In[303]:


metrics = {
            'Price-to-Earnings Ratio': 'PE Percentile',
            'Price-to-Book Ratio':'PB Percentile',
            'Price-to-Sales Ratio': 'PS Percentile',
            'EV/EBITDA':'EV/EBITDA Percentile',
            'EV/GP':'EV/GP Percentile'
}

for row in rv_dataframe.index:
    for metric in metrics.keys():
        rv_dataframe.loc[row, metrics[metric]] = stats.percentileofscore(rv_dataframe[metric], rv_dataframe.loc[row, metric])/100

# Print each percentile score to make sure it was calculated properly
#for metric in metrics.values():
    #print(rv_dataframe[metric])

#Print the entire DataFrame    
#rv_dataframe


# In[304]:


from statistics import mean

for row in rv_dataframe.index:
    value_percentiles = []
    for metric in metrics.keys():
        value_percentiles.append(rv_dataframe.loc[row, metrics[metric]])
    rv_dataframe.loc[row, 'RV Score'] = mean(value_percentiles)
    
#rv_dataframe


# In[305]:


rv_dataframe.sort_values(by = 'RV Score', inplace = True)
rv_dataframe = rv_dataframe[:20]
rv_dataframe.reset_index(inplace = True)
rv_dataframe.drop('index', axis=1, inplace = True)


# In[306]:

#portfolio_input()


# In[307]:


position_size = portfolio_size / len(rv_dataframe.index)
for i in range(0, len(rv_dataframe['Ticker'])):
    rv_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size / rv_dataframe['Price'][i])
#rv_dataframe


# In[308]:


writer = pd.ExcelWriter('value_strategy.xls')
#rv_dataframe.to_excel('value_strategy.xls', index = False)
rv_dataframe.to_excel(writer, sheet_name='Sheet1', index = False)

writer.close()



from PIL import Image
image = Image.open('images/image.png')

st.image(image, caption='Stock Prices')



### --- LOAD DATAFRAME
excel_file = 'value_strategy.xls'
sheet_name = 'Sheet1'

df = pd.read_excel(excel_file,
                   sheet_name=sheet_name,
                   usecols='A:N',
                   header=0)

st.dataframe(df)

# --- PLOT PIE CHART
pie_chart = px.pie(df,
                   title='STOCKS',
                   values='Price',
                   names='Ticker')

st.plotly_chart(pie_chart)

#mask = df 

# --- PLOT BAR CHART
bar_chart = px.bar(df,
                   x='Ticker',
                   y='Price',
                   text='Price',
                   color_discrete_sequence = ['#F63366']*len(df),
                   template= 'plotly_white')
st.plotly_chart(bar_chart)

## ---- SIDEBAR ----
#st.sidebar.header("Please Filter Here:")
#ticker = st.sidebar.multiselect(
#    "Select the Ticker:",
#    options=df["Ticker"].unique(),
#    default=df["Ticker"].unique()
#)
##
##number_of_shares_to_buy = st.sidebar.multiselect(
##    "Select the Customer Type:",
##    options=df["Number of Shares to Buy"].unique(),
##    default=df["Number of Shares to Buy"].unique(),
##)
#
#rv_score = st.sidebar.multiselect(
#    "Select the RV Score:",
#    options=df["RV Score"].unique(),
#    default=df["RV Score"].unique()
#)
#
## SALES BY PRODUCT LINE
#df_selection = df.query(
#    "Ticker == @ticker & Number of Shares to Buy ==@number_of_shares_to_buy & RV Score == @rv_score"
#)
#
## SALES BY PRODUCT LINE [BAR CHART]
#sales_by_product_line = (
#    df_selection.groupby(by=["Ticker"]).sum()[["RV Score"]].sort_values(by="RV Score")
#)
#fig_product_sales = px.bar(
#    sales_by_product_line,
#    x="RV Score",
#    y=sales_by_product_line.index,
#    orientation="h",
#    title="<b>Sales by Product Line</b>",
#    color_discrete_sequence=["#0083B8"] * len(sales_by_product_line),
#    template="plotly_white",
#)
#fig_product_sales.update_layout(
#    plot_bgcolor="rgba(0,0,0,0)",
#    xaxis=(dict(showgrid=False))
#)

# --- PLOT BAR CHART
bar_chart = px.bar(df,
                   y='Ticker',
                   x='Number of Shares to Buy',
				   orientation="h",
                   text='Number of Shares to Buy',
                   color_discrete_sequence = ['#F63366']*len(df),
                   template= 'plotly_white')
st.plotly_chart(bar_chart)

# --- PLOT PIE CHART
pie_chart = px.pie(df,
                   title='RV SCORE',
                   values='RV Score',
                   names='Ticker')
st.plotly_chart(pie_chart)
