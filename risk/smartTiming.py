#!usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file: RiskManager.py
@time: 2020/11/24
"""

import logging
import traceback
import numpy as np
import pandas as pd
from functools import reduce
from configs.Database import mysql, Database, WIND_DB
from collections import defaultdict
from utils.AiData import which_table
from utils.Date import getTradeSectionDates, getTradeDates
from utils.Decorator import func_timer
from risk.futureManager import futureManager
from utils.listTostrforSql import tostr
from configs.tableConfig import asset, initPandasDataFrame

def get_all_main_contract(start='20100101', end='20210530', maincode='IF.CFE'):
    db = Database(WIND_DB)
    sql = "select FS_MAPPING_WINDCODE, S_INFO_WINDCODE, STARTDATE, ENDDATE from wind.CfuturesContractMapping where " \
          " STARTDATE >= {} and ENDDATE <= {} and S_INFO_WINDCODE = '{}' ".format(start, end, maincode)
    db.cursor.execute(sql)
    data = db.cursor.fetchall()
    mapdata = pd.DataFrame(data, columns=['FS_MAPPING_WINDCODE', 'S_INFO_WINDCODE', 'STARTDATE', 'ENDDATE'])
    return mapdata


def get_single_main_contract(mapdata, trade_date, maincode='IF.CFE'):
    # mapdata = pd.DataFrame(data, columns=['FS_MAPPING_WINDCODE', 'S_INFO_WINDCODE', 'STARTDATE', 'ENDDATE'])
    mapdata = mapdata[(mapdata['S_INFO_WINDCODE'] == maincode) &
                      (mapdata['STARTDATE'] <= trade_date) &
                      (mapdata['ENDDATE'] >= trade_date)]
    futurecode = mapdata['FS_MAPPING_WINDCODE'].values[0]
    return futurecode

def add_volitility_sig():
    pass


def spider_web_signal(start, end, rank=20):
    # n_start = getTradeSectionDates(start, 2)[-1]
    # n_end = getTradeSectionDates(end, 2)[-1]
    db = Database(WIND_DB)
    # contract = get_main_contract(trade_date)
    # trade_date_ahead = getTradeSectionDates(trade_date, -1)[0]
    sql = "select TRADE_DT, S_INFO_WINDCODE, FS_INFO_TYPE, FS_INFO_RANK, S_OI_POSITIONSNUMC " \
          "from wind.CIndexFuturesPositions where " \
          " FS_INFO_RANK <= {} and S_INFO_WINDCODE like 'IF%.CFE' " \
          "and TRADE_DT >= {} and TRADE_DT <= {} order by TRADE_DT".format(rank, start, end)
    db.cursor.execute(sql)
    data = db.cursor.fetchall()
    df = pd.DataFrame(data, columns=['trade_dt', 'contract', 'direction', 'rank', 'position_chg'])
    df = df[df.direction != 1]
    l_s = df.groupby(['trade_dt', 'contract', 'direction'])[['position_chg']].sum().reset_index()
    # l_s['new_trade_dt'] = l_s['trade_dt'].apply(lambda x: getTradeSectionDates(x, 2)[-1])
    return l_s


def compute_North_signal(start='20100501', end='20210517', window=20):
    # trade_date = getTradeSectionDates(date, -1)[0]
    db = Database(WIND_DB)
    sql = "select TRADE_DT, VALUE from wind.SHSCDailyStatistics where S_INFO_EXCHMARKET = 'MHN' " \
          "and ITEM_CODE = 293002011 and TRADE_DT >= {} and TRADE_DT <= {} order by TRADE_DT".format(start, end)
    db.cursor.execute(sql)
    data = db.cursor.fetchall()
    north_inflow = pd.DataFrame(data, columns=['trade_dt', 'value'])
    north_inflow['percentile_75_10'] = north_inflow['value'].rolling(window) \
        .apply(lambda x: x.quantile(0.8, interpolation='higher'))
    north_inflow['percentile_95_10'] = north_inflow['value'].rolling(window) \
        .apply(lambda x: x.quantile(0.95, interpolation='higher'))
    north_inflow['percentile_25_10'] = north_inflow['value'].rolling(window) \
        .apply(lambda x: x.quantile(0.2, interpolation='lower'))
    north_inflow['percentile_05_10'] = north_inflow['value'].rolling(window) \
        .apply(lambda x: x.quantile(0.05, interpolation='lower'))
    north_inflow.dropna(inplace=True)
    north_inflow['sig'] = np.where(north_inflow['value'] >= north_inflow['percentile_75_10'], 0.5, np.nan)
    north_inflow['sig'] = np.where(north_inflow['value'] >= north_inflow['percentile_95_10'], 1, north_inflow['sig'])
    north_inflow['sig'] = np.where(north_inflow['value'] <= north_inflow['percentile_25_10'], -0.5, north_inflow['sig'])
    north_inflow['sig'] = np.where(north_inflow['value'] <= north_inflow['percentile_05_10'], -1, north_inflow['sig'])

    north_inflow.fillna(0, inplace=True)
    return north_inflow


def compute_HS300_positon(start='20100101', end='20210521', index_code='000300.SH', window=5):
    db = Database(WIND_DB)
    sql = "select TRADE_DT, S_DQ_CLOSE from wind.AIndexEODPrices where S_INFO_WINDCODE = '{}' " \
          "and TRADE_DT >= {} and TRADE_DT <= {} order by TRADE_DT".format(index_code, start, end)
    db.cursor.execute(sql)
    data = db.cursor.fetchall()
    df = pd.DataFrame(data, columns=['trade_dt', 'close'])
    df['ma_n'] = df['close'].rolling(window).mean()
    df = df.dropna()
    df['position'] = df['close'] / df['ma_n']
    df['ratio'] = np.where((df['position'] < 0.95)|(df['position'].shift() < 0.95)|(df['position'].shift(2) < 0.95)
                           |(df['position'].shift(3) < 0.95), 0.8, 0.4)

    df['ratio'] = np.where((df['position'] > 1.03)|(df['position'].shift() > 1.03)|(df['position'].shift(2) > 1.03)
                           |(df['position'].shift(3) > 1.03), 0.1, df['ratio'])

    return df


def get_smart_timing(start='20100501', end='20210521'):
    sig_dict = {}
    datelis = getTradeDates(start, end)
    spider = spider_web_signal(start, end)
    north = compute_North_signal(start, end)
    hs300 = compute_HS300_positon()
    all_contract_df = get_all_main_contract()
    for dt in datelis:
        next_date = getTradeSectionDates(dt, 2)[-1]
        contract = get_single_main_contract(all_contract_df, dt)
        # next_contract = get_single_main_contract(all_contract_df, next_date)
        print(next_date)
        spider_sig = spider[(spider.trade_dt == dt) & (spider.contract == contract)]['position_chg'].values
        long_value = spider_sig[0]
        short_value = spider_sig[1]
        if (long_value > 0) and (short_value < 0):
            if (abs(long_value) >= 100) and (abs(short_value) >= 100):
                spidersigs = 1
            else:
                spidersigs = 0.5
        elif (long_value < 0) and (short_value > 0):
            if (abs(long_value) >= 100) and (abs(short_value) >= 100):
                spidersigs = -1
            else:
                spidersigs = -0.5
        else:
            spidersigs = 0

        try:
            north_sig = north[north.trade_dt == dt]['sig'].values[0]
        except:
            north_sig = 0
        hs300_sig = hs300[hs300.trade_dt == dt]['ratio'].values[0]

        sig_dict[next_date] = [north_sig, spidersigs, hs300_sig]
    sig_dict[datelis[0]] = [0, 0, 0]
        sig_dict[next_date] = [north_sig, spidersigs]
    sig_dict[datelis[0]] = [0, 0]
    return sig_dict


if __name__ == '__main__':
    b = get_smart_timing(start='20210521')
    print(b)
    # compute_HS300_positon()
