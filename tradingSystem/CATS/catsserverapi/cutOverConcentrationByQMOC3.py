# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2021/1/28 下午5:38
# @Author : lxf
# @File : cutOverConcentrationByQMOC3.py
# @Project : ai-investment-manager

import os,sys
import traceback

path1 = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
sys.path.append(path1)
import pandas as pd
import numpy as np
from configs.Database import mysql
from tradingSystem.CATS.catsserverapi.models.Account import LocalOsInfo
from tradingSystem.CATS.catsserverapi.RootNetToCats import RootNetToCats
from tradingSystem.CATS.catsserverapi.models.AlgoParams import AlgoParams
from tradingSystem.CATS.catsserverapi.models.QMOC3Params import QMOC3Params

algoidToModel = {
    'AITWAP3':AlgoParams,
    'QMOC3':QMOC3Params
}

minOrderVolume = 100

def get_concentration_config(env='dev',strategy_id=''):
    assert strategy_id,'strategy_id empty!'
    sql = "SELECT b.strategy_id,a.risk_id,a.key,a.value FROM risk_config a left join strategy_config b on a.risk_id = b.risk_id where b.strategy_id = %s and a.key = 'concentration_ratio'"
    with mysql(env) as cursor:
        cursor.execute(sql,strategy_id)
        data = cursor.fetchall()
        if data:
            return data[0][3]



def getOrders(position,algo_id='QMOC3'):
    model = algoidToModel[algo_id]
    orders = []
    if position.empty:return orders
    for index,row in position.iterrows():
        orders.append(model(
            symbol=row['WIND_CODE'],
            targetVol=row['sellVolume'],
            tradeSide=2,
        ))

    return orders


def adjustPositionByConcentration(env='dev', mode='test', algo_id='QMOC3'):
    # 获取账户信息和集中度配置。检查持仓是否有超过集中度的
    rntc = RootNetToCats(env=env, mode=mode)
    accountAndstrategy = rntc.getAccountInfoByDB()
    for account_info, strategy_id in accountAndstrategy:
        if account_info.tradeAcctType == 'G2A':continue
        localInfo = LocalOsInfo()
        if rntc.login(acctInfo=account_info, localInfo=localInfo):
            #登录根网账户
            rntc.createRootNetServer(env=env, mode=mode, accountinfo=account_info)
            try:
            # 获取持仓
                position = rntc.rootNet.getPosition(tradeAcct=account_info.tradeAcct)
                if isinstance(position, pd.DataFrame) and not position.empty:
                    maxRatio = float(get_concentration_config(env=env, strategy_id=strategy_id))
                    position['maxRatio'] = position.apply(lambda x:maxRatio/2 if x['WIND_CODE'].startswith('300') else maxRatio,axis=1)
                    totalAsset = rntc.rootNet.getCashAndAssert().get(account_info.tradeAcct)[2]
                    position['total_asset'] = totalAsset
                    position['nowRatio'] = position['NOTIONAL']/ position['total_asset']
                    position['extRatio'] = np.where(position['nowRatio'] > position['maxRatio'], position['nowRatio'] - position['maxRatio'], 0)
                    position['extVolume'] = np.ceil(position['extRatio']/position['nowRatio']*position['POSITION']/minOrderVolume)*minOrderVolume
                    position['sellVolume'] = position.apply(lambda x: min(x['extVolume'],x['POSITION']), axis=1)
                    position = position[position['sellVolume'] != 0]
                    orders = getOrders(position,algo_id=algo_id)
                    rntc.sendOrderToQMOC(orders,algoId=algo_id)
            except:
                traceback.print_exc()
    if rntc.rootNet:
        rntc.close()

if __name__ == '__main__':
    adjustPositionByConcentration(env='prod',mode='prod',algo_id='QMOC3')

