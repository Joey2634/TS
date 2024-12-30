import pandas as pd
import matplotlib.pyplot as plt
from AI_Data.queryDBData import getTradeDates
import numpy as np
from utils.Database import *
from algobacktest.Utility import loadDepthData


def Allocate_money(stock_pair_num, money=100000000):
    return money // stock_pair_num


def loadFeeRate(total_security_list):
    """
    加载费率信息
    :param total_security_list:
    :param strategy_configs:
    :return:
    """
    business_types = ['HS']
    sql = "select business_type,windcode,fee_type,fee_rate from trading_fee_rate where business_type"
    if len(business_types) > 1:
        sql = sql + " in {0}".format(tuple(business_types))
    elif len(business_types) == 1:
        sql = sql + " = '{0}'".format(business_types.pop())
    else:
        exit("Error: No Business Type")
    sql += " and windcode"
    if len(total_security_list) > 1:
        sql = sql + " in {0}".format(tuple(total_security_list))
    elif len(total_security_list) == 1:
        sql = sql + " = '{0}'".format(tuple(total_security_list)[0])
    else:
        exit("Error: No security")
    with mysql(AI_SHARE) as cursor:
        cursor.execute(sql)
        data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['business_type', 'windcode', 'fee_type', 'fee_rate'])
    df['fee_rate'] = df['fee_rate'].astype('float')
    df['BS'] = df['fee_type'].map({'B': 1, 'S': -1})
    return df


def Load_Tick_data(time, code):
    time_int = int(time[:4] + time[5:7] + time[8:10])
    res = loadDepthData('/data1/Depth_NPZ_Raw', time_int, code)
    df = pd.DataFrame(res['timestamp'], res['lastPrice'])
    df.reset_index(inplace=True)
    df.columns = [code, 'timestamp']
    df1 = df[df[code] != 0]
    return df1


def Load_spread(time, code1, code2):
    d0 = Load_Tick_data(time, code1)
    d1 = Load_Tick_data(time, code2)
    dd = pd.merge(d0, d1, on='timestamp')
    [slope, intercept] = np.polyfit(dd[code2], dd[code1], 1).round(2)
    dd['spread'] = dd[code1] - (dd[code2] * slope + intercept)
    # dd = dd.set_index('timestamp')
    return dd, slope


def get_fee(code, typ):
    ff = loadFeeRate([code])
    print(ff)
    return ff[(ff.windcode == code) & (ff.fee_type == typ)]['fee_rate'].values[0]


def get_short_stock_fee(fee=0.0835):
    return fee ** 1 / 252


if __name__ == '__main__':
    a = Load_spread('2018-11-07', '600016.SH', '601360.SH')
    print(a)
    # print(getTradeDates('2011-11-01', '2012-11-01'))
