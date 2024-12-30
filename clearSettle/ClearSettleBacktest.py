# -*- coding:utf-8 -*-

"""
@author: NanXu
@file: ClearSettleBacktest.py
@time: 2020-12-22
回测环境清算
"""
from functools import reduce
from clearSettle.assetManagement.AssetManagementFeeBacktest import AssetManagementFeeBacktest
from utils.AiData import which_table, getTradeSectionDates
from utils.Decorator import func_timer
from configs.tableConfig import *
from clearSettle.ClearSettle import ClearSettle


class ClearSettleBacktest(ClearSettle):
    info = {'CFuturesmarginratio': ['S_INFO_WINDCODE', 'TRADE_DT', 'MARGINRATIO'],  # 期货
            'AShareEODPrices': ['S_DQ_PRECLOSE', 'S_DQ_CLOSE'],
            'ChinaClosedFundEODPrice': ['S_DQ_PRECLOSE', 'S_DQ_CLOSE'],
            'HKshareEODPrices': ['S_DQ_PRECLOSE', 'S_DQ_CLOSE'],
            'CCommodityFuturesEODPrices': ['S_DQ_PRESETTLE', 'S_DQ_SETTLE'],
            'ChinaOptionEODPrices': ['S_DQ_PRESETTLE', 'S_DQ_SETTLE'],
            'CBondFuturesEODPrices': ['S_DQ_PRESETTLE', 'S_DQ_SETTLE'],
            'CIndexFuturesEODPrices': ['S_DQ_PRESETTLE', 'S_DQ_SETTLE']}
    dividend = {
        'AShareEXRightDividendRecord': ['EX_DATE', 'S_INFO_WINDCODE', 'BONUS_SHARE_RATIO','CONVERSED_RATIO'],
        'HKshareEvent': ['S_INFO_WINDCODE', 'EX_DATE', 'BONUS_SHARE_RATIO'],
        'CMFundSplit':['F_INFO_SPLITANNOECDATE', 'S_INFO_WINDCODE', 'F_INFO_SPLITINC']}

    def __init__(self, strategy_configs, market_quotes, asset, account, position, trade, start_date, am_configs, am_fee, env='dev', level='INFO'):
        super().__init__(strategy_configs, env, level=level)
        self.asset = asset
        self.trade = trade
        self.position = position
        self.account = account
        self.market_quotes = market_quotes
        self.setEXInfo(start_date)
        self.getMarginRate()
        self.amf = AssetManagementFeeBacktest(env, am_configs, am_fee, self.asset)

    @func_timer
    def runClearSettle(self, trade_date, trade_df, pre_position, pre_account, pre_asset):
        """
        主程序入口：计算逻辑，昨日总资产 + 今日盈利 = 今日总资产，今日现金 = 今日总资产 - 今日持仓
        :param trade_date:
        :return:
        """
        self.trade_date = self.setTradeDate(trade_date)
        self.logger.debug('交易日:{}, 合并昨日持仓和今日交易'.format(self.trade_date))
        pre_position, trade_df = self.dealData(pre_position, trade_df)
        position_trade, trade_info = self.coreCale(pre_position, trade_df)
        self.trade.extend(trade_info.values.tolist())
        self.logger.debug('交易日:{}, 计算position'.format(trade_date))
        posiiton = self._position(position_trade)
        self.position.extend(posiiton.values.tolist())
        self.logger.debug("交易日:{}, 计算account".format(trade_date))
        df_account, account = self._account(position_trade, pre_account)
        self.account.extend(account.values.tolist())
        self.logger.debug('交易日:{}, 计算asset'.format(trade_date))
        asset = self._asset(df_account, pre_asset, trade_info)
        self.asset.extend(asset.values.tolist())

        account_tomorrow,  asset_tomorrow = self.amf._adjFee(account, asset)
        return posiiton, account, asset, self.amf.need_cash, account_tomorrow, asset_tomorrow


    def dealData(self, pre_position, trade_df):
        '''
        处理昨日持仓和今日交易，加载当日行情数据
        :param pre_position:
        :param trade:
        :return:
        '''
        #!!!!!!!!!处理港股停牌A股不停牌的行情问题，回测默认不插行情
        pre_position = pre_position[pre_position['volume'] > 0][['strategy_id', 'windcode', 'LS', 'volume','avg_cost','notional']]
        pre_position = pre_position.rename(columns={'volume': 'position','notional':'notional_pre'})
        trade_df = pd.DataFrame(columns=trade['columns']) if trade_df.empty else trade_df[trade_df['volume'] != 0].copy()
        stock_list = set(pre_position['windcode'].values.tolist() + trade_df['windcode'].values.tolist())
        self.marketDataDict = self.getMarketDataDict(stock_list)
        return pre_position, trade_df

    def getMarginRate(self):
        '''
        期货合约保证金\合约乘数
        :return:
        '''
        self.margin_ratio = self.market_quotes.get('CFUTURESMARGINRATIO',pd.DataFrame())
        self.getMulti()

    def getBenchmarkPrice(self, config):
        '''
        相对计较基准行情
        :return:
        '''
        self.benchmarkPrice = self.market_quotes

    def getMarketDataDict(self, codes):
        '''
        加载标的行情信息
        :param codes:
        :return:
        '''
        if not codes:
            return {}
        tables = set([which_table(code) for code in codes])
        yesterday = getTradeSectionDates(self.trade_date,-2)[0]
        pd_data = [self.market_quotes[table].query("TRADE_DT>'{}' and TRADE_DT<='{}'".format(yesterday,
                    self.trade_date)).reset_index() for table in tables]
        result = reduce(lambda x, y: x.append(y), pd_data)
        # 港股重新计算PRECLOSE,这里判断多于一天最后一天的PRECLOSE=CLOSE-累加（CLOSE-PRECLOSE）
        columns_dict = {key:'last' for key in result.columns}
        columns_dict.update({'diff':'sum'})
        columns_dict.pop('S_INFO_WINDCODE')
        result['diff'] = result['S_DQ_CLOSE'] - result['S_DQ_PRECLOSE']
        result = result.groupby('S_INFO_WINDCODE').agg(columns_dict)
        result['S_DQ_PRECLOSE'] = result['S_DQ_CLOSE'] - result['diff']
        return result.to_dict()

    def setEXInfo(self, start_day):
        '''
        初始化送转股信息，A股和港股
        :param start_day:
        :return:
        '''
        result = pd.DataFrame(columns=['date', 'windcode', 'stock_bonus'])
        A_stock = self.market_quotes['AShareEXRightDividendRecord'].copy()
        A_stock = A_stock[A_stock['EX_DATE'] >= start_day]
        A_stock['stock_bonus'] = A_stock['BONUS_SHARE_RATIO'] + A_stock['CONVERSED_RATIO']
        A_stock = A_stock.rename(
            columns={'EX_DATE': 'date', 'S_INFO_WINDCODE': 'windcode'})
        result = result.append(A_stock[['date', 'windcode', 'stock_bonus']])
        ETF = self.market_quotes['CMFundSplit'].copy()
        ETF = ETF[ETF['F_INFO_SPLITANNOECDATE'] >= start_day]
        ETF = ETF.rename(
            columns={'F_INFO_SPLITANNOECDATE': 'date', 'S_INFO_WINDCODE': 'windcode', 'F_INFO_SPLITINC':'stock_bonus'})
        ETF['stock_bonus'] = ETF['stock_bonus'] - 1  # ETF拆分算法区别配股
        result = result.append(ETF[['date', 'windcode', 'stock_bonus']])
        HK = self.market_quotes['HKshareEvent']
        stock = HK[HK['EX_DATE'] >= start_day]
        stock = stock.rename(
            columns={'EX_DATE': 'date', 'S_INFO_WINDCODE': 'windcode', 'BONUS_SHARE_RATIO': 'stock_bonus'})
        result = result.append(stock[['date', 'windcode', 'stock_bonus']])
        result.fillna(0, inplace=True)
        result = result[result['stock_bonus'] != 0]
        self.EXInfo = result.set_index('date')

    @classmethod
    def updateWindInfoTables(cls, windInfoDict, performance_configs):
        '''
        加载清算需要load的信息
        :param result: 前面步骤汇总的信息
        :param performance_configs: 绩效参数
        :return:
        '''
        ## 或有load
        for table in windInfoDict.keys():
            if table in cls.info:
                windInfoDict[table]['fields'].update(cls.info[table])
        ## 必须load
        # 清算分红信息
        for table, field in cls.dividend.items():
            windInfoDict[table]['fields'].update(field)
        # performance比较基准
        performance_codes = []
        for per_conf in performance_configs.values():
            performance_codes.extend(per_conf.get('relative_benchmark').split(","))
            performance_codes.extend(per_conf.get('capm_benchmark').split(","))
        for stock in set(performance_codes):
            table = which_table(stock)
            windInfoDict[table]['codes'].add(stock)
            windInfoDict[table]['fields'].update(['S_INFO_WINDCODE', 'TRADE_DT', 'S_DQ_PRECLOSE', 'S_DQ_CLOSE'])