#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:lucifer
@file: sendOrder.py
@time: 2019/06/04
 """
import os
import sys
import datetime
now_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(now_path)
from utils.Date import getTradeSectionDates
from tradeExecution.sendOrderMock import sendOrderMock
from utils.logger import setup_logging_by_params
setup_logging_by_params('sendOrderMock')

if __name__ == '__main__':
    # 'S-L-5|MaxDiversification|CLOSE|RISK-4'
    # strategyids = ['smart_beta_sz50-1','smart_beta_hs300-1',
    #                'S-L-4|LastPrice|CLOSE|RISK-38',
    #                'turing_1-1','turing_2-1','turing_3-1',
    #                'S-L-4|LastPrice|CLOSE|RISK-169',
    #                'stock_long_2-1','stock_long_1-1',
    #                'L-M-D-1']
    strategyids = ['M-L|LastPrice|CLOSE|RISK-175-2|100M|m19',
                   'M-L|LastPrice|CLOSE|RISK-175-2|100M|lm']
    today = datetime.datetime.now().strftime('%Y%m%d')
    if today in getTradeSectionDates(today, -1):
        sendOrder = sendOrderMock(strategy_ids=strategyids,env='dev',mode='mock')
        sendOrder.run()
