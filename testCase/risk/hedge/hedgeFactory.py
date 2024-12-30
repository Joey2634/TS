# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2021/6/2 下午3:22
# @Author : lxf
# @File : hedgeFactory.py
# @Project : ai-investment-manager

from risk.hedge.hedgeManager import hedgeManager

def get_hedgeManager(key, params):
    if key == 'default':
        return hedgeManager(params)