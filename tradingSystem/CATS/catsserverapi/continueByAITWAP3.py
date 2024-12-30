#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file:continueByAITWAP3.py
@time:2020/09/09
"""
import os,sys
import time
import arrow
from collections import defaultdict
path1 = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
sys.path.append(path1)
from configs.Database import mysql, PROD,SHARE,DEV ,AITRADERTEST,AITRADERPROD
from tradingSystem.CATS.catsserverapi.RootNetToCats import RootNetToCats
from tradingSystem.CATS.catsserverapi.models.Account import LocalOsInfo
from tradingSystem.CATS.catsserverapi.models.AlgoParams import AlgoParams
from tradingSystem.CATS.catsserverapi.models.QMOC3Params import QMOC3Params
from utils.AiData import getMinPriceCHG_UNIT

modelName = {
    'AITWAP3': AlgoParams,
    'QMOC3': QMOC3Params
}

tradeSideToTradeType = {
    '1': 1,
    '2': -1
}

def getTickSize(windcode, etfCodes):
    if windcode in etfCodes:
        return 0.005, 3
    else:
        return 0.005, 2


def getETFCodes():
    with mysql(SHARE) as cursor:
        sql = "select wind_code from ETF_SUPPORT"
        cursor.execute(sql)
        data = cursor.fetchall()
        return [row[0] for row in data]


def get_restart_orders(side='1',algo_type = 'AITWAP3',env='dev'):
    """
    get order need to restart by tradeSide
    '0':both,'1':buy,'2':sell
    """
    result = defaultdict(list)
    date = str(arrow.now().date())
    if env == 'prod':
        dbconfig = AITRADERPROD
    else:
        dbconfig = AITRADERTEST
    with mysql(env=dbconfig) as cursor:
        if side == '0':
            sql = "select trade_account,params from algo_restart_params where trade_date = %s and algo_type = %s"
            cursor.execute(sql, (date,algo_type))
        else:
            sql = "select trade_account,params from algo_restart_params where trade_date = %s and trade_side = %s and algo_type = %s"
            cursor.execute(sql, (date, side,algo_type))
        data = cursor.fetchall()
        if data:
            for row in data:
                result[row[0]].append(row[1])
    return result


def resend_aitwap3(env=DEV,mode='test', trade_side='2', algo_id='AITWAP3'):
    # get restart orders
    params = get_restart_orders(side=trade_side,algo_type=algo_id,env=env)
    if not params: return
    rntc = RootNetToCats(env=env, mode=mode)
    accountAndstrategy = rntc.getAccountInfoByDB()
    time.sleep(0.5)
    for account_info, strategy_id in accountAndstrategy:
        orders = params.get(account_info.tradeAcct)
        if not orders: continue
        localInfo = LocalOsInfo()
        if rntc.login(acctInfo=account_info, localInfo=localInfo):
            for orderstr in orders:
                order = modelName[algo_id](**eval(orderstr))
                if int(order.targetVol) <= 0: continue
                order.acctType = account_info.tradeAcctType
                print(order.getCatsParams())
                rntc.catsServer.catsStartAlgo(algoId=algo_id, startParams=str(order.getCatsParams()))


def resend_to_qmoc3(env='test',mode='test', trade_side='1', algo_id='QMOC3', stopPrice=0):
    # get restart orders
    params = get_restart_orders(side=trade_side,algo_type=algo_id,env=env)
    if not params: return
    rntc = RootNetToCats(env=env,mode=mode)
    accountAndstrategy = rntc.getAccountInfoByDB()
    for account_info, strategy_id in accountAndstrategy:
        orders = params.get(account_info.tradeAcct)
        if not orders: continue
        localInfo = LocalOsInfo()
        if rntc.login(acctInfo=account_info, localInfo=localInfo):
            rntc.createRootNetServer(env=env,mode=mode,accountinfo=account_info)
            nowCASH = rntc.rootNet.tradingServer.getAvaCash()[account_info.tradeAcct]
            ordersObjects = []
            for orderstr in orders:
                order = modelName[algo_id](**eval(orderstr))
                if int(order.targetVol) <= 0: continue
                order.beginTime = '145700'
                order.acctType = account_info.tradeAcctType
                order.stopPrice = stopPrice
                newPrice = rntc.rootNet.getPriceInfo(order.symbol).newPrice
                limitPrice = newPrice + newPrice * 0.005 * tradeSideToTradeType[str(order.tradeSide)]
                tickSize = getMinPriceCHG_UNIT(order.symbol)*10000
                order.limitPrice = round(limitPrice*10000/tickSize)*tickSize/10000
                ordersObjects.append(order)
            ordersObjects = rntc.filterOrderByCash(ordersObjects,nowCASH)
            for orderObj in ordersObjects:
                if int(orderObj.targetVol) <= 0: continue
                print(orderObj.getCatsParams())
                rntc.catsServer.catsStartAlgo(algoId=algo_id, startParams=str(orderObj.getCatsParams()))
    if rntc.rootNet:
        rntc.close()

if __name__ == '__main__':
    resend_aitwap3(env=PROD, mode=PROD, trade_side='0', algo_id='AITWAP3')
