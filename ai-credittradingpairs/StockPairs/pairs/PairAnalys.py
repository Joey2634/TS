# -*- coding: utf-8 -*-

'''
@Project : PyCharm
@File : PairAnalys.py
@Contact : cuiweijian@citics.com
@author : Simon
@Date : 2020/10/12
@AddTime 下午5:28
'''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import coint
from scipy.stats import pearsonr

from pairs.Get_fee_TickData import Load_Tick_data, Load_spread, Allocate_money, get_fee, get_short_stock_fee
from utils.Database import *
from utils.Wheels import getWindcodesByIndex, load_data, standardization
from pairs.PairsChoose import PairsChoose
from AI_Data.queryDBData import getTradeDates, getTradeSectionDates
from utils.Config import ENV
from statsmodels.tsa.stattools import adfuller

trade_dict = {}


class PairAnalys(object):

    def __init__(self, codeA, codeB, start_date, end_date):
        self.codeA = codeA
        self.codeB = codeB
        self.pairs_id = self.getpairs_id()

        self.trade_date_list = getTradeDates(start_date, end_date)
        self.dataseriesA = load_data(codeA, start_date, end_date)
        self.dataseriesB = load_data(codeB, start_date, end_date)

        self.datadf = pd.DataFrame([self.dataseriesA, self.dataseriesB]).T
        self.datadf.columns = [self.codeA, self.codeB]

    def getpairs_id(self):
        return self.codeA.split('.')[0] + self.codeB.split('.')[0]

    # 该端口可以检验多种属性，如斜率，截距，P-value
    def check_data(self):
        # 测试相关性和协整关系
        _, pv_coint, _ = coint(self.dataseriesA, self.dataseriesB)
        _, pv2, _ = coint(self.dataseriesB, self.dataseriesA)
        corr, pv_corr = pearsonr(self.dataseriesA, self.dataseriesB)
        print("Cointegration pvalue : %0.4f" % pv_coint)
        print("Correlation coefficient ： %0.4f" % (corr))

    # 画出股票的整体走势图
    def plot_PairStock_Price(self):
        self.datadf.plot(figsize=(10, 8), subplots=True, title='Pair_Stock_Price_Trend', grid=True)
        plt.show()

    def plot_Price_Scatter(self):
        plt.figure(figsize=(10, 8))
        plt.title('Pair_Stock_Correlation')
        plt.plot(self.datadf[self.codeA], self.datadf[self.codeB], '.')
        plt.xlabel('codeA')
        plt.ylabel('codeB')
        plt.show()

    def get_Intercept(self, multiiple=2, plotOrNot=False):

        S1 = self.datadf[self.codeA]
        S2 = self.datadf[self.codeB]
        [slope, intercept] = np.polyfit(S2, S1, 1).round(multiiple)
        intcpt = S1 - (S2 * slope + intercept)

        if plotOrNot:
            plt.figure(figsize=(10, 5))
            plt.title("Ratios histogram")
            plt.ylabel('Frequency')
            plt.xlabel('Intervals')
            intcpt.plot()
            plt.show()
        return S1, S2, intcpt

    def plot_ZScore(self, plotOrNot=False):
        _, _, intcpt = self.get_Intercept(plotOrNot)
        zScore = (intcpt - intcpt.mean()) / intcpt.std()
        if plotOrNot:
            zScore.plot(figsize=(12, 6))
            plt.axhline(zScore.mean(), color='black')
            plt.axhline(1.0, color='red', linestyle='--')
            plt.axhline(-1.0, color='green', linestyle='--')
            plt.legend(['Ratio z-score', 'Mean', '+1', '-1'])
            plt.title("zScore time series")
            plt.xlabel('Date')
            plt.ylabel('Intervals')
            plt.show()
            plt.figure(figsize=(12, 6))
            zScore.hist(bins=200)
            plt.title("zScore histogram")
            plt.ylabel('Frequency')
            plt.xlabel('Intervals')
            plt.show()
        return zScore

    def test_shapiro(self):
        # stat1, p1 = shapiro(data["stock_portfolio"])
        pass

    def test_ADF(self):
        test_result = adfuller(self.get_Intercept()[-1])
        if test_result[1] < 0.01:
            print('强平稳性，1%置信度')
            return True
        elif test_result[1] < 0.05:
            print('中平稳性，5%置信度')
            return True
        else:
            return False

    def gen_zscore(self, i, data):
        df = data.iloc[:i]
        df_std = (df - df.mean()) / df.std()
        return df_std.values[-1]

    # (1）止损设定3%~5%没有影响
    # (2) scale从3>>5,平仓带越窄收益越高，回撤越小，5>>6，效果反转
    # (3)通过设定每个股票对总资金的30%回撤，不会影响正收益，能够大幅度降低负收益
    # (4) 加入佣金之后，信号频率高股票亏损明显
    # （5）止损金设定比例，从3%到8%调整，

    def Pairs_Tick(self, time, pair_num, precision=2, thresh_u=1, thresh_d=1, scale=5,
                   stop_loss_ratio=0.08):
        Stock_Pair_dict = {}
        PC_flag = False
        break_flag = False
        RQ_flag = False
        PC_num = 0
        Tick_df, slope = Load_spread(time, self.codeA, self.codeB)
        S1 = Tick_df[self.codeA]
        S2 = Tick_df[self.codeB]
        Timestamp = Tick_df['timestamp']
        spread = Tick_df['spread']
        times = 100 * (10 ** (precision))
        # 配对交易详情
        trade_detail = {}
        para_df = self.gen_Trade_df()

        if trade_dict and len(para_df[(para_df.S1 == self.codeA) & (para_df.S2 == self.codeB)]) != 0:
            para_df = para_df[(para_df.S1 == self.codeA) & (para_df.S2 == self.codeB)]
            para_df = para_df.sort_values(by=['time', 'timestamp'], ascending=[False, False])
            countS1 = para_df['countS1'].values[0]
            countS2 = para_df['countS2'].values[0]
            money = para_df['money'].values[0]
            m0 = money
            RQ_flag = True
        else:
            # S1仓位
            countS1 = 0
            # S2仓位
            countS2 = 0
            # 资金分配端口
            money = Allocate_money(pair_num)
            m0 = money

        # 换手次数
        trade_num = 0
        month_lis = [[Timestamp[0], money]]
        length = len(spread)
        for i in range(length - 1):
            if i < 1:
                continue
            z_value = self.gen_zscore(i, spread)
            # 如果信号 zscore > 1，那么short s1（s1仓位-1）,得到的钱long s2*spread（s1仓位+1*spread）。

            if PC_flag:
                change_money = countS1 * S1[i + 1] + countS2 * S2[i + 1]
                money += change_money
                if countS1 > 0:
                    money -= countS1 * S1[i + 1] * get_fee(self.codeA, 'S')
                elif countS1 < 0:
                    money -= countS2 * S2[i + 1] * get_fee(self.codeB, 'S')
                RQ_flag = False
                print('执行止损，', '时间：', Timestamp[i + 1], '股票：', self.codeA, '原数量：', countS1, '做空股票：', self.codeB, \
                      '原数量：', countS2, '\n', '交易资金量：', change_money, '交易后资金余额：', money)
                trade_detail[(self.codeA, self.codeB, time, Timestamp[i + 1])] = [countS1, countS2, change_money, money]
                # 止损之后，将开仓阈值放大到原来的1.1倍
                if countS1 > 0:
                    thresh_d *= 1.1
                elif countS1 < 0:
                    thresh_u *= 1.1
                # 将仓位归0
                countS1 = 0
                countS2 = 0
                trade_num += 1
                if break_flag:
                    print('该股票对当日已经到达日止损线，清仓！')
                    Stock_Pair_dict[(self.codeA, self.codeB)] = [thresh_u, thresh_d, PC_num, trade_num, m0,
                                                                 month_lis[-1][-1],
                                                                 month_lis[-1][-1] / m0 - 1]
                    return money, month_lis, Stock_Pair_dict, trade_detail
            else:
                if z_value > thresh_u and countS1 == 0:
                    change_money = S1[i + 1] * times - S2[i + 1] * round(slope, precision) * times
                    money += change_money
                    money -= S2[i + 1] * round(slope, precision) * times * get_fee(self.codeB, 'B')
                    print('佣金金额：', S2[i + 1] * round(slope, precision) * times * get_fee(self.codeB, 'B'))
                    countS1 -= times
                    countS2 += round(slope, precision) * times
                    print('触碰上边界，', '时间：', Timestamp[i + 1], '做多股票：', self.codeB, '做空股票：', self.codeA, \
                          '\n', '交易资金量：', change_money, '交易后资金余额：', money)
                    trade_detail[(self.codeA, self.codeB, time, Timestamp[i + 1])] = [countS1, countS2, change_money,
                                                                                      money]
                    print('*.-' * 10)
                    trade_num += 1
                    RQ_flag = True

                # 如果信号zscore < -1，那么short spread*s2,得到的钱long s1。
                elif z_value < thresh_d * -1 and countS1 == 0:
                    change_money = S1[i + 1] * times - S2[i + 1] * round(slope, precision) * times
                    money -= change_money
                    money -= S1[i + 1] * times * get_fee(self.codeA, 'B')
                    print('佣金金额：', S1[i + 1] * times * get_fee(self.codeA, 'B'))
                    countS1 += times
                    countS2 -= round(slope, precision) * times
                    print('触碰下边界，', '时间：', Timestamp[i + 1], '做多股票：', self.codeA, '做空股票：', self.codeB, \
                          '\n', '交易资金量：', change_money, '交易后资金余额：', money)
                    trade_detail[(self.codeA, self.codeB, time, Timestamp[i + 1])] = [countS1, countS2, change_money,
                                                                                      money]
                    print('*.-' * 10)
                    trade_num += 1
                    RQ_flag = True
                # 如果信号zscore处在(-0.5, 0.5)之间，清仓——反向操作，用此刻的价格*此刻的仓位作为清仓的成本。同时仓位清零。
                elif abs(z_value) < (thresh_u + thresh_d) / scale and countS1 != 0:
                    change_money = countS1 * S1[i + 1] + countS2 * S2[i + 1]
                    money += change_money
                    # 扣除卖出股票的交易佣金
                    if countS1 > 0:
                        money -= countS1 * S1[i + 1] * get_fee(self.codeA, 'S')
                    elif countS1 < 0:
                        money -= countS2 * S2[i + 1] * get_fee(self.codeB, 'S')
                    print('触碰平倉边界，', '时间：', Timestamp[i], '股票：', self.codeA, '原数量：', countS1, '做空股票：', self.codeB, \
                          '原数量：', countS2, '\n', '交易资金量：', change_money, '交易后资金余额：', money)
                    trade_detail[(self.codeA, self.codeB, time, Timestamp[i + 1])] = [countS1, countS2, change_money,
                                                                                      money]

                    print('*.-' * 10)
                    countS1 = 0
                    countS2 = 0
                    trade_num += 1
            # 进行止损监控,设定阈值，达到止损线进行平仓
            if (money / month_lis[-1][-1] < 1 - stop_loss_ratio) and (PC_flag == False):
                print('已经触发止损条件，将在下一tick平仓, {},{},损失金额为{}:'.format(self.codeA, self.codeB, month_lis[-1] - money))
                PC_flag = True
                PC_num += 1
            else:
                PC_flag = False

            # 加入融券扣费
            if countS1 < 0 and RQ_flag == True:
                money -= countS1 * S1[i + 1] * get_short_stock_fee() * -1
                RQ_flag = False
            elif countS1 > 0 and RQ_flag == True:
                money -= countS2 * S2[i + 1] * get_short_stock_fee() * -1
                RQ_flag = False
            month_lis.append([Timestamp[i + 1], money])
            if money / m0 < 0.65:
                break_flag = True
        Stock_Pair_dict[(self.codeA, self.codeB)] = [thresh_u, thresh_d, PC_num, trade_num, m0, month_lis[-1][-1],
                                                     month_lis[-1][-1] / m0 - 1]
        return money, month_lis, Stock_Pair_dict, trade_detail

    @staticmethod
    def gen_Trade_df():
        try:
            df = pd.DataFrame(trade_dict)
            df1 = df.T.reset_index()
            df1.columns = ['S1', 'S2', 'time', 'timestamp', 'countS1', 'countS2', 'change_money', 'money']
            return df1
        except:
            print('trade_dict is empty!')
            return 0


def fixed_rslist(time, corr_test_year=2, long_pool_index='000016.SH', short_pool_index='000016.SH'):
    start = str(int(time[:4]) - corr_test_year) + time[4:]
    end = getTradeSectionDates(time, -2)[0]
    p = PairsChoose(start, end, long_pool_index, short_pool_index)
    return p.get_pairlist()


def pair(time, rslist, corr_test_year=2):
    start = str(int(time[:4]) - corr_test_year) + time[4:]
    end = getTradeSectionDates(time, -2)[0]
    print(start, end)
    trade_log = {}
    stockpair_ret_dict = {}
    for lis in rslist:
        print(lis[0], lis[1])
        pa = PairAnalys(lis[0], lis[1], start, end)
        mon = pa.Pairs_Tick(time, len(rslist))
        print('money get:', mon[0])
        print('*-' * 10)
        trade_log.update(mon[-1])  # 记录股票对交易明细
        stockpair_ret_dict.update(mon[2])
    trade_dict.update(trade_log)
    return trade_log, stockpair_ret_dict


# thresh_u, thresh_d, PC_num, trade_num, m0, month_lis[-1][-1],month_lis[-1][-1] / m0 - 1
def Gen_total_df(startdate, enddate, switch=True):
    date_lis = getTradeDates(startdate, enddate)
    total_df = pd.DataFrame()
    rslist = fixed_rslist(startdate)
    for date in date_lis:
        if switch:
            df = pd.DataFrame(pair(date, rslist)[1]).T
            df['date'] = date
            df = df.reset_index()
            df.columns = ['S1', 'S2', 'thresh_u', 'thresh_d', '平仓次数', '日内交易次数', '初始资金', '日末资金', '收益率', '日期']
            total_df = pd.concat([total_df, df], axis=0)
        else:
            df1 = pd.DataFrame(pair(date, rslist)[0]).T
            df1 = df1.reset_index()
            df1.columns = ['S1', 'S2', '日期', '时间戳', 'S1持仓量', 'S2持仓量', '交易金额', '资金存量']
            total_df = pd.concat([total_df, df1], axis=0)
    return total_df


if __name__ == '__main__':
    a = pair('2020-11-06', fixed_rslist('2020-11-06'))
    # print(trade_dict)
    b = PairAnalys.gen_Trade_df()
    # print(b)
    c = b[(b.S1 == '600016.SH') & (b.S2 == '600000.SH')].sort_values(
        by=['time', 'timestamp'], ascending=[False, False])
    print(c)
