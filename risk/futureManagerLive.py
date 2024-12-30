# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2021/3/16 上午10:51
# @Author : lxf
# @File : futureManagerLive.py
# @Project : ai-investment-manager

from risk.futureManager import futureManager


class futureManagerLive(futureManager):
    """

    """

    def __init__(self, windInfo, env='dev'):
        super().__init__(windInfo=windInfo, env=env)
        self.loadCashNeedMove()



    def loadCashNeedMove(self):
        pass

