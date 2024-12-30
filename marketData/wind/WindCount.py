import gzip
import os
import sys

import datetime

now_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(now_path)
from utils.AiData import *
import _pickle
import os
from configs.Database import *
import time
import pandas as pd
from marketData.wind import *
import numpy as np
import re


"""
查看全表数据量
"""


def pickleWindData(table):
    """
    wind oracle ---> pickle
    """
    oracle = Database(WIND_DB)

    # 字段名
    sql1 = "select COLUMN_NAME from all_tab_columns where table_name =upper('{}')".format(table)
    oracle.cursor.execute(sql1)
    columns = oracle.cursor.fetchall()
    columns = [i[0] for i in columns]
    if columns:
        sql = "select count(1) from wind.{}".format(table)
        oracle.cursor.execute(sql)
        count_num = oracle.cursor.fetchall()
        print('{},表一共有{}条数据'.format(table, count_num[0][0]))
        if count_num[0][0] > 3000000:
            print('数据量大！！!!!!!!!!!!!!!!!!!!!!!!!, {}'.format(table))

    else:
        print('{},表不存在***'.format(table))
    print('-'*40)


if __name__ == '__main__':
    codes = ['300096.SZ', 'sssss', '600653.SH']
    start_date = '20200101'
    end_date = '20201216'
    data = getWindData(table='AShareEODDerivativeIndicator', code_list=codes,
                       start_date=start_date,
                       end_date=end_date,
                       fields=['S_DQ_MV', 'S_VAL_PB_NEW', 'S_VAL_PE_TTM',
                               'S_VAL_PCF_NCFTTM', 'S_DQ_FREETURNOVER', 'NET_PROFIT_PARENT_COMP_TTM',
                               'OPER_REV_TTM', 'UP_DOWN_LIMIT_STATUS'])



    a = getWindData('AShareEODDerivativeIndicator', ['300096.SZ', 'sssss', '600653.SH'], fields=['S_INFO_WINDCODE'])
    codes = a['S_INFO_WINDCODE'].tolist()
    res = [i for i in codes if not (i.startswith('A') or i.startswith('T'))]
    print(1)




    AI_DB_INFO_PROD = dict(DBTYPE='mysql', HOST='172.23.122.238', USER='aidata', PASSWORD='Aidatactcs630', DBNAME='aidatabase',PORT=3306)

    db = Database(AI_DB['dev'])
    sql = """select trade_date, count(windcode) from security_pool where security_selection_id='{}' and trade_date>='{}' and trade_date<='{}' group by trade_date """ \
        .format('S-L-5', '20150105', '20201125')
    db.cursor.execute(sql)
    data = db.cursor.fetchall()
    df1 = pd.DataFrame(data=list(data), columns=['trade_date', 'code'])

    db = Database(AI_DB_INFO_PROD)
    sql = """select trade_date, count(selection_code) from stock_selection where security_selection_id='{}' and trade_date>='{}' and trade_date<='{}'  group by trade_date""" \
        .format('AI-IM-5', '2015-01-05', '2020-11-25')
    db.cursor.execute(sql)
    data = db.cursor.fetchall()
    df2 = pd.DataFrame(data=list(data), columns=['trade_date', 'code'])
    df2['trade_date'] = df2['trade_date'].apply(
        lambda x: datetime.datetime.strftime(datetime.datetime.strptime(x, '%Y-%m-%d'), '%Y%m%d'))

    df_m = pd.merge(df1, df2, how='left',on=['trade_date'])







    t = time.time()
    table_names = wind_0404

    for table in table_names:
        if table not in stock_futures:
            # print('pickle---', table.upper())
            pickleWindData(table)
    print('耗时:---', time.time()-t)













