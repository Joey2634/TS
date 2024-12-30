# -*- coding: utf-8 -*-

'''
@Project : PyCharm
@File : PairsUpdate.py
@Contact : cuiweijian@citics.com
@author : Simon
@Date : 2020/11/6
@AddTime 下午1:31
'''
from StockPairs.utils.Database import *
import arrow
from StockPairs.utils.Wheels import get_oneday_data
from AI_Data.queryDBData import getTradeDates
from StockPairs.utils.Config import ENV

class PairsUpdate(object):

    def __init__(self,trade_date=''):
        self.pairs_dict, self.params_dict = self.load_params_dict()
        self.pairs_ids = list(self.pairs_dict.keys())
        self.trade_date = trade_date if trade_date else arrow.now().format('YYYY-MM-DD')

    def load_params_dict(self):
        pairs_dict,params_dict = {},{}
        db = Database(AI_DB[ENV])
        sql_seg = "SELECT pairs_id,stock_long,stock_short,mean,std FROM stockpairs_params;"
        db.cursor.execute(sql_seg)
        all_res = db.cursor.fetchall()
        for res in all_res:
            pairs_dict[res[0]] = [res[1],res[2]]
            params_dict[res[0]] = [float(res[3]),float(res[4])]

        return pairs_dict,params_dict

    def update(self):

        res_list = []
        for id in self.pairs_ids:
            try:
                stockA,stockB = self.pairs_dict.get(id)
                mean,std = self.params_dict.get(id)
                priceA = get_oneday_data(stockA,self.trade_date)
                priceB = get_oneday_data(stockB,self.trade_date)
                ratio = priceA/priceB
                zscore = (ratio-mean)/std
                res_list.append([id,stockA,stockB,self.trade_date,ratio,zscore])
            except Exception as e:
                print(e.__str__())
        db = Database(AI_DB[ENV])
        db.cursor.executemany("insert into stockpairs_backtest values(%s,%s,%s,%s,%s,%s)", res_list)
        db.conn.commit()
        db.cursor.close()
        db.conn.close()


if __name__ == '__main__':
    trade_dates = getTradeDates('2020-10-01','2020-11-04')
    for date in trade_dates:
        pu = PairsUpdate(date)
        pu.update()
        print("done: ",date)