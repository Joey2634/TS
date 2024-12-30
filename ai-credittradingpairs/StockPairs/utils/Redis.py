# -*- coding: utf-8 -*-

'''
@Project : PyCharm
@File : Redis.py
@Contact : cuiweijian@citics.com
@author : Simon
@Date : 2020/11/3
@AddTime 下午4:57
'''
from StockPairs.utils.Database import *

def getredisconfig(usefor='A_STOCK_MARKET_DEV_BAK'):

    db = Database(AI_DB_INFO_COMMON)
    sql_seg_1 = "select host,db,port,passwd from redis_configs where usefor= %s"
    db.cursor.execute(sql_seg_1, usefor)
    data = db.cursor.fetchall()
    db.cursor.close()
    db.conn.close()
    return data[0]

redis_config_dev = getredisconfig()