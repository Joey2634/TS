# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2021/2/24 下午8:07
# @Author : lxf
# @File : hedgeRatiotest.py
# @Project : ai-investment-manager


def calucateStockHedgeRatio(marginRatio, maxChange=0.1, orginPosition=1.0, hedgeRatio=1.0):
    """
    x:stockPositionRatio # 股票占比
    y:futurePositionRatio # 空头期货保证金占比
    z:cashRatio #
    r:marginRatio
    h:空头对冲多头的比例
    {x+y+z=1
     x*h=y/r
     z>=y/r*maxChange*1.1}  1.1的意思是  maxChange扣的钱+持仓亏损需要补的保证金
     解得:
        x <= 1/(1+h*r+h*maxChange*1.1) // 0.001 /1000 截取三位小数,既对0.001取整然后除以1000.
    :param marginRatio: 保证金率
    :param maxChange:最大跌幅
    :return:
    """
    stockPositionRatio = min((1 / (1 + hedgeRatio * marginRatio + hedgeRatio * maxChange * 1.1)),
                             orginPosition)
    futurePositionRatio = stockPositionRatio * marginRatio * hedgeRatio
    cashRatio = 1 - stockPositionRatio - futurePositionRatio
    return stockPositionRatio, futurePositionRatio, cashRatio


def calucateFutureBlanceRatio(marginRatio, maxChange=0.1, cash_need_move=0):
    """
    :param marginRatio: 保证金率
    :param maxChange:最大跌幅
    :param cash_need_move: 需要给多头移动的钱所占期货资产的比例
    期货自平衡，既期货满仓，保证不爆仓的保证金和现金占比

    x = futureBond      # 期货持仓占用保证金
    y = cash            # 现金
    r = marginRatio     # 保证金比例
    z = cash_need_move
    x + y +z = 1
    y >= x /r*maxChange + x*maxChange
    解得： x <= 1-z/(1+maxChange/r+maxChange)
    """
    futureBond = (1 - cash_need_move) / (1 + maxChange / marginRatio + maxChange)
    cash = 1 - futureBond
    return futureBond, cash



if __name__ == '__main__':
    print(
        calucateStockHedgeRatio(marginRatio=0.12,hedgeRatio=0.4),
        # calucateStockHedgeRatio(marginRatio=0.12, hedgeRatio=0.8)
    )
    print(calucateFutureBlanceRatio(0.4,0.1))