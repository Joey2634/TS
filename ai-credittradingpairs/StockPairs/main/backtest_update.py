# -*- coding: utf-8 -*-

'''
@Project : PyCharm
@File : backtest_update.py
@Contact : zeyuyue@cicc.com
@author : Joey
@Date : 2021/11/6
@AddTime 2:02 P.M.
'''
import os,sys
path = os.path.dirname(os.path.dirname(os.getcwd()))
sys.path.append(path)
from StockPairs.pairs.PairsUpdate import PairsUpdate

if __name__ == '__main__':
    pu = PairsUpdate()
    pu.update()