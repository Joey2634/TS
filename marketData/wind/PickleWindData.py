import os
import sys
now_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(now_path)

import _pickle
import multiprocessing
import os

from configs.Database import *
import time
import pandas as pd
from marketData.wind import *

"""
按年 标的录入pickle
"""


def pickleWindData(table, year):
    """
    wind oracle ---> pickle
    """
    oracle = Database(WIND_DB)
    start_date = year+'0101'
    end_date = year+'1231'

    date_field = getDateField(table)
    # 字段名
    print('获取{}表字段名...'.format(table))
    sql1 = "select COLUMN_NAME from all_tab_columns where table_name =upper('{}')".format(table)
    oracle.cursor.execute(sql1)
    columns = oracle.cursor.fetchall()
    columns = [i[0] for i in columns]

    # 当前年份数据
    print('获取{}年--{}表数据...'.format(year, table))
    # 获取sql语句
    sql = "select {} FROM wind.{} where {} >= '{}' and {}<='{}'" \
        .format(','.join(columns), table, ','.join(date_field), start_date, ','.join(date_field),end_date)
    oracle.cursor.execute(sql)
    data = oracle.cursor.fetchall()
    oracle.cursor.close()
    oracle.conn.close()

    # 剔除 字段OBJECT_ID
    print('剔除字段OBJECT_ID...')
    df = pd.DataFrame(data, columns=columns)  # 拿到全年数据df
    if 'OBJECT_ID' in columns:
        df.drop(['OBJECT_ID'], axis=1, inplace=True)
        columns.remove('OBJECT_ID')

    # os.system('cd /home/li/Market_Data && mkdir -p {}/{} '.format(table, year))
    os.system('cd /share_data/Wind_Data && mkdir -p {}/{} '.format(table, year))
    code_list = sorted(set(df.S_INFO_WINDCODE.values.tolist()))
    for code in code_list:
        try:
            print('存储{}表,{}年, {}标的中...'.format(table, year, code))
            # with open('/home/li/Market_Data/{}/{}/{}.pkl'.format(table, year, code), 'wb') as f:
            with open('/share_data/Wind_Data/{}/{}/{}.pkl'.format(table, year, code), 'wb') as f:
                df_res = df[df['S_INFO_WINDCODE'] == code]
                _pickle.dump(df_res, f, protocol=-1)
        except Exception as e:
            print(e, '{}表,{}年, {}标的数据不存在...'.format(table, year, code))


def getDateField(table):
    """
    获取各表日期字段
    """
    if table in table_members:
        date_field = 'S_CON_INDATE'
    elif table in table_ann_dt:
        date_field = 'ANN_DT'
    elif table in table_trade_days:
        date_field = 'TRADE_DAYS'
    elif table in table_trade_date:
        date_field = 'TRADE_DATE'
    elif table in table_listdate:
        date_field = 'S_INFO_LISTDATE'
    elif table in table_occurrence_date:
        date_field = 'OCCURRENCE_DATE'
    elif table in table_report_period:
        date_field = 'REPORT_PERIOD'
    elif table in table_est_dt:
        date_field = 'EST_DT'
    elif table in table_f_est_date:
        date_field = 'F_EST_DATE'
    elif table in table_price_date:
        date_field = 'PRICE_DATE'
    elif table in table_f_prt_enddate:
        date_field = 'F_PRT_ENDDATE'
    elif table in table_rating_date:
        date_field = 'RATING_DT'
    else:
        date_field = 'TRADE_DT'
    return list((date_field, ))


def getCodeField(table):
    """
    获取windcode字段
    """
    if table in f_info_windcode_table:
        code_field = 'F_INFO_WINDCODE'
    else:
        code_field = 'S_INFO_WINDCODE'
    return code_field


def multiRun(table_names, years):
    """
    多进程调用函数
    """
    result = []
    pool = multiprocessing.Pool()
    for table in table_names:
        for year in years:
            result.append(pool.apply_async(pickleWindData, (table, year)))
    pool.close()
    pool.join()


if __name__ == '__main__':

    t = time.time()
    # 日频更新的表
    daily_data = ['AIndexEODPrices', 'AShareEODPrices', 'ChinaClosedFundEODPrice', 'HKIndexEODPrices',
                  'HKshareEODPrices', 'AIndexWindIndustriesEOD', 'AIndexIndustriesEODCITICS', 'ASWSIndexEOD',
                  'ChinaOptionEODPrices', 'CBondFuturesEODPrices', 'CIndexFuturesEODPrices',
                  'CCommodityFuturesEODPrices',
                  'AShareEODDerivativeIndicator', 'AShareTechIndicators', 'AShareEnergyindexADJ',
                  'AshareintensitytrendADJ',
                  'AShareL2Indicators', 'AShareswingReversetrendADJ', 'AShareTechIndicators', 'AShareYield',
                  'PITFinancialFactor', 'RevenueTechnicalFactor', 'TurnoverTechnicalFactor', 'SIndexPerformance',
                  'AShareConsensusRollingData', 'AShareStockRatingConsus',
                  'TrendRiskFactor', 'AIndexValuation', 'ConsensusExpectationFactor', 'AShareMoneyFlow'
                  ]
    # 行情表
    eod_data = ['AIndexEODPrices', 'AShareEODPrices', 'ChinaClosedFundEODPrice', 'HKIndexEODPrices',
                'HKshareEODPrices', 'AIndexWindIndustriesEOD', 'AIndexIndustriesEODCITICS', 'ASWSIndexEOD',
                'ChinaOptionEODPrices', 'CBondFuturesEODPrices', 'CIndexFuturesEODPrices', 'CCommodityFuturesEODPrices']
    table_names = eod_data
    years = ['2020']
    for table in table_names:
        for year in years:
            print('pickle---', table, year)
            pickleWindData(table, year)
    print('耗时:---', time.time()-t)

    # 多进程run
    table_names = eod_data
    years = ['2020']
    multiRun(table_names, years)

    # # 读取比较
    # t = time.time()
    # with open('/home/li/wind_pickle_data/Stock_Eod_Prices-2010.pkl', 'rb') as f:
    #     dd = _pickle.load(f)
    #     # print(dd)
    # print('本地耗时:---', time.time()-t)
    #
    # t = time.time()
    # with open('/data2/Stock_Eod_Prices/Stock_Eod_Prices-2010.pkl', 'rb') as f:
    #     dd = _pickle.load(f)
    #     # print(dd)
    # print('共享耗时:---', time.time()-t)










