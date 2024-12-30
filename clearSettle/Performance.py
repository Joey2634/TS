# coding:utf-8
import pandas as pd
from clearSettle.performanceIndex import PerformanceIndex


class Performance(object):
    """ 绩效评估 """

    def __init__(self, strategy_id, benchmark, market_quotes, capm_benchmark=[]):
        """
        Description: 初始化绩效评价
        :param strategy_id: strategy_id
        :param benchmark:wind_codes用来比对的标的
        :param market_quotes:行情
        :param capm_benchmark:资本资产定价模型比较基准list
        """
        self.strategy_id = strategy_id
        self.benchmark = benchmark
        self.capm_benchmark = capm_benchmark
        self.market_quotes = self._setMarketQuotes(market_quotes)
        self.performace_metrics_name_dict = {
            'total_returns': u'累计收益率 (%)',
            'annual_return': u'年化利率-复利(%)',
            'avg_year_return': u'年平均收益率-非复利(%)',
            'sharpe_ratio': u'夏普率(越大越好)',
            'sortino_ratio': u'索提诺率(越大越好)',
            'max_drawdown': u'最大回撤率(%)',
            'longest_max_drawdown_duration': u'最大回撤时长(天)',
            'max_drawdown_5bd': u'5交易日最大回撤(%)',
            'max_drawdown_20bd': u'20交易日最大回撤(%)',
            'avg_daily_return': u'日平均收益率-非复利(%)',
            'std_dev_daily_return': u'日平均波动率(%)',
            'beta_300': u'贝塔系数-沪深300',
            'beta_500': u'贝塔系数-中证500',
            'alpha_300': u'阿尔法-沪深300',
            'alpha_500': u'阿尔法-中证500',
            'win_p': u'胜率'
        }  # 默认的一些评价指标的中文

    def getPerformanceAssessment(self, rfr, data, index_ids=[]):
        """
        Description：绩效评价
        :param index_ids:需要显示的绩效评价指标列表
        :param rfr: risk free rate
        :param data: [date, pctchange]
        :return: 返回一个dataframe格式，根据index的参数返回,默认输出df的index是绩效评价指标，如果不是’index‘的话， df的index是万得代码
        """
        data = data.set_index('date')
        if not index_ids:
            index_ids = self.performace_metrics_name_dict.keys()
        trade_dates = data.index
        # 拼接比较基准行情
        for wind_code in self.benchmark:
            data[wind_code] = self.market_quotes.query("S_INFO_WINDCODE=='{}'".format(
                wind_code)).reset_index().set_index('TRADE_DT').loc[trade_dates[1:], 'pct']  # 第一天为0
        result_db = self.calPerformanceIndex(trade_dates, data, index_ids, rfr)
        return result_db

    def calPerformanceIndex(self, trade_dates, df_strategy, index_ids, rfr):
        '''
        计算绩效指标
        :param trade_dates:
        :param df_strategy: pd.dataframe(columns=['trade_date','涨跌幅数据'...])
        :param index_ids:
        :param rfr:
        :return:
        '''
        result_db = pd.DataFrame()
        # 取CAPM比较基准数据
        benchmark = {}
        for i in self.capm_benchmark:
            benchmark[i] = self.market_quotes.query("S_INFO_WINDCODE=='{}'".format(i)).reset_index().set_index('TRADE_DT').loc[trade_dates, 'pct']
            benchmark[i].iloc[0] = 0
        df_strategy.fillna(0, inplace=True)
        for header in df_strategy.columns:
            result_index = self._indexMap(trade_dates[0], trade_dates[-1], df_strategy[header], index_ids, rfr,
                                          benchmark)
            result_index['strategy_id'] = self.strategy_id
            result_index['benchmark_id'] = self.getBenchmarkName(df_strategy.columns[0], header)
            result_index['start'] = trade_dates[0]
            result_index['end'] = trade_dates[-1]
            result = pd.DataFrame([result_index])
            result_db = result_db.append(result[['strategy_id', 'benchmark_id', 'start', 'end'] + list(index_ids)])
        return result_db

    def getBenchmarkName(self, strategy_name, header):
        if 'year-' in strategy_name and 'year-' not in header:
            return strategy_name + '-' + header
        return header

    # *******************私有方法*********************************

    def _indexMap(self, start_day, end_day, returns, index_id, rfr, benchmark):
        '''
        计算夏普率等需要的分析数据
        '''
        performance_index = PerformanceIndex(returns, start_day, end_day, rfr)
        # 默认的一些index的对应的一些函数
        func_index = performance_index.func_index
        res = {}
        for index_mem in index_id:
            if index_mem == 'max_drawdown_5bd':
                res[index_mem] = func_index[index_mem](5)[0]

            elif index_mem == 'max_drawdown_20bd':
                res[index_mem] = func_index[index_mem](20)[0]

            elif index_mem == 'max_drawdown':
                res[index_mem] = performance_index.max_drawdown(returns)[0]

            elif index_mem == 'longest_max_drawdown_duration':
                res[index_mem] = func_index[index_mem](returns)[3]
            elif 'beta' in index_mem:
                index = index_mem.split('_')
                data = benchmark.get('000300.SH', pd.Series()) if '300' in index[-1] else benchmark.get('000905.SH', pd.Series())
                res[index_mem] = func_index[index_mem](data)
            elif 'alpha' in index_mem:
                index = index_mem.split('_')
                data = benchmark.get('000300.SH', pd.Series()) if '300' in index[-1] else benchmark.get('000905.SH', pd.Series())
                beta = res.get('beta_300', 0) if '300' in index else res.get('beta_500', 0)
                res[index_mem] = func_index[index_mem](beta, res['annual_return'], data)
            elif index_mem in func_index.keys():
                res[index_mem] = func_index[index_mem]()
            else:
                print('该参数是错误的！！！')
                raise ValueError

        return res

    def _setMarketQuotes(self, market_quotes):
        '''
        init index pctchange
        '''
        if not self.benchmark: return
        market_quotes = market_quotes['AIndexEODPrices']
        market_quotes['pct'] = market_quotes['S_DQ_CLOSE'] / market_quotes['S_DQ_PRECLOSE'] - 1
        market_quotes = market_quotes.reset_index()[['TRADE_DT', 'S_INFO_WINDCODE', 'pct']]
        market_quotes.set_index('S_INFO_WINDCODE', inplace=True)
        return market_quotes
