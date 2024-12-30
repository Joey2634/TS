#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file:sendOrder.py
@time:2020/05/28
"""
import sys
import pandas as pd
from configs.Database import DEV
from tradingSystem.CATS.catsserverapi.catsConfig import CatsTypeTotradeAcct
from tradingSystem.CATS.catsserverapi.models.Account import LocalOsInfo
from tradingSystem.CATS.catsserverapi.RootNetToCats import RootNetToCats



def run(env=DEV, mode='test',strategyids: list = None,targetOrders: pd.DataFrame = None,T0TargetOrder=pd.DataFrame(), accountType='CASH'):
    rntc = RootNetToCats(env=env,mode=mode)
    accountAndstrategy = rntc.getAccountInfoByDB()
    for account, strategy_id in accountAndstrategy:
        if strategy_id not in strategyids: continue
        if CatsTypeTotradeAcct[account.tradeAcctType] != accountType: continue
        rntc.loadAlgoConfig(strategy_id, algo_type='AITWAP3')
        localInfo = LocalOsInfo()
        if rntc.login(account, localInfo):
            rntc.sendOrder(strategy_id, account, targetOrders, algo_id='AITWAP3')
            if accountType =='CASH':
                rntc.sendToOrder(strategy_id, account, T0TargetOrder, algo_id='AITWAP3')
            rntc.saveInstanceidToDB(type='twap')
    if rntc.rootNet:
        rntc.close()


if __name__ == '__main__':
    run(env=DEV, mode='test',strategyids=['S-L-4|LastPrice|CLOSE|RISK-169'])
