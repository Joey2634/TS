#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file:sendT0Orders.py
@time:2020/09/02
"""
import sys
import traceback
import pandas as pd
from configs.Database import MOCK, PROD
from tradingSystem.CATS import RootNetToCats
from tradingSystem.CATS import QMOC3Params
from tradingSystem.CATS import LocalOsInfo
from tradingSystem.CATS import check

if not check():
    print("today is not trade day ,exit!")
    sys.exit(0)


stock_starts_with = ('60','30','00')


def run(env=MOCK,strategyids:list=None):
    rntc = RootNetToCats(env=env)
    accountAndstrategy = rntc.getAccountInfoByDB()
    for account, strategy_id in accountAndstrategy:
        if strategy_id not in strategyids:continue
        rntc.loadAlgoConfig(strategy_id, algo_type='AIDTrade3')
        localInfo = LocalOsInfo()
        if rntc.login(account, localInfo):
            orders = rntc.getOrders(strategyid=strategy_id, model=QMOC3Params)
            orderSellDict = {}
            for order in orders:
                if not order.symbol.startswith(stock_starts_with):continue
                if str(order.tradeSide) == '2':
                    orderSellDict[order.symbol] = order.targetVol
            print(orderSellDict)
            rntc.createRootNetServer(env,account)
            try:
                position = rntc.rootNet.getPosition()
                if isinstance(position, pd.DataFrame) and position.empty: continue
                for index, row in position.iterrows():
                    if not row['WIND_CODE'].startswith(stock_starts_with): continue
                    volume = int(row['POSITION']) - orderSellDict.get(row['WIND_CODE'], 0)
                    if volume < 100: continue
                    rntc.sendOrderOneCode(symbol=row['WIND_CODE'],tradeSide= '1',targetVol=volume,algo_id='AITWAP3', tradingStyle ='0')
                    rntc.sendOrderOneCode(symbol=row['WIND_CODE'],tradeSide= '2',targetVol=volume,algo_id='AITWAP3', tradingStyle ='0')
            except:
                traceback.print_exc()
            finally:
                pass
            rntc.saveInstanceidToDB('t0')


if __name__ == '__main__':
    run(PROD)
