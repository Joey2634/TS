# -*- coding: utf-8 -*-

'''
@Project : PyCharm
@File : Wheels.py
@Contact : cuiweijian@citics.com
@author : Simon
@Date : 2020/10/12
@AddTime 上午9:24
'''

from utils.Database import *
from AI_Data.dataSource import DataSource
import arrow
import numpy as np
import logging
import pandas as pd


def getWindcodesByIndex(indus, start_date='20190101'):
    # 通过行业代码获取成分股
    sql_1 = "SELECT S_CON_WINDCODE FROM AINDEXMEMBERS WHERE S_INFO_WINDCODE = '{}' and S_CON_INDATE < {} AND (S_CON_OUTDATE > {} OR S_CON_OUTDATE IS NULL )".format(
        indus, start_date, start_date)

    Oracledatabase = Database(WIND_DB)
    Oracleconn = Oracledatabase.conn
    Oraclecursor = Oracledatabase.cursor
    try:
        Oraclecursor.execute(sql_1)
        data = Oraclecursor.fetchall()
        windcodes = [i[0] for i in data]
    except Exception as e:
        print(str(e))
        windcodes = []
    finally:
        Oraclecursor.close()
        Oracleconn.close()
    return windcodes


def standardization(data):
    # 标准化函数
    """
    :param data: list for number or np.array
    :return: list for number or np.array
    """
    mu = np.mean(data)
    sigma = np.std(data)
    return (data - mu) / sigma


def load_data(wind_code, startdate='2015-06-03', enddate='2020-12-30'):
    ds = DataSource()
    data = ds.getEODData(wind_code, startdate, enddate)

    if isinstance(data, pd.DataFrame):
        close_price = data['CLOSE'].tolist()
        pct_change = data['PCTCHANGE'].tolist()
        timelist = data['DATE'].tolist()
        time_series = [arrow.get(i).format('YYYY-MM-DD') for i in timelist]
    else:
        close_price = []
    return close_price


def get_oneday_data(wind_code, trade_date):
    ds = DataSource()
    data = ds.getEODData(wind_code, trade_date, trade_date)
    return float(data['CLOSE'])


def get_logging(logname='Stockpair'):
    # filepath = os.path.abspath('..')+'/pair/logs/'+logname
    logger = logging.getLogger(logname)
    logger.propagate = False
    if not logger.handlers:
        streamhandler = logging.StreamHandler()
        streamhandler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        streamhandler.setFormatter(formatter)
        logger.addHandler(streamhandler)

    return logger


def move_table():
    table_name1 = 'stockpairs_realtime'
    table_name2 = 'stockpairs_realtime'
    db1 = Database()
    db2 = Database(CREDIT_TRADING_DEV)
    sql_seg1 = "select * from %s" % table_name1
    db1.cursor.execute(sql_seg1)
    all_res = db1.cursor.fetchall()
    db2.cursor.executemany("insert into {} values(%s,%s,%s,%s,%s,%s)".format(table_name2), all_res)
    db2.conn.commit()
    db1.cursor.close()
    db1.close()
    db2.cursor.close()
    db2.close()


TODAY = END_DATE = arrow.now().format('YYYY-MM-DD')
if __name__ == '__main__':
    a = load_data('603259.SH', '2015-01-01', '2017-01-01')
    get_oneday_data('600030.SH', '2020-11-05')
