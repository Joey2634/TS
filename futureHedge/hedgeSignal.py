import pandas as pd
import numpy as np
from utils.Date import getTradeSectionDates, getTradeDates
from utils.Database import *


class Future_Load_Signal():
    """
     get one pair signal for Trade.
     """

    def __init__(self, start_date, end_date, strategy_id, spot='510300.SH'):
        self.code = spot
        self.strategy_id = strategy_id
        self.start_date = start_date
        self.end_date = end_date

    def get_daily_target_position(self):
        sig_lis = []
        trade_dates = getTradeDates(self.start_date, self.end_date)
        for date in trade_dates:
            sig_lis.append([self.strategy_id, date, self.code, 1, 0.95])
        return sig_lis

    def delete_target_position(self, env='dev'):
        with mysql(env) as cursor:
            cursor.execute("delete from target_position_backtest "
                           "where strategy_id = '{}' ".format(self.strategy_id))

    def store_target_position(self, table, rows, env='dev'):
        with mysql(env) as cursor:
            cursor.executemany("insert into {} values (%s,%s,%s,%s,%s)".format(table), rows)

def spider_web_signal(contract, trade_date, rank=20):
    db = Database(WIND_DB)
    trade_date_ahead = getTradeSectionDates(trade_date, -1)[0]
    sql = "select TRADE_DT, FS_INFO_MEMBERNAME, FS_INFO_TYPE, FS_INFO_RANK, S_OI_POSITIONSNUMC from wind.CIndexFuturesPositions where " \
          " FS_INFO_RANK <= {} and S_INFO_WINDCODE = '{}' " \
          "and TRADE_DT >= {} and TRADE_DT <= {} order by TRADE_DT".format(rank, contract, trade_date_ahead,
                                                                           trade_date)

    db.cursor.execute(sql)
    data = db.cursor.fetchall()
    df = pd.DataFrame(data, columns=['trade_dt', 'name', 'direction', 'rank', 'position_chg'])
    df =df[df.direction != 1]
    l_s = df.groupby('direction')[['position_chg']].sum()
    print(df, '\n'*3, l_s,l_s.loc[2].values[0])
    long_value = l_s.loc[2].values[0]
    short_value = l_s.loc[3].values[0]

    if (long_value > 0) and (short_value < 0):
        return 1
    elif (long_value < 0) and (short_value > 0):
        return -1
    else:
        return 0



if __name__ == '__main__':
    # fut_load = Future_Load_Signal('20150101', '20210515', 'F_H_3|LastPrice|CLOSE|RISK-h19')
    # fut_load.delete_target_position()
    # lis = fut_load.get_daily_target_position()
    # print(lis)
    # fut_load.store_target_position('target_position_backtest', lis)

    spider_web_signal('IF1007.CFE', '20100622')
