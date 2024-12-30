# -*- coding: utf-8 -*-

'''
@Project : PyCharm
@File : CalcuVol.py
@Contact : cuiweijian@citics.com
@author : Simon
@Date : 2020/10/29
@AddTime 下午3:59
'''
from StockPairs.utils.Database import *
from StockPairs.utils.Config import ENV
def get_ratio(stock,stock_type='LONG',deta=2):
    # 根据标的代码与多空方向,查询比例ratio。
    """
    stock: 万德代码
    stock_type: LONG/SHORT : 多空方向
    deta: ratio精度，默认两位.
    return： ratio/多头标的/空头标的
    """
    db = Database(AI_DB[ENV])
    if stock_type == 'LONG':
        sql_seg = "SELECT ratio,stock_long,stock_short FROM stockpairs_backtest where stock_long='%s' order by trade_date desc limit 1;" % stock
    else:
        sql_seg = "SELECT ratio,stock_long,stock_short FROM stockpairs_backtest where stock_short='%s' order by trade_date desc limit 1;" % stock
    db.cursor.execute(sql_seg)
    res = db.cursor.fetchone()
    print(res)
    if res:
        ratio,stock_long,stock_short = res
    else:
        ratio,stock_long,stock_short = 0,'',''
    ratio = round(ratio, deta)
    # 如果没有该配对,返回0
    return ratio,stock_long,stock_short




def calcu_vol(num,ratio,deta=2):
    # 根据客户输入的量以及ratio，给客户返回对应的对冲标的数量
    res_num = round((num*ratio)/(10**deta))*(10**deta)

    return res_num

if __name__ == '__main__':
    ratio, stock_long, stock_short = get_ratio('600029.SH')
    print(calcu_vol(2700,ratio))