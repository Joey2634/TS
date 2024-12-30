#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file:QMOC3Params.py
@time:2020/08/31
"""

import re


class QMOC3Params():

    def __init__(self, acctType='', account='', symbol='', tradeSide='',
                 targetVol='', beginTime='', limitPrice='0',
                 stopPrice='0',  tradingStyle='1',**kwargs):
        """

        :param acctType:          交易账户类别
        :param account:           交易账号
        :param symbol:            标的
        :param tradeSide:         买卖方向
        :param targetVol:         目标量
        :param beginTime:         开始时间
        :param limitPrice:        限价
        :param stopPrice:         止损价
        :param minOrderAmt:       最小下单金额
        :param tradingStyle:      交易风格
        """
        """
        {'account': '30100199462', 'acctType': 'SZDDF0',
         'beginTime': '95919', 'channel': 'dca43f5a-9a2c-11ea-8000-94188289357c',
          'endTime': '112940', 'file_name_group': '', 'limitPrice': '0', 'minOrderAmt': '0',
           'participateRate': '0', 'source_channel': 'autoScanUniversal',
            'source_group': 'AlogOrder_35958217_1', 'source_id': '30100199462',
             'symbol': '600295.SH', 'targetVol': '72200', 'tradeSide': '1', 'tradingStyle': '1'}
        """
        self.acctType = acctType
        self.account = account
        self.symbol = symbol
        self.tradeSide = tradeSide
        self.targetVol = targetVol
        self.beginTime = beginTime
        self.limitPrice = limitPrice
        self.stopPrice = stopPrice
        self.tradingStyle = tradingStyle

    def getCatsParams(self):
        p = re.compile("__.*__")
        result = ""
        for attr in dir(self):
            if p.search(attr) == None and attr != 'getCatsParams':
                a1 = str(attr) + "=" + str(getattr(self, str(attr))) + ";"
                result += a1

        return result.strip(";")


if __name__ == '__main__':
    print(QMOC3Params().getCatsParams())