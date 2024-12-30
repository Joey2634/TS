import os
import sys
now_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(now_path)

import _pickle
import multiprocessing
import os
import datetime
from configs.Database import *
import time
import pandas as pd
from marketData.wind import *

"""
每日更新--- 按年 标的录入pickle
"""


def pickleWindData(table, trade_date):
    """
    wind oracle ---> pickle
    """
    oracle = Database(WIND_DB)
    year = trade_date[:4]

    date_field = getDateField(table)
    code_field = getCodeField(table)
    # 字段名
    print('获取{}表字段名...'.format(table))
    sql1 = "select COLUMN_NAME from all_tab_columns where table_name =upper('{}')".format(table)
    oracle.cursor.execute(sql1)
    columns = oracle.cursor.fetchall()
    columns = [i[0] for i in columns]

    # 当前年份数据
    print('获取{}--{}表数据...'.format(trade_date, table))
    # 获取sql语句
    sql = "select {} FROM wind.{} where {} = '{}'" \
        .format(','.join(columns), table, ','.join(list((date_field,))), trade_date)
    oracle.cursor.execute(sql)
    data = oracle.cursor.fetchall()
    oracle.cursor.close()
    oracle.conn.close()

    # 剔除 字段OBJECT_ID
    print('剔除字段OBJECT_ID...')
    df = pd.DataFrame(data, columns=columns)  # 拿到当日数据df
    if 'OBJECT_ID' in columns:
        df.drop(['OBJECT_ID'], axis=1, inplace=True)
        columns.remove('OBJECT_ID')
    # 所有标的
    code_list = sorted(set(df[code_field].values.tolist()))

    # os.system('cd /home/li/Market_Data && mkdir -p {}/{} '.format(table, year))
    os.system('cd /share_data/Wind_Data && mkdir -p {}/{} '.format(table, year))
    if not code_list:
        print('{}表,{}, 数据尚未更新...'.format(table, trade_date))
    else:
        for code in code_list:
            try:
                print('存储{}表,{}, {}标的中...'.format(table, trade_date, code))

                if not os.path.exists('/share_data/Wind_Data/{}/{}/{}.pkl'.format(table, year, code)):
                    with open('/share_data/Wind_Data/{}/{}/{}.pkl'.format(table, year, code), 'wb') as f:
                        df_final = df[df[code_field] == code]
                        _pickle.dump(df_final, f, protocol=-1)
                else:
                    with open('/share_data/Wind_Data/{}/{}/{}.pkl'.format(table, year, code), 'rb') as f:
                        df_before = _pickle.load(f)
                    with open('/share_data/Wind_Data/{}/{}/{}.pkl'.format(table, year, code), 'wb') as f:
                    # with open('/home/li/Market_Data/{}/{}/{}.pkl'.format(table, year, code), 'wb') as f:
                        df_res = df[df[code_field] == code]
                        df_res = df_res[df_before.columns.tolist()]
                        df_final = df_before.append(df_res).drop_duplicates(subset=[code_field, date_field], keep='last')
                        _pickle.dump(df_final, f, protocol=-1)
            except Exception as e:
                print(e, '{}表,{}, {}标的数据不存在...'.format(table, trade_date, code))


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
    return date_field


def getCodeField(table):
    """
    获取windcode字段
    """
    if table in f_info_windcode_table:
        code_field = 'F_INFO_WINDCODE'
    else:
        code_field = 'S_INFO_WINDCODE'
    return code_field


def multiRun(table_names, trade_date):
    """
    多进程调用函数
    """
    result = []
    pool = multiprocessing.Pool()
    for table in table_names:
        result.append(pool.apply_async(pickleWindData, (table, trade_date)))
    pool.close()
    pool.join()


if __name__ == '__main__':
    # with open('/share_data/Wind_Data/AShareEODPrices/2020/605377.SH.pkl', 'rb') as f:
    # with open('/home/li/Market_Data/{}/{}/{}.pkl'.format('AIndexEODPrices', '2020', '000001.SH'), 'rb') as f:
    #     dd = _pickle.load(f)

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
                'ChinaOptionEODPrices', 'CBondFuturesEODPrices', 'CIndexFuturesEODPrices', 'CCommodityFuturesEODPrices',
                'AShareEODDerivativeIndicator', 'AShareTechIndicators']
    trade_date = datetime.datetime.now().strftime('%Y%m%d')

    # table_names = eod_data
    # table_names = ['HKshareEODPrices']
    # for table in table_names:
    #     print('pickle---', table, trade_date)
    #     pickleWindData(table, trade_date)
    # print('耗时:---', time.time()-t)

    # 多进程run
    table_names = daily_data
    multiRun(table_names, trade_date)
    print('耗时:---', time.time()-t)












