#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file:restartAITWAP3Sell.py
@time:2020/08/31
"""
import os,sys
path1 = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
sys.path.append(path1)
from configs.Database import PROD
from tradingSystem.CATS.catsserverapi.continueByAITWAP3 import resend_to_qmoc3



if __name__ == '__main__':
    resend_to_qmoc3(env=PROD,mode=PROD,trade_side='0',algo_id='QMOC3')

