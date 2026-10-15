# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 21:12:07 2022

@author: Victor Lee
"""

import os
import pandas as pd
import numpy as np
import yfinance as yf
import time
import telegram
# from tabulate import tabulate
import matplotlib.pyplot as plt
from datetime import date
import asyncio
import warnings
warnings.filterwarnings("ignore")
#import talib as TA


path=os.path.dirname(os.path.abspath(__file__))+"/"
filename=path+"AASTOCKS_Export_2025-7-13.xlsx"

# Token and chat ID used in telegram
TOKEN="8919894256:AAE7PQ4dT46cAF-RA0wkMHWUrbAIdPBl_jY"
chat_id="5349094008"

# Starting date which is used to generate the chart
date1="2024-01-01"
today=date.today().strftime("%d%m%Y")

# Import excel with stock codes and create a list L_stock which stores the 
# stock codes

L_stocks=pd.read_excel(filename)["代號"].tolist()
L_stocks=[i[1:] for i in L_stocks]
L_stocks.append("^HSI")
L_stocks_names=pd.read_excel(filename)["名稱"].tolist()
L_stocks_names.append("恆生指數")

# To download the stock data one by one and save it as a dictionary
def getdata(L):
    D1={}
    for i in L:
        df=yf.download(i,"2021-01-01",progress=False)
        df.columns = df.columns.droplevel('Ticker')
        message="Now downloading data:"+i
        print(message)
        D1[i]=df
    return(D1)

# Based on the dictionary above generates the result with the restuen of previous 5 days and 
# previous 20 days

def table_gen1(D):
    L_return_1day=[]
    L_return_5days=[]
    L_return_20days=[]
    for i in L_stocks:        
        return1day=round(100*(D[i]["Close"].iloc[-1]-D[i]["Close"].iloc[-2])/D[i]["Close"].iloc[-2],1)
        return5days=round(100*(D[i]["Close"].iloc[-1]-D[i]["Close"].iloc[-5])/D[i]["Close"].iloc[-5],1)
        return20days=round(100*(D[i]["Close"].iloc[-1]-D[i]["Close"].iloc[-20])/D[i]["Close"].iloc[-20],1) 
        L_return_1day.append(return1day)        
        L_return_5days.append(return5days)
        L_return_20days.append(return20days)
    df_result=pd.DataFrame({"Stock Code":L_stocks,"Stock Name":L_stocks_names,"Return(1day)":L_return_1day,
                           "Return(5days)":L_return_5days,"Return(20days)":L_return_20days})
    df_result.sort_values(["Return(1day)","Return(5days)","Return(20days)"],ascending=False,inplace=True)
    return(df_result)


D_stocks=getdata(L_stocks)

df_result=table_gen1(D_stocks)


df_result.to_excel("df_result"+"_"+today+".xlsx",index=False)

L_coins_sorted=df_result["Stock Code"].iloc[:5].tolist()
L_coins_sorted.append("^HSI")


f1, ax = plt.subplots(figsize = (15,10))
for i in L_coins_sorted:
    ax.plot(D_stocks[i].loc[date1:].index,D_stocks[i].loc[date1:]["Close"]/D_stocks[i].loc[date1:]["Close"].iloc[0],label=i,linewidth=1)
ax.legend()
ax.grid(True)
plt.savefig("chart1.png")

# Send the result with Telegram

bot = telegram.Bot(token=TOKEN)

async def send(bot):
    await bot.send_document(chat_id=chat_id, document=open("df_result"+"_"+today+".xlsx", 'rb'))
    await bot.send_photo(chat_id=chat_id, photo=open('chart1.png', 'rb'))
                 
asyncio.run(send(bot))

