#!/usr/bin/env python
# coding: utf-8

#Data collection libraries
import requests #The requests library for HTTP requests in Python
import streamlit as st
from streamlit import config as _config
import streamlit.bootstrap

#Data Processing libraries
import pandas as pd
import numpy as np #The Numpy numerical computing library for numerical calculations
import math #The Python math module
import pandas as pd #The Pandas data science library
from scipy import stats #The SciPy stats modules

#Create excel Data Output
import xlsxwriter #The XlsxWriter library to create Excel File

#Data Visualization Libraries
import plotly.express as px
from PIL import Image

#System Libraries
import os
import sys

st.set_page_config(page_title='Stock Price Visualization')
st.header('Stock Prices 2022')
st.subheader('Let us guide you on your Investment Journey')


#Reading input from user for portfolio size
user_input = st.number_input('Enter your portfolio size: ', min_value=1000, value=5000, step=5000)

stocks = pd.read_csv('sp_500_stocks.csv')
stocks = stocks[~stocks['Ticker'].isin(['DISCA', 'HFC','VIAC','WLTW'])]

from iexcreds import IEX_CLOUD_API_TOKEN




symbol = 'AAPL'
api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote?token={IEX_CLOUD_API_TOKEN}'
data = requests.get(api_url).json()


pe_ratio = data['peRatio']

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

final_dataframe = pd.DataFrame(columns = my_columns)

for symbol_string in symbol_strings:
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
        
final_dataframe.sort_values('Price-to-Earnings Ratio', inplace = True)
final_dataframe = final_dataframe[final_dataframe['Price-to-Earnings Ratio'] > 0]
final_dataframe = final_dataframe[:20]
final_dataframe.reset_index(inplace = True)
final_dataframe.drop('index', axis=1, inplace = True)


portfolio_size = float(user_input)
position_size = portfolio_size/ len(final_dataframe.index)
for i in range(0, len(final_dataframe['Ticker'])):
    final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size / final_dataframe['Price'][i])

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

for column in ['Price-to-Earnings Ratio', 'Price-to-Book Ratio','Price-to-Sales Ratio',  'EV/EBITDA','EV/GP']:
    rv_dataframe[column].fillna(rv_dataframe[column].mean(), inplace = True)

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

from statistics import mean

for row in rv_dataframe.index:
    value_percentiles = []
    for metric in metrics.keys():
        value_percentiles.append(rv_dataframe.loc[row, metrics[metric]])
    rv_dataframe.loc[row, 'RV Score'] = mean(value_percentiles)

rv_dataframe.sort_values(by = 'RV Score', inplace = True)
rv_dataframe = rv_dataframe[:20]
rv_dataframe.reset_index(inplace = True)
rv_dataframe.drop('index', axis=1, inplace = True)

position_size = portfolio_size / len(rv_dataframe.index)
for i in range(0, len(rv_dataframe['Ticker'])):
    rv_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size / rv_dataframe['Price'][i])

writer = pd.ExcelWriter('value_strategy.xls')
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

# --- PLOT BAR CHART
bar_chart = px.bar(df,
                   x='Ticker',
                   y='Price',
                   text='Price',
                   color_discrete_sequence = ['#F63366']*len(df),
                   template= 'plotly_white')
st.plotly_chart(bar_chart)

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
