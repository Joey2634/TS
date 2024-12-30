#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file:storeEodData.py
@time:2020/06/01
"""
import datetime
import traceback
from configs.Database import DEV, PROD, mysql
from tradingSystem.CATS.catsserverapi.UseAITrading.rootNet import rootNet
from utils.Date import getTradeSectionDates


def storeTodb(env, closePricedict):
    if closePricedict:
        rows = list(closePricedict.values())
        with mysql(env=env, commit=True) as cursor:
            sql_clear = "truncate ai_stock_price"
            sql_insert = "insert into ai_stock_price values (%s,%s,%s,%s,%s,%s,%s)"
            cursor.execute(sql_clear)
            cursor.executemany(sql_insert, rows)


def getStrategyIds(env,mode,strategy_ids=None):
    """
    根据 env和 mode 从数据库获取需处理策略id
    """
    if strategy_ids: return strategy_ids

    with mysql(env) as cursor:
        sql = "select distinct strategy_id from strategy_config where mode = %s"
        cursor.execute(sql, mode)
        data = cursor.fetchall()
        return [row[0] for row in data]


def useRootNet(env=DEV,mode='test',commit=False):
    strategy_ids = getStrategyIds(env,mode)
    r = rootNet(env=env,mode=mode,commit=commit)
    try:
        r.getAccountInfoByStrategyidsAndLogin(strategy_ids)
        r.store_account()
        r.store_position()
        r.store_today_trades()
        closePrice = r.storeClosePrice()
    except:
        closePrice = {}
        traceback.print_exc()
    finally:
        r.close()
        pass
    storeTodb(env, closePrice)


if __name__ == '__main__':
    today = datetime.datetime.now().strftime('%Y%m%d')
    if today in getTradeSectionDates(today, -1):
        useRootNet(env='prod',mode='prod',commit=True)
