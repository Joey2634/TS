# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2021/6/1 下午8:13
# @Author : lxf
# @File : hedgeManager.py
# @Project : ai-investment-manager


class hedgeManager():
    """

    """

    def __init__(self, params):
        self.params = self._analisys_params(params)



    def need_reset(self):
        """

        """
        upper, lower = self.params['reset']
        upper = float(upper)
        lower = float(lower)
        #todo:调用判断逻辑，返回True/False
        pass

    def get_beta(self):
        """
        key = beta
        """
        return float(self.params['beta'])

    def get_maincode(self):
        maincode = self.params['code']
        return maincode

    def get_futurecode(self, date):
        """
        key:code, 合约代码
        days: 提前多少天更换合约
        """
        maincode = self.params['code']
        days = int(self.params['days'])
        #todo:调用函数获当前日期对应的合约代码


    def _analisys_params(self, params):
        result = {}
        kwargs = params.split(',')
        for param in kwargs:
            key, value = param.split(":")
            result[key] = value
        return result