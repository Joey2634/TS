# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2021/4/26 上午9:30
# @Author : lxf
# @File : storeEodData.py
# @Project : ai-investment-manager
import os
import sys
import datetime
now_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(now_path)
from tradingSystem.CATS.catsserverapi.storeEodData import useRootNet
from utils.Date import getTradeSectionDates



today = datetime.datetime.now().strftime('%Y%m%d')
if today in getTradeSectionDates(today, -1):
    useRootNet(env='prod', mode='prod', commit=True)