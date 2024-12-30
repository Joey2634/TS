# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/12/23 下午3:51
# @Author : lxf
# @File : targetOrderLive.py
# @Project : ai-investment-manager

import pandas as pd
from tradeExecution.createOrder.targetOrderMock import targetOrderMock


class targetOrderLive(targetOrderMock):

    def __init__(self, env='dev',
                 mode='mock',
                 trade_date='',
                 pre_date='',
                 assetInfo: pd.DataFrame = None,
                 strategyConfigs: list = None,
                 windData: dict = None,
                 security_list: set = None,
                 tradingServer = None,
                 nowAssetInfo = None
                 ):

        """
        根据env和mode 决定 总资产信息，昨日持仓和最新价的获取方式
                mode=='mock':数据库获取
                mode=='prod':交易系统获取
        """
        super().__init__(env=env,
                         mode=mode,
                         trade_date=trade_date,
                         pre_date=pre_date,
                         assetInfo=assetInfo,
                         strategyConfigs=strategyConfigs,
                         windData=windData,
                         security_list=security_list)
        self.tradingServer = tradingServer
        self.nowAssetInfo = nowAssetInfo



    def run(self, targetPosition, T0TargetPosition, nowAsset):
        targetOrdersNormal,targetOrderT0 = super().run(targetPosition, T0TargetPosition, nowAsset)
        return targetOrdersNormal,targetOrderT0



    # -----------------------------------------private funcs -----------------------------------------------------------

    def _fill_price(self, row: pd.Series,priceType=''):
        """
        获取最新价
        """
        if priceType:
            return getattr(self.tradingServer.getStkInfo(row['windcode']),priceType)
        return self.tradingServer.getStkInfo(row['windcode']).newPrice

    def _getAssetInfo(self):
        # return self.assetInfo[self.assetInfo['trade_date'].str.replace("-","") == self.trade_date]
        return self.nowAssetInfo





