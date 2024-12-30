# -*- coding:utf-8 -*-

"""
@author: NanXu
@file: ClearSettle.py
@time: 2020-11-16
模拟实盘环境清算
"""
import math
from collections import defaultdict
from clearSettle.ClearSettle import ClearSettle
from configs.Database import oracle
from utils.AiData import which_table, loadFeeRate, getWindData, fill_account_type, getCommission
from configs.tableConfig import *


class ClearSettleMock(ClearSettle):

    def __init__(self, strategy_configs, am_configs, env='dev', trade_date='', level='DEBUG'):
        super().__init__(strategy_configs, env, level=level)
        self.initInfo(trade_date, am_configs)
        self.setEXInfo(self.trade_date)

    def runClearSettle(self):
        """
        主程序入口：计算逻辑，昨日总资产 + 今日盈利 = 今日总资产，今日现金 = 今日总资产 - 今日持仓
        :param trade_date:
        :return: dict(df)
        """
        self.logger.debug('交易日:{}, 计算trade,合并昨日持仓和今日交易'.format(self.trade_date))
        trade_info = self._trade(self.targetOrders, self.account)
        position_trade, trade = self.coreCale(self.pre_position, trade_info)
        self.logger.debug('交易日:{}, 计算position'.format(self.trade_date))
        position = self._position(position_trade)
        self.logger.debug("交易日:{}, 计算account".format(self.trade_date))
        df_account, account = self._account(position_trade, self.account)
        self.logger.debug('交易日:{}, 计算asset'.format(self.trade_date))
        asset = self._asset(df_account, self.asset, trade)
        self.logger.debug('交易日:{}, asset,account调整资管费用'.format(self.trade_date))
        res = {'asset': asset, 'position': position, 'trade': trade, 'account': account}
        self.logger.debug('交易日:{}, 计算am_fee'.format(self.trade_date))
        am_fee = self.amf.getAmFee()
        if not am_fee.empty:
            res.update({'am_fee': am_fee})
        return res

    def getProdData(self, trade_date):
        '''
        获取模拟策略生产数据
        '''
       # 读取昨日position
        self.cursor.execute("select strategy_id, windcode, LS, volume,avg_cost from `position` where trade_date = '{}' and volume <>0 and strategy_id in ({})".format(self.pre_day, self.id_mysql))
        self.pre_position = pd.DataFrame(list(self.cursor.fetchall()), columns=['strategy_id', 'windcode', 'LS', 'position', 'avg_cost'])
        # 读取今日account
        self.cursor.execute("select * from account where trade_date = '{}' and strategy_id in ({})".format(self.trade_date, self.id_mysql))
        self.account = pd.DataFrame(list(self.cursor.fetchall()), columns=account['columns'])
        # 读取今日asset
        self.cursor.execute("select * from asset where trade_date = '{}' and strategy_id in ({})".format(self.trade_date, self.id_mysql))
        self.asset = pd.DataFrame(list(self.cursor.fetchall()), columns=asset['columns'])
        # traget_order
        self.cursor.execute("select * from target_order where trade_date='{}' and strategy_id in ({})".format(self.trade_date, self.id_mysql))
        self.targetOrders = pd.DataFrame(list(self.cursor.fetchall()),columns=target_order['columns'])

    def getMarketDataDict(self):
        '''
        标的行情数据
        '''
        windInfoDict = defaultdict(list)
        codes = set(self.pre_position['windcode'].values.tolist() + self.targetOrders['windcode'].values.tolist())
        for code in codes:
            windInfoDict[which_table(code)].append(code)
        pd_data = pd.DataFrame(columns=['S_INFO_WINDCODE'])
        for table, info in windInfoDict.items():
            tmp = ['S_DQ_OPEN','AVERAGE']
            tmp.extend(['S_DQ_PRESETTLE','S_DQ_SETTLE']) if table =='CIndexFuturesEODPrices' else tmp.extend(['S_DQ_PRECLOSE','S_DQ_CLOSE'])
            tmp = getWindData(table=table, code_list=info, start_date=self.trade_date, end_date=self.trade_date, fields=tmp, multi=self.multi)
            pd_data = pd_data.append(tmp)
        return pd_data.set_index(['S_INFO_WINDCODE']).to_dict()

    def setEXInfo(self, trade_date):
        '''
        初始化配股信息，不考虑分红
        '''
        trade_date = trade_date.replace('-', '')
        with oracle() as cursor:
            cursor.execute("select EX_DATE, s_info_windcode, BONUS_SHARE_RATIO+CONVERSED_RATIO from wind.AshareEXRightDividendRecord where EX_DATE = '{}'".format(trade_date))
            A_stock = list(cursor.fetchall())
            cursor.execute("select BONUS_SHARE_D_DATE,S_INFO_WINDCODE, BONUS_SHARE_RATIO from wind.HKSHAREEVENT where BONUS_SHARE_D_DATE = '{}'".format(trade_date))
            HK = list(cursor.fetchall())
        result = pd.DataFrame(list(A_stock) + list(HK), columns=['date', 'windcode', 'stock_bonus'])
        self.EXInfo = result.set_index('date')

    # -----------------私有函数-----------------------

    def _trade(self, targetOrders, todayAccount):
        self.priceType = {strategyConfig['strategy_id']: strategyConfig['trade_price'] for strategyConfig in
                          self.strategy_configs}
        # 按标的以及对应策略配置的成交价格类型获取价格
        targetOrders['price'] = targetOrders.apply(self._fill_price, axis=1, priceType=self.priceType)
        # 考虑期货乘数
        targetOrders['multi'] = targetOrders.apply(self._fill_multi, axis=1)
        targetOrders['notional'] = targetOrders['volume'].values * targetOrders['price'].values * targetOrders['multi'].values
        self.fee_rate = loadFeeRate(targetOrders['windcode'].values.tolist(), self.strategy_configs)
        targetOrders['business_type'] = targetOrders['strategy_id'].map(self.sys_id)
        targetOrders['fee_rate'] = targetOrders.apply(self._fill_fee_rate, axis=1)
        targetOrders['commission_rate'] = targetOrders.apply(getCommission, axis=1, commission=self.commissionRate)
        targetOrders['fee_rate'] = targetOrders['fee_rate'] + targetOrders['commission_rate']
        targetOrders['fee'] = targetOrders['notional'].values * targetOrders['fee_rate'].values
        targetOrders['margin_rate'] = targetOrders.apply(self.getFutureMarginRate, axis=1)
        targetOrders['amount'] = targetOrders['notional'].values * targetOrders['margin_rate'].values
        # # 判断现金是否为负
        targetOrders = self._checkCash(targetOrders, todayAccount)
        return targetOrders[targetOrders['volume'] != 0]

    def _checkCash(self, targetOrders, preAccount):
        """
        # # 判断现金,若为负，调整
        :param targetOrders:
        :param preAsset:
        :return:
        """
        if targetOrders.empty: return targetOrders
        targetOrders['account_type'] = targetOrders.copy().apply(fill_account_type, axis=1)
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

    def _cashPositive(self, cash, df):
        '''
        确保资金为正,资金不够时,按照买入金额从低到高删除订单，成交量不足100的直接删除，直至资金为正且调整后订单量大于100股
        :param pre_cash:
        :param trade_amount:
        :param df:
        :return:
        '''
        df = df.copy()
        df['trade_price_and_fee'] = round(df['price'] + df['price'] * df['fee_rate'], 3)
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
                df.loc[index, 'amount'] -= need_position * row['price'] * row['margin_rate']
                df.loc[index, 'fee'] = df.loc[index, 'notional'] * row['fee_rate']
            if cash > 0:
                break
        return df

