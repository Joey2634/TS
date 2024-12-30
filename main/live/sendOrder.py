#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:lucifer
@file: sendOrder.py
@time: 2019/06/04
 """
import datetime
import os
import sys
import traceback
now_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(now_path)
from utils.Date import getTradeSectionDates
from utils.logger import setup_logging_by_params
setup_logging_by_params('sendOrderLive')

from tradeExecution.sendOrderLive import sendOrderLive

if __name__ == '__main__':
    try:
        today = datetime.datetime.now().strftime('%Y%m%d')
        if today in getTradeSectionDates(today, -1):
            sendOrder = sendOrderLive(env='prod', mode='prod')
            sendOrder.run(orderType='CASH')
    except:
        traceback.print_exc()
    finally:
        sendOrder.close()