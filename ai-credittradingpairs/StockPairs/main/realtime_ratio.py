# -*- coding: utf-8 -*-

'''
@Project : PyCharm
@File : realtime_ratio.py
@Contact : zeyuyue@cicc.com
@author : Joey
@Date : 2021/11/6
@AddTime 2:03 P.M.
'''
import os,sys
path = os.path.dirname(os.path.dirname(os.getcwd()))
sys.path.append(path)
from StockPairs.realtime.RealTimeRatio import RealTimeRatio

if __name__ == '__main__':
    rt = RealTimeRatio()
    rt.run()