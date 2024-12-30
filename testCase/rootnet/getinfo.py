# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2021/2/4 下午2:29
# @Author : lxf
# @File : getinfo.py
# @Project : ai-investment-manager

import traceback
from CTSlib.ApiUtils import printObject
from tradingSystem.rootNet.RootNetTrading import RootNetTrading

trading = RootNetTrading(env='test', consoleOut=True)
try:
    #prod
    # trading.login(optId='64578', optPwd='Jack1983@', acctId='010000510586', acctPwd='063223')
    # trading.login(optId='64578', optPwd='Jack1983@', acctId='010000510592', acctPwd='063223')
    # trading.login(optId='64578', optPwd='Jack1983@', acctId='010008510586', acctPwd='063223', acctType='FUTURE')
    # trading.login(optId='64578', optPwd='Jack1983@', acctId='010000510592', acctPwd='063223')

    trading.login(optId='68909', optPwd='111111', acctId='010020200721', acctPwd='111111', acctType='FUTURE')
    # trading.login(optId='68909', optPwd='111111', acctId='010000510365', acctPwd='111111')
    # print('futureInfo\n', futureInfo := trading.getFutureInfo('IF2103.CFE'))
    # printObject(trading.getStkInfo('IF2104.CFE'),"stkInfo")
    # printObject(trading.getStkInfo('600030.SH'),"stkInfo")
    print("totalAsset:{},cash:{},positionValue:{}".format(trading.getTotalAsset(), trading.getAvaCash(), trading.getPositonValue()))
    print('account\n',  account := trading.getFundInfo())
    print("orders\n",   orders := trading.getOrders())
    print("trades\n",   trades := trading.getTrades())
    print("position\n", position := trading.getPositions())
except:
    traceback.print_exc()
finally:
    trading.disconnect()
