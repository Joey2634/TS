# coding=utf-8'
import numpy as np
import datetime
import math
import pandas as pd
from configs.Database import mysql
from utils.AiData import fill_account_type, getFutureData, getPriceData, getFutureCode, getTradeSectionDates, \
     getPreDayDict


class PerformanceIndex:

    """
        Description：定义的一些计算评价指标的算法,和自定义算法
        :param returns:AI_Data返回的数据的涨跌幅部分
        :param start_day: 开始时间,例如:'2017-11-01'
        :param end_day: 结束时间,例如:'2017-12-05'
        :param rfr:夏普指数，夏普比率计算参数,例如0.0001
        :returns ：九种评价指标算法结果
    """
    def __init__(self, returns, start_day, end_day, rfr):


        self.rfr = rfr
        self.returns = returns
        self.start_day = start_day
        self.end_day = end_day
        self.days = self.get_days()
        self.func_index = {
            "total_returns": self.total_return,
            "annual_return": self.annualized_return,
            "avg_year_return": self.average_year_returns,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "longest_max_drawdown_duration": self.max_drawdown,
            "max_drawdown_5bd": self.max_short_term_drawdown,
            "max_drawdown_20bd": self.max_short_term_drawdown,
            "avg_daily_return": self.average_daily_returns,
            "std_dev_daily_return": self.volatility,
            'beta_300': self.beta,
            'beta_500': self.beta,
            'alpha_300': self.alpha,
            'alpha_500': self.alpha,
            'win_p': self.win_prob
            }

    # 将传过来的时间进行处理，得到能够计算的时间
    def get_days(self):
        start1 = datetime.datetime.strptime(self.start_day, '%Y%m%d')
        end1 = datetime.datetime.strptime(self.end_day, '%Y%m%d')
        days = (end1 - start1).days + 1  # 包含资金进账日
        return days

    # 最大回撤cumprod()返回的是累积连乘结果,最大回撤率(%)
    # returns是pandas的结构中的某一列的所有的值

    def max_drawdown(self, returns):
        r = returns.add(1).cumprod()
        # 数据除以累计最大值-1
        dd = r.div(r.cummax()).sub(1)
        # 最小值
        mdd = dd.min()
        # 最小值对应索引位置
        end = dd.idxmin()
        # 最小值索引之前的最大值索引
        start = r.loc[:end].idxmax()
        # 最大回撤周期
        duration = (datetime.datetime.strptime(end, '%Y%m%d') - datetime.datetime.strptime(start, '%Y%m%d')).days
        return 100*(round(mdd, 4)), start, end, duration

    # 最大短期回撤
    def max_short_term_drawdown(self, days_new):
        mdd_short = 0.0
        start_day = ''
        end_day = ''
        dur = 0
        for i in range(0, self.returns.index.size):
            df = self.returns[i:i + days_new]
            # self.returns = df
            mdd, start, end, duration = self.max_drawdown(df)
            # res = self.max_drawdown()

            if mdd < mdd_short:
                mdd_short = mdd
                start_day = start
                end_day = end
                dur = duration
        return mdd_short, start_day, end_day, dur

    # 累计收益率-复利(%)
    def total_return(self):
        accReturn = self.returns.add(1).cumprod()
        return 100 * (round(accReturn[-1] - 1, 4))

    # 年化利率-复利(%)
    def annualized_return(self):
        accReturn = self.returns.add(1).cumprod()
        return 100 * (round(pow(accReturn[-1], 365.0 / self.days) - 1, 4))

    # 日平均收益率-非复利(%)---------减去周末时间
    def average_daily_returns(self):
        average_daily_returns = self.returns.sum() / self.days
        return 100 * (round(average_daily_returns, 4))

    # 年平均收益率-非复利(%)
    def average_year_returns(self):
        average_year_returns = self.returns.sum() * 365.0 / self.days
        return 100 * (round(average_year_returns, 4))

    # 日平均波动率(%)
    def volatility(self):
        accReturn = self.returns.std()
        return 100 * (round(accReturn, 4))

    # 夏普指数，夏普比率,夏普率(越大越好)
    def sharpe_ratio(self):
        if self.returns.std() == 0:
            a = 0.000001
        else:
            a = 0
        return round(math.sqrt(252) * (self.returns.mean() - self.rfr) / (self.returns.std() + a), 2)

    # 索丁诺比率,索提诺率(越大越好)
    def sortino_ratio(self):
        Ret = self.returns.values
        ER = np.mean(Ret)
        DOWN_RISK = np.sqrt(np.mean(np.power(np.minimum(Ret, self.rfr), 2)) / np.size(Ret))
        if DOWN_RISK == 0:
            DOWN_RISK += 0.000001
        sortino = ER / DOWN_RISK
        return round(sortino, 2)

    def beta(self, benchmark):
        '''
        计算Beta:cov/var
        :param benchmark:
        :return:
        '''
        if benchmark.empty:
            return 0
        res_df = pd.DataFrame({'strategy':self.returns, 'benchmark':benchmark})
        res = res_df.cov()
        beta = res.iat[0, 1] / res.iat[1, 1]
        return beta

    def alpha(self, beta, annual_return, benchmark):
        '''
        计算alpha: strategy_return-beta*benchmark_return
        :param beta:
        :param annual_return:
        :param benchmark:
        :return:
        '''
        if benchmark.empty:
            return 0
        accReturn = benchmark.add(1).cumprod()
        annual_benchmark = 100 * (round(pow(accReturn[-1], 365.0 / self.days) - 1, 4))
        alpha = annual_return - beta * annual_benchmark
        return alpha / 100

    # 胜率(%)
    def win_prob(self):
        returns = self.returns[1:]
        res = sum(np.where(returns > 0, 1, 0))/len(returns)
        return res

    @staticmethod
    def turnover(strategy_ids=[], env='dev', start_date='', end_date='', mode='SS', backtest=False, n=2):
        '''
        获取策略换手率
        :param strategy_ids:list
        :param env:
        :param start_date:
        :param end_date:
        :param n: 期货换手总交易额/月初总资产
        :param backtest:
        :return:
        '''
        table = 'asset_backtest' if backtest else 'asset'
        strategy_id = str(strategy_ids).replace('[', ''). replace(']', '')
        # 拿<=end_date的数据,扣掉货币基金
        with mysql(env, cursor_type='dict') as cursor:
            cursor.execute("select strategy_id, trade_date, sod_total_asset from {} where strategy_id in ({}) and "
                           "trade_date>='{}' and trade_date<='{}'".format(table,strategy_id,start_date,end_date))
            total_asset = pd.DataFrame(cursor.fetchall())
            table = 'trade_backtest' if backtest else 'trade'
            cursor.execute("SELECT strategy_id, windcode,trade_date, notional,volume FROM {} where strategy_id in ({}) "
                           "and trade_date>='{}'and trade_date<='{}' and windcode not in ('511880.SH')".format(table, strategy_id,  start_date, end_date))
            notional_df = pd.DataFrame(cursor.fetchall())
        notional_df['type'] = notional_df.apply(fill_account_type, axis=1)
        cash = notional_df[notional_df['type'] == 'CASH'][['strategy_id','notional']].groupby('strategy_id').sum()
        asset = total_asset[['strategy_id', 'sod_total_asset']].groupby('strategy_id').sum()
        res = pd.merge(asset, cash, left_index=True, right_index=True, how='left')
        res.fillna(0, inplace=True)
        res['value'] = round(res['notional'] / res['sod_total_asset'] * 100 * 252, 2)
        res['value'] = res['value'].astype(str)
        res['account_type'] = 'CASH'
        res['mode'] = mode
        res = res.reset_index()[['strategy_id', 'account_type', 'mode', 'value']].values.tolist()

        notional_df['trade_date'] = notional_df['trade_date'].map(lambda x: str(x).replace('-',''))
        notional_df_future = notional_df[notional_df['type'] == 'FUTURE'].copy()
        if not notional_df_future.empty:
            #拿出月末总资产
            total_asset['month'] = total_asset['trade_date'].map(lambda x: str(x.year)+str(x.month))
            total_asset['trade_date'] = total_asset['trade_date'].map(lambda x: str(x).replace('-', ''))
            start_date = getTradeSectionDates(total_asset['trade_date'].min(), -2)[0]  # 往前取一天，拿前收
            end_date = total_asset['trade_date'].max()
            total_asset = total_asset.drop_duplicates('month', keep='first')
            data, df, multi = getFutureData(env, strategy_ids)
            total_asset['maincode'] = total_asset['strategy_id'].map(lambda x: data[x])  # 拼主力合约
            total_asset['future_code'] = total_asset.apply(getFutureCode, axis=1, mapdata=df) # 拼映射合约
            total_asset['multi'] = total_asset['future_code'].map(lambda x: multi[x])  # 拼合约乘数

            # 拿映射合约行情 total_asset拼接前收
            date_dict = getPreDayDict(start_date, end_date)
            total_asset['price_date'] = total_asset['trade_date'].map(lambda x: date_dict[x])
            price = getPriceData(total_asset['future_code'].unique(), start_date, end_date)[['S_INFO_WINDCODE','TRADE_DT','S_DQ_CLOSE']]
            price.rename(columns={'S_INFO_WINDCODE':'future_code', 'TRADE_DT':'price_date'}, inplace=True)
            total_asset = pd.merge(total_asset, price, on=['future_code', 'price_date'])
            # 算每月合约最大交易张数
            total_asset['maxVolume'] = total_asset.apply(lambda x: math.ceil(n * x['sod_total_asset'] / x['multi'] / x['S_DQ_CLOSE']), axis=1)
            tmp = pd.merge(notional_df[['strategy_id', 'trade_date']], total_asset[['strategy_id', 'trade_date', 'maxVolume']], on=['strategy_id', 'trade_date'], how='left')
            if np.isnan(tmp.loc[0, 'maxVolume']):  # 首日无值取第一个值
                tmp.loc[0, 'maxVolume'] = total_asset.loc[0, 'maxVolume']
            tmp = tmp.fillna(method='ffill').drop_duplicates()

            notional_df_future = pd.merge(notional_df_future, tmp, on=['strategy_id', 'trade_date'], how='left')
            notional_df_future['date'] = notional_df_future['trade_date'].map(lambda x: datetime.datetime.strptime(x, '%Y%m%d'))
            notional_df_future['week'] = notional_df_future['date'].map(lambda x:str(x.year)+str(x.week))
            notional_df_future = notional_df_future.groupby(['strategy_id', 'week']).agg({'volume':'sum', 'maxVolume':'first'})
            notional_df_future.reset_index(inplace=True)
            # 计算每周比例
            notional_df_future['ratio'] = notional_df_future['volume'] / notional_df_future['maxVolume'] * 100
            future_turn_ratio = notional_df_future.groupby('strategy_id').agg({'ratio':['max', 'mean']})
            for index, row in future_turn_ratio.iterrows():
                res.append([index, 'FUTURE', mode, str(round(row[('ratio','max')],2))+'/' + str(round(row[('ratio','mean')],2))])
        return res


if __name__ == '__main__':
    PerformanceIndex.turnover(['S-L-3|LastPrice|CLOSE|RISK-369|'], 'dev', '20100430','20210521', mode='SS',backtest=True)

