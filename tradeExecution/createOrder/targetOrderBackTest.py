#!usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file: targetOrderBackTest.py
@time: 2020/11/24
"""
import math
import warnings
import numpy as np
import pandas as pd
from functools import reduce
from collections import defaultdict
from utils.Decorator import func_timer
from configs.Database import mysql, SHARE
from configs.riskConfig import FUTURE_ENDS
from utils.AiData import which_table, eod_data, loadCommissionRate, getCommission


class targetOrderBackTest():
    """
    # 回测类,通过传递的参数,完成本次order的生成,
    # 注：目前逻辑只支持简单的多头和股票策略,不支持期货等
    """

    def __init__(self, strategyConfigs=None,
                 marketData: dict = None,
                 target_order: list = None,
                 security_list: set = None,
                 trade: list = None,
                 futureManager = None):
        """
        :param strategyConfigs:
        :param marketData:
        :param target_order:
        :param security_list:
        :param trade:
        :param margin_ratio:
        :param multiplier:
        """
        self.security_list = security_list
        self.trades = trade
        self.marketData = marketData
        self.targetOrders = target_order
        self.strategyConfigs = strategyConfigs
        self.futureManager = futureManager
        self.sysType = {strategyConfig['strategy_id']: strategyConfig['business_type'] for strategyConfig in self.strategyConfigs}
        self.margin_ratio = self.marketData.get('CFUTURESMARGINRATIO', self._init_margin())
        self.multiPlier = self.marketData.get('CFUTURESCONTPRO', self._init_multiplier())
        with mysql(SHARE) as self.cursor:
            self.fee_rate = self._loadFeeRate(security_list, self.strategyConfigs)
        self.commissionRate = loadCommissionRate([i['strategy_id'] for i in self.strategyConfigs if i['business_type']=='A6'])
        self.needDelete = defaultdict(lambda: False)

    @func_timer
    def run(self, trade_date, targetPosition:pd.DataFrame, prePosition, todayAsset, todayAccount):
        """
        :param trade_date:  当前交易日
        :param targetPosition: 今日目标仓位
        :param prePosition: 昨日持仓
        :param todayAsset: 当前总资产信息
        :param todayAccount: 当前账户信息
        :return:
        """
        self.trade_date = trade_date
        self._keepPosition(targetPosition)
        # self.marketDataDict = self.marketData.query("TRADE_DT=='{}'".format(trade_date)).reset_index().set_index(['S_INFO_WINDCODE']).to_dict()
        self.getMarketDataDict(targetPosition, prePosition)
        # 按今天设定的成交价更新当前总资产
        todayAccount,prePosition = self.reCalucatePreAsset(prePosition, todayAccount)
        todayAsset = todayAccount.groupby(by=['strategy_id', 'trade_date'], as_index=False).agg({
            'strategy_id': 'first',
            'sod_total_asset': 'sum',
        })
        # 将昨日持仓的日期改为当前日期
        prePosition = self.dealPrePosition(prePosition)
        # 在今日targetposition上按策略id拼接totalasset一列，用来计算今日目前金额
        targetPosition['account_type'] = targetPosition.copy().apply(self._fill_account_type, axis=1)
        targetPosition['account_type'] = targetPosition['account_type'].astype('str')
        targetPosition = pd.merge(targetPosition, todayAsset[['strategy_id', 'sod_total_asset']], on=['strategy_id'])
        # 计算某个标的今日目标金额
        targetPosition['target_notional'] = targetPosition['target_ratio'] * targetPosition['sod_total_asset']
        # 将昨日持仓信息和今日目标持仓信息拼接
        targetPosition['LS'] = targetPosition['LS'].astype('float')
        prePosition['LS'] = prePosition['LS'].astype('float')
        targetOrders = pd.merge(targetPosition, prePosition, on=['strategy_id', 'trade_date', 'LS', 'windcode', 'account_type'], how='outer').fillna(0)
        # 按标的拼接保证金率
        # targetOrders = pd.merge(targetOrders, self.margin_ratio, on=['windcode', 'trade_date'], how='left').fillna(1)
        targetOrders['margin_ratio'] = targetOrders.apply(self._fill_margin_ration, axis=1)
        # targetOrders['account_type'] = targetOrders.copy().apply(self._fill_account_type, axis=1)
        if targetOrders.empty:return self.getAmptyTrades()
        # 计算出每个标的今日要调整金额，正为买，负为卖
        targetOrders['result_notional'] = (targetOrders['target_notional'].values - targetOrders['amount'].values) / targetOrders['margin_ratio'].values
        # bs 正为买，负为卖
        targetOrders['BS'] = np.where(targetOrders['result_notional'] > 0, 1, -1)
        # 按标的以及对应策略配置的成交价格类型获取价格
        targetOrders['price'] = targetOrders.apply(self._fill_price, axis=1)
        # 踢出没有价格的标的（停牌)
        targetOrders.dropna(axis=0, how='any', inplace=True)
        # 去除停牌的标的
        targetOrders.drop(targetOrders[targetOrders['windcode'].isin(self.marketData['STOPINFO'][self.trade_date])].index, inplace=True)
        # 赋值 businesstype，以便获取费率
        targetOrders['business_type'] = targetOrders['strategy_id'].map(self.sysType)
        # 获取费率
        # targetOrders = pd.merge(targetOrders,self.fee_rate,on=['business_type','windcode','BS'],how='left')
        targetOrders['fee_rate'] = targetOrders.apply(self._fill_fee_rate, axis=1)
        targetOrders['commission_rate'] = targetOrders.apply(getCommission, axis=1, commission=self.commissionRate)
        targetOrders['fee_rate'] = targetOrders['fee_rate'] + targetOrders['commission_rate']
        # 计算卖的手续费，并重新计算买的totalAsset
        self.reCalucateBuyTotalAsset(targetOrders)
        # 计算初始下单量
        targetOrders['shares'] = np.where(targetOrders['BS'] == 1,
                                          np.abs(targetOrders['result_notional']).values / (targetOrders['price'].values * (1 + targetOrders['fee_rate'])),
                                          np.abs(targetOrders['result_notional']).values / targetOrders['price'].values)
        # 按标的获取最小下单量
        targetOrders['min_order_volume'] = targetOrders.apply(self._fill_multiplier, axis=1)
        # 计算按最小下单量整除之后的基础量
        targetOrders['basal'] = (targetOrders['shares'] // targetOrders['min_order_volume'])
        # 计算除了整数部分的余量，按买/卖不同处理规则。 公式(1-bs)/2,买舍去，卖向上取整
        if targetOrders.empty:
            targetOrders['increment'] = 0
        else:
            targetOrders['increment'] = np.vectorize(self._getInt)(
            targetOrders['shares'] % targetOrders['min_order_volume'] / targetOrders['min_order_volume']) * ((1-targetOrders['BS'].values) / 2)
        targetOrders['volume'] = (targetOrders['basal'].values + targetOrders['increment'].values) * targetOrders['min_order_volume']
        # 期货volume 改为手数
        targetOrders['volume'] = targetOrders.apply(self._judge_future_volume, axis=1)
        # 对于卖单，防止下单量超出持仓量。超出部分抹去
        targetOrders['volume'] = np.where((targetOrders['BS'] == -1) & (targetOrders['volume'] > targetOrders['position']), targetOrders['position'], targetOrders['volume'])
        # 判断是否保持昨日持仓
        targetOrders['need_delete'] = targetOrders['strategy_id'].map(self.needDelete)
        targetOrders.drop(targetOrders[targetOrders['need_delete'] == True].index, inplace=True)

        #order计算结束，存储
        targetOrder = targetOrders[['strategy_id', 'trade_date', 'BS', 'LS', 'windcode', 'volume', 'price']]
        self.targetOrders.extend(targetOrder.values.tolist())
        #计算trade
        # trades = targetOrders[
        #     ['strategy_id', 'trade_date', 'windcode', 'BS', 'LS', 'account_type', 'volume', 'fee_rate', 'margin_ratio']]
        trades = targetOrders.copy()
        if trades.empty:
            trades = pd.DataFrame(columns=['strategy_id', 'trade_date', 'windcode', 'BS', 'LS', 'amount', 'volume',
                                           'price', 'fee', 'notional'])
            return trades
        else:
            trades = trades.copy()
            trades['price'] = trades.apply(self._fill_trade_price, axis=1)
            trades_twap = trades[trades['price'] == 'AITWAP3']
            if not trades_twap.empty:
                from Trader.backtest.MockBacktest import mockBacktest
                trades_mock = trades[trades['price'] != 'AITWAP3']
                trades_twap = mockBacktest(trades_twap,'2',True)
                trades_twap['price'] = trades_twap['trade_price']
                trades_twap['volume'] = trades_twap['trade_volume']
                trades = pd.concat([trades_mock,trades_twap[['strategy_id', 'trade_date', 'windcode', 'BS', 'LS', 'account_type',
                                                             'volume', 'fee_rate','margin_ratio','price']]])
            # 名义本金
            trades['notional'] = np.where(trades['windcode'].str.endswith(FUTURE_ENDS),
                                          trades['volume'].values * trades['price'].values * trades['min_order_volume'],
                                          trades['volume'].values * trades['price'].values)
            # 费用
            trades['fee'] = trades['notional'].values * trades['fee_rate'].values
            # 占资
            trades['amount'] = trades['notional'].values * trades['margin_ratio'].values

            # # 判断现金是否为负
            trades = self.checkCash(trades, todayAccount)
        # 记录今日order和trade
        trades = trades[
            ['strategy_id', 'trade_date', 'windcode', 'BS', 'LS', 'amount', 'volume', 'price', 'fee', 'notional']]
        return trades

    def dealPrePosition(self, prePosition):
        """
        处理做如持仓，主要筛选要用的列，重命名持仓量字段，避免持仓量跟目标量字段冲突，将日期改为当前处理的日期
        :param prePosition:
        :return:
        """
        prePosition = prePosition[['strategy_id', 'account_type', 'trade_date', 'LS', 'windcode', 'volume', 'amount']]
        prePosition = prePosition[prePosition['volume'] !=0]
        prePosition = prePosition.rename(columns={'volume': 'position'})
        prePosition.loc[:, 'trade_date'] = self.trade_date
        return prePosition

    def checkCash(self, targetOrders, preAccount):
        """
        # # 判断现金,若为负，调整
        :param targetOrders:
        :param preAccount:
        :return:
        """
        if targetOrders.empty: return targetOrders
        targetOrders = targetOrders.copy()
        targetOrders['cash_cut'] = targetOrders['amount'].values * targetOrders['BS'].values + targetOrders[
            'fee'].values
        cash_cut = targetOrders.groupby(['strategy_id','account_type'])['cash_cut'].sum().reset_index()
        cash_cut = pd.merge(cash_cut, preAccount, on=['strategy_id', 'account_type'], how='left')
        cash_cut['diff'] = cash_cut['cash'] - cash_cut['cash_cut']
        cash_cut = cash_cut[cash_cut['diff'] < 0]
        # if not cash_cut.empty:warnings.warn('当前order将可能造成资金为负，将做调整！')
        if not cash_cut.empty:
            print('当前order将可能造成资金为负，将做调整！')
        for index, row in cash_cut.iterrows():
            cash_tmp = targetOrders[(targetOrders['strategy_id'] == row['strategy_id']) & (targetOrders['account_type'] == row['account_type'])]
            cash_tmp = self._cashPositive(row['diff'], cash_tmp)
            targetOrders.drop(targetOrders[(targetOrders['strategy_id'] == row['strategy_id']) &
                                           (targetOrders['account_type'] == row['account_type'])].index, inplace=True)
            targetOrders = targetOrders.reset_index(drop=True)
            targetOrders = targetOrders.append(cash_tmp).reset_index(drop=True)
        return targetOrders

    def saveData(self, targetOrders):
        """
        存储今日order
        :param targetOrders:
        :return:
        """
        trades = targetOrders[
            ['strategy_id', 'trade_date', 'windcode', 'BS', 'LS', 'amount', 'volume', 'price', 'fee', 'notional']]
        targetOrders = targetOrders[['strategy_id', 'trade_date', 'BS', 'LS', 'windcode', 'volume', 'price']]
        self.targetOrders.extend(targetOrders.values.tolist())
        # self.trades.extend(trades.values.tolist())
        return trades

    def getAmptyTrades(self):
        """
        如果没有成交信息，返回一个空的dataframe
        :return:
        """
        return pd.DataFrame(columns=[['strategy_id', 'trade_date', 'windcode', 'BS', 'LS', 'amount', 'volume', 'price', 'fee', 'notional']])

    def reCalucatePreAsset(self, prePosition:pd.DataFrame, preAccount:pd.DataFrame):
        """
        重新计算总资产
        :param prePositionNew:
        :param preAccount:
        :return:
        """
        preAccountNew = preAccount.copy()
        prePositionNew = prePosition.copy()
        prePositionNew['account_type'] = prePositionNew.apply(self._fill_account_type, axis=1)
        prePositionNew['account_type'] = prePositionNew['account_type'].astype('str')
        # 按标的获取最小下单量
        prePositionNew['min_order_volume'] = prePositionNew.apply(self._fill_multiplier, axis=1)
        if not prePositionNew.empty:
            prePositionNew['price'] = prePositionNew.apply(self._fill_price, axis=1)
            prePositionNew['margin_ratio'] = prePositionNew.apply(self._fill_margin_ration, axis=1)
            prePositionNew.dropna(axis=0, how='any', inplace=True)
            prePositionNew['amount'] = prePositionNew.apply(self._recal_amount, axis=1, preAccount=preAccountNew)
            positionValue = prePositionNew.groupby(['strategy_id', 'account_type'])['amount'].sum().reset_index()
            preAccountNew['sod_total_asset'] = preAccountNew.apply(self._recal_asset, positionValue=positionValue, axis=1)
        return preAccountNew, prePositionNew

    # --------------------------------------- private func -------------------------------------------------

    def _loadFeeRate(self, total_security_list, strategy_configs):
        """
        加载费率信息
        :param total_security_list:
        :param strategy_configs:
        :return:
        """
        business_types = set([config['business_type'] for config in strategy_configs])
        sql = "select business_type,windcode,fee_type,fee_rate from trading_fee_rate where business_type"
        if len(business_types) > 1:
            sql = sql + " in {0}".format(tuple(business_types))
        elif len(business_types) == 1:
            sql = sql + " = '{0}'".format(business_types.pop())
        else:
            exit("Error: No Business Type")
        # sql += " and windcode"
        # if len(total_security_list) > 1:
        #     sql = sql + " in {0}".format(tuple(total_security_list))
        # elif len(total_security_list) == 1:
        #     sql = sql + " = '{0}'".format(tuple(total_security_list)[0])
        # else:
        #     exit("Error: No security")
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        df = pd.DataFrame(data,columns=['business_type','windcode','fee_type','fee_rate'])
        df['fee_rate'] = df['fee_rate'].astype('float')
        df['BS'] = df['fee_type'].map({'B':1,'S':-1,'OPEN':1,'CLOSE':-1})
        return df

    def _getInt(self, x):
        return math.ceil(x)

    def _fill_price(self, row: pd.Series):
        """
        按策略配置里的价格类型，填充成交价
        :param row:
        :return:
        """
        pricefieldname = 'S_DQ_OPEN'
        # if row['windcode'].endswith(FUTURE_ENDS) and pricefieldname ==['S_DQ_CLOSE']:
        #     pricefieldname = 'S_DQ_SETTLE'
        return self.marketDataDict[pricefieldname].get(row['windcode'], np.NAN)

    def _fill_trade_price(self, row : pd.Series):
        pricefieldname = self.priceType[row['strategy_id']]
        if row['windcode'].endswith(FUTURE_ENDS):
        # if row['windcode'].endswith(FUTURE_ENDS) and pricefieldname == ['S_DQ_CLOSE']:
            pricefieldname = 'S_DQ_SETTLE'
        if pricefieldname == 'AITWAP3':
            return 'AITWAP3'
        else:
            return self.marketDataDict[pricefieldname].get(row['windcode'], np.NAN)


    def _fill_margin_ration(self, row: pd.Series):
        if row.empty:
            return 1
        if row['windcode'].endswith(FUTURE_ENDS):
            #'S_INFO_WINDCODE', 'TRADE_DT', 'MARGINRATIO'
            ratio = self.margin_ratio.query('S_INFO_WINDCODE=="{}"'.format(row['windcode'])).query('TRADE_DT<="{}"'.format(self.trade_date)).iloc[-1,-1]
        else:
            ratio = 1
        return ratio

    def _fill_multiplier(self,row:pd.Series):
        if row.empty:
            return 100
        if row['windcode'].endswith(FUTURE_ENDS):
            #columns = ['S_INFO_WINDCODE', 'S_INFO_PUNIT', 'S_INFO_CEMULTIPLIER', 'S_INFO_RTD']
            return int(self.multiPlier.query("S_INFO_WINDCODE=='{}'".format(row['windcode'])).S_INFO_CEMULTIPLIER.values[0])
        elif row['windcode'].startswith('688') and row['windcode'].endswith('SH'):
            return 200
        else:
            return 100

    def _fill_fee_rate(self,row:pd.Series):
        if row.empty:return 0
        windcode = row['windcode']
        if row['windcode'].endswith(FUTURE_ENDS):
            maincode = windcode[:2]+windcode[-4:]
        else:
            maincode = windcode
        fee_rate = self.fee_rate.query("windcode=='{}'".format(maincode)).query("business_type=='{}'".format(row['business_type'])).query("BS=={}".format(row['BS'])).fee_rate.values[0]
        return fee_rate

    def _recal_amount(self, row: pd.Series, preAccount: pd.DataFrame = None):
        if row.empty:return
        windcode = row['windcode']
        if row['price'] == np.nan:
            return row['amount']
        elif windcode.endswith(FUTURE_ENDS):
            new_amount = row['price'] * row['volume'] * row['margin_ratio'] * row['min_order_volume']
            cash_add = (row['notional'] - row['price'] * row['volume'] * row['min_order_volume'] + row['amount'] - new_amount)
            preAccount.loc[(preAccount.strategy_id == row['strategy_id']) & (preAccount.account_type == 'FUTURE'), ['cash']] += cash_add
            return new_amount
        else:
            return row['price'] * row['volume']


    def _cashPositive(self, cash, df):
        '''
        确保资金为正,资金不够时,按照买入金额从低到高删除订单，成交量不足100的直接删除，直至资金为正且调整后订单量大于100股
        :param pre_cash:
        :param trade_amount:
        :param df:
        :return:
        '''
        df = df.copy()
        df['trade_price_and_fee'] = df['price'] + df['price'] * df['fee_rate']
        df.sort_values(['notional'], inplace=True, ascending=False)
        df = df.reset_index(drop=True)
        for index, row in df.copy().iterrows():
            if row['BS'] != 1: continue
            if cash + row['notional'] < 0:
                cash += row['notional']
                df.drop(index=index, inplace=True)
            else:
                need_position = (0 - cash) / row['trade_price_and_fee']
                need_position = min(math.ceil(need_position / 100) * 100, row['volume'])
                cash += need_position * row['trade_price_and_fee']
                df.loc[index, 'volume'] -= need_position
                df.loc[index, 'notional'] -= need_position * row['price']
                df.loc[index, 'amount'] -= need_position * row['price'] * row['margin_ratio']
                df.loc[index, 'fee'] = df.loc[index, 'notional'] * row['fee_rate']
            if cash > 0: break
        return df

    def _recal_asset(self, row: pd.Series, positionValue: dict = None):
        """
        :param row:
        :param positionValue:
        :return:
        """
        positions = positionValue[positionValue['strategy_id'] == row['strategy_id']]
        if positions.empty : return row['cash']
        positions = positions[positions['account_type'] == row['account_type']]
        if positions.empty :return row['cash']
        amount = positions['amount'].values[0]
        return row['cash'] + amount

    def getMarketDataDict(self,targetPosition,prePosition):
        codes = set(targetPosition['windcode'].values.tolist()+prePosition['windcode'].values.tolist())
        tables = set([which_table(code) for code in codes if which_table(code)])
        pd_data = [self.marketData[table].query("TRADE_DT=='{}'".format(self.trade_date)).reset_index() for table in tables]
        if not pd_data:return {}
        result  = reduce(lambda x,y:x.append(y),pd_data)
        self.marketDataDict = result.set_index(['S_INFO_WINDCODE']).to_dict()

    def _init_margin(self):
        return pd.DataFrame(columns=['S_INFO_WINDCODE', 'TRADE_DT', 'MARGINRATIO'])

    def _init_multiplier(self):
        columns = ['S_INFO_WINDCODE', 'S_INFO_PUNIT', 'S_INFO_CEMULTIPLIER', 'S_INFO_RTD']
        return pd.DataFrame(columns=columns)


    # ------------------------------------------- classmethod ----------------------------------------------------------
    @classmethod
    def updateWindInfoTables(self, windInfo: dict, strategyConfigs, security_pool:set, keepPosition:dict):
        """
        策略配置中的成交价格字段
        """
        self.priceType = {strategyConfig['strategy_id']: strategyConfig['trade_price'] for strategyConfig in
                          strategyConfigs}
        self.keepPosition = keepPosition
        for windcode in security_pool:
            windInfo[which_table(windcode)]['codes'].add(windcode)
        for table,values in windInfo.items():
            if table in eod_data:
                windInfo[table]['fields'].update(list(self.priceType.values())+['S_DQ_OPEN', 'TRADE_DT', 'S_INFO_WINDCODE'])

    def reCalucateBuyTotalAsset(self, targetOrders):
        """
        根据卖单总金额，计算出的卖产生的手续费，重新计算买单可买金额。
        """
        # 预估手续费
        targetOrders['fee'] = targetOrders['result_notional'] * targetOrders['BS'] * targetOrders['fee_rate']
        # 计算卖单手续费
        sellFeeSum = targetOrders[(targetOrders['BS'] == -1) & (targetOrders['account_type'] == 'CASH')].groupby(by='strategy_id').agg({'fee': 'sum'}).to_dict()
        # 重新计算买单可用总资产
        # targetOrders['sod_total_asset'] = np.where(targetOrders['BS'] == 1, targetOrders['sod_total_asset'] - sellFeeSum, targetOrders['sod_total_asset'])
        targetOrders['sod_total_asset'] = targetOrders.apply(self._cutSellFee, axis=1, feeDict=sellFeeSum)
        # 重新计算买单目标金额
        targetOrders['target_notional'] = targetOrders['target_ratio'] * targetOrders['sod_total_asset']
        # 重新买单需变化金额
        targetOrders['result_notional'] = (targetOrders['target_notional'].values - targetOrders['amount'].values) / \
                                          targetOrders['margin_ratio'].values

    def _cutSellFee(self, row: pd.Series, feeDict=None):
        if row['BS'] == 1 and row['account_type'] == 'CASH':
            return row['sod_total_asset'] - feeDict['fee'].get(row['strategy_id'], 0)
        else:
            return row['sod_total_asset']

    def _fill_account_type(self, row: pd.Series):
        if row.empty:
            return 'CASH'
        if row['windcode'].endswith(FUTURE_ENDS):
            return 'FUTURE'
        else:
            return 'CASH'





    def _keepPosition(self, targetPosition):
        strategy_ids = [config['strategy_id'] for config in self.strategyConfigs]
        for strategy_id in strategy_ids:
            if targetPosition[targetPosition['strategy_id'] == strategy_id].empty and self.keepPosition[strategy_id]:
                self.needDelete[strategy_id] = True
            else:
                self.needDelete[strategy_id] = False


    def _judge_future_volume(self, row: pd.DataFrame):
        """
        期货数量改为张数
        """
        if row['windcode'].endswith(FUTURE_ENDS):
            volume = row['volume'] // row['min_order_volume']
        else:
            volume = row['volume']
        return volume



