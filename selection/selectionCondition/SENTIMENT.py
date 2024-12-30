import pandas as pd
import time
import datetime
import sys
import os
now_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(now_path)
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

from configs.Database import *
from utils.AiData import getATotalST, getATotalStop
from utils.Date import getTradeSectionDates, getTradeDates
from utils.Decorator import func_timer

"""
wind舆情黑名单
"""


class Sentiment(object):
    def __init__(self, env):
        self.env = env
        # 初始化黑名单事件，剔除: 204001002 交易异常 204007010股东减持股票、204007012管理层及相关人士减持股票、204007022股东拟减持股票、204025001股权质押
        # 204105002大股东股权质押补充     204007016限售股份上市流通  等的事件代号
        # 目前只有  204007016限售股份上市流通剔除
        with mysql('share') as cursor:
            cursor.execute("select event_categorycode from black_event_list")
            del_event = set(['204007016'])
            self.event_categorycode = list(set([i[0] for i in list(cursor.fetchall())]) - del_event)

    def get_blacklist(self, trade_date):
        '''
        拿到黑名单
        :param trade_date:
        :return:
        '''
        table = 'a_share_black_new'
        sql = "select distinct anncedate,windcode,event_type from {} where anncedate = '{}' ".format(table, trade_date)
        with mysql('sentiment') as cursor:
            cursor.execute(sql)
            returns_sql = cursor.fetchall()
        df_new_black = pd.DataFrame(data=list(returns_sql), columns=['datetime', 'windcode', 'event_type'])
        df_new_black['source'] = 'wind與情库'
        df_new_black['opdate'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return df_new_black.values.tolist()

    def insertWindUPDB(self, param=[]):
        """
        插入数据库进行展示
        :param param:
        :return:
        """
        if param:
            values = str(('%s',) * len(param[0])).replace("'", "")
            with mysql('sentiment', commit=True) as cursor:
                cursor.execute("delete from black_list_show")
                cursor.executemany("insert into black_list_show values {}".format(values), param)

    def getAShareBlack(self, trade_date):
        """
        获取黑名单，通过自定义的事件查找标的，并剔除停盘、ST以及688开头的新股，并插入数据库
        前一交易日15：00-今日15：00作为今日数据
        :param trade_date:
        :return:
        """
        pre_day = getTradeSectionDates(trade_date, -2)[0]
        # 取数据
        sql = "select a.s_event_anncedate,a.s_info_windcode,c.s_info_name,b.s_typname,a.opdate \
                from asharemajorevent a \
                inner join asharetypecode b on a.s_event_categorycode = b.s_origin_typcode \
                inner join asharedescription c on a.s_info_windcode = c.s_info_windcode \
                where a.s_event_anncedate >= '{}' and a.s_event_anncedate <= '{}' and a.s_event_categorycode in ({})" \
            .format(pre_day, trade_date, str(self.event_categorycode).replace("[", "").replace("]", ""))
        with oracle() as cursor:
            cursor.execute(sql)
            returns_sql = cursor.fetchall()
        # 只选取前一日15：00之后到今日15：00更新的数据
        returns_sql = pd.DataFrame(returns_sql,
                                   columns=['annce_date', 'wind_code', 'info_name', 'event_name', 'opdate'])
        st_stamp = datetime.datetime.strptime(pre_day + str(' 15:00:00'), '%Y%m%d %H:%M:%S')
        t_stamp = datetime.datetime.strptime(trade_date + str(' 15:00:00'), '%Y%m%d %H:%M:%S')
        returns_sql = returns_sql[list(map(lambda x: (x >= st_stamp and x < t_stamp), returns_sql['opdate']))]
        # 调整日期格式
        returns_sql['opdate'] = returns_sql['opdate'].astype(str)
        # 去除ST股、去除停牌
        del_stock = getATotalST(trade_date)['code'].tolist() + getATotalStop(startDay=trade_date, endDay=trade_date)['s_info_windcode'].tolist()
        returns_sql = returns_sql[~(returns_sql['wind_code'].isin(del_stock))]
        # 去除688开头的新股
        returns_sql = returns_sql[~(returns_sql['wind_code'].str.startswith('688'))]
        returns_sql = returns_sql.reset_index(drop=True)

        returns_sql['annce_date'] = trade_date  # 把前一日15：00之后到今日15：00都变成今日，方便回测使用
        returns_sql['selection_id'] = 'sentiment'
        returns_sql['owner'] = 'swj'
        returns_sql['description'] = 'wind與情库'
        # 去重
        returns_sql = returns_sql.drop_duplicates(['annce_date', 'wind_code'])
        res = returns_sql[['selection_id', 'annce_date', 'wind_code', 'owner', 'event_name']].reset_index(drop=True)
        print(len(res))
        res_list = res.values.tolist()
        # 出信息后, 持续五个交易日
        con_date = getTradeSectionDates(trade_date, 6)
        dd = res.copy()
        for day in con_date[1:]:
            dd['annce_date'] = day
            res = res.append(dd)
        # 插入数据
        with mysql(self.env, commit=True) as cursor:
            sql = "select * from black_list_his where selection_id='sentiment' " \
                  "and trade_date>= '{}' and trade_date<= '{}'".format(con_date[0], con_date[-1])
            cursor.execute(sql)
            before_data = cursor.fetchall()
            before_df = pd.DataFrame(list(before_data), columns=res.columns.tolist())
            res = res.append(before_df).drop_duplicates(subset=['annce_date', 'wind_code'])
            cursor.execute("delete from black_list_his where selection_id='sentiment' "
                           "and trade_date>= '{}' and trade_date<= '{}'".format(con_date[0], con_date[-1]))
            cursor.executemany("insert into black_list_his VALUES(%s,%s,%s,%s,%s)", res.values.tolist())

    @func_timer
    def run(self, trade_date, backtest=False):
        # 当日和前一交易日黑名单與情数据存入数据库,回测只考虑当日
        self.getAShareBlack(trade_date)

    def backtest(self, start_date, end_date):
        A_DATE = getTradeDates(start_date=start_date, end_date=end_date)
        for date in A_DATE:
            print(date)
            self.run(date, True)


if __name__ == '__main__':
    # env = 'dev'
    # sentiment = Sentiment(env)
    # start_day = '20150105'
    # end_day = str(datetime.date.today()).replace('-', '')
    # sentiment.backtest(start_day, end_day)
    # 两个环境都更新
    for env in ['prod', 'dev']:
        sentiment = Sentiment(env)
        today = str(datetime.date.today()).replace('-', '')
        t = time.time()
        start_day = '20210203'
        end_day = today
        sentiment.backtest(start_day, end_day)
        print('time spend--', time.time()-t)











