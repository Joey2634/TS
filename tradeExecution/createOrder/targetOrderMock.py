# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/12/23 下午3:51
# @Author : lxf
# @File : targetOrderLive.py
# @Project : ai-investment-manager

import logging
import numpy as np
import pandas as pd
import redis

from configs.Redis import liveMarketRedisConfig
from configs.riskConfig import FUTURE_ENDS
from tradeExecution.createOrder.targetOrderBackTest import targetOrderBackTest


class targetOrderMock(targetOrderBackTest):
    """
    模拟环境，生成调仓指令
    """

    def __init__(self, env='dev',
                 mode='mock',
                 trade_date='',
                 pre_date='',
                 assetInfo: pd.DataFrame = None,
                 strategyConfigs: list = None,
                 windData: dict = None,
                 security_list: set = None,
                 futureManager=None
                 ):

        """
        根据env和mode 决定 总资产信息，昨日持仓和最新价的获取方式
                mode=='mock':数据库获取
                mode=='prod':交易系统获取
        """
        super().__init__(strategyConfigs=strategyConfigs,
                         marketData=windData,
                         security_list=security_list,
                         futureManager=futureManager)
        self.env = env
        self.mode = mode
        self.trade_date = trade_date
        self.pre_date = pre_date
        self.assetInfo = assetInfo
        self.liveMarketData = windData['liveMarketInfo']
        self.logger = logging.getLogger('targetOrder')

    def run(self, targetPosition, T0targetPostion: pd.DataFrame = None, todayAsset=None):
        targetOrdersNormal = self.normalOrder(targetPosition, todayAsset)
        targetOrdersT0 = self.T0Order(T0targetPostion, todayAsset)
        return targetOrdersNormal, targetOrdersT0

    def normalOrder(self, targetPosition, todayAsset):
        prePosition = self.dealPrePosition(self.prePosition)
        self.logger.info('prePosition:\n{}'.format(prePosition.to_string()))
        self.logger.info("todayAsset:\n{}".format(todayAsset.to_string()))
        # 在今日targetposition上按策略id拼接totalasset一列，用来计算今日目前金额
        targetPosition = targetPosition.copy()
        targetPosition = pd.merge(targetPosition, todayAsset[['strategy_id', 'sod_total_asset']], on=['strategy_id'])
        # 计算某个标的今日目标金额
        targetPosition['target_notional'] = targetPosition['target_ratio'] * targetPosition['sod_total_asset']
        # 将昨日持仓信息和今日目标持仓信息拼接
        targetOrders = pd.merge(targetPosition, prePosition, on=['strategy_id', 'trade_date', 'LS', 'windcode'], how='outer').fillna(0)
        targetOrders['margin_ratio'] = targetOrders.apply(self._fill_margin_ration, axis=1)
        if targetOrders.empty: return self.getAmptyTrades()
        # 计算出每个标的今日要调整金额，正为买，负为卖
        targetOrders['result_notional'] = (targetOrders['target_notional'].values - targetOrders['amount'].values) / \
                                          targetOrders['margin_ratio'].values
        # self.logger.info("result_notional:{}".format(targetOrders[['strategy_id','windcode','result_notional']].to_dict()))
        # bs 正为买，负为卖
        targetOrders['BS'] = np.where(targetOrders['result_notional'] > 0, 1, -1)
        # 按标的以及对应策略配置的成交价格类型获取价格
        targetOrders['price'] = targetOrders.apply(self._fill_price, axis=1)
        # 踢出没有价格的标的（停牌)
        targetOrders.dropna(axis=0, how='any', inplace=True)
        # 去掉价格为0的标的
        self.logger.info('targetOrders price =0:\n{}'.format(targetOrders[targetOrders['price'] == 0].to_string()))
        targetOrders = targetOrders[targetOrders['price'] != 0]
        # 赋值 businesstype，以便获取费率
        targetOrders['business_type'] = targetOrders['strategy_id'].map(self.sysType)
        # 获取费率
        # targetOrders = pd.merge(targetOrders, self.fee_rate, on=['business_type', 'windcode', 'BS'], how='left')
        targetOrders['fee_rate'] = targetOrders.apply(self._fill_fee_rate, axis=1)
        # 计算卖的手续费，并重新计算买的totalAsset
        # 计算初始下单量
        targetOrders['shares'] = np.where(targetOrders['BS'] == 1,
                                          np.abs(targetOrders['result_notional']).values / (
                                                  targetOrders['price'].values * (1 + targetOrders['fee_rate'])),
                                          np.abs(targetOrders['result_notional']).values / targetOrders['price'].values)
        # 按标的获取最小下单量
        targetOrders['min_order_volume'] = targetOrders.apply(self._fill_multiplier, axis=1)
        # 计算按最小下单量整除之后的基础量
        targetOrders['basal'] = (targetOrders['shares'] // targetOrders['min_order_volume'])
        # 计算除了整数部分的余量，按买/卖不同处理规则。 公式(1-bs)/2,买舍去，卖向上取整
        targetOrders['increment'] = np.vectorize(self._getInt)(
            targetOrders['shares'] % targetOrders['min_order_volume'] / targetOrders['min_order_volume']) * (
                                            (1 - targetOrders['BS'].values) / 2)
        targetOrders['volume'] = (targetOrders['basal'].values + targetOrders['increment'].values) * targetOrders[
            'min_order_volume']
        # 期货volume 改为手数
        targetOrders['volume'] = targetOrders.apply(self._judge_future_volume, axis=1)
        # 对于卖单，防止下单量超出持仓量。超出部分抹去
        targetOrders['volume'] = np.where(
            (targetOrders['BS'] == -1) & (targetOrders['volume'] > targetOrders['position']), targetOrders['position'],
            targetOrders['volume'])

        self.logger.info('targetOrders:\n{}'.format(targetOrders.to_string()))
        targetOrders = targetOrders[['strategy_id', 'trade_date', 'BS', 'LS', 'windcode', 'volume', 'price']]
        return targetOrders

    def T0Order(self, T0targetPosition, todayAsset):
        self.logger.info("T0TargetPosition:\n{}".format(T0targetPosition.to_string()))
        if T0targetPosition.empty: return self._initTargetOrder()
        AssetInfo = self._getAssetInfo()
        self.logger.info("asstInfo:\n{}".format(AssetInfo.to_string()))
        # 在今日targetposition上按策略id拼接totalasset一列，用来计算今日目前金额
        targetPosition = pd.merge(T0targetPosition, todayAsset[['strategy_id', 'sod_total_asset']], on=['strategy_id'])
        # 计算某个标的今日目标金额
        targetPosition['result_notional'] = targetPosition['target_ratio'] * targetPosition['sod_total_asset']
        # bs 正为买，负为卖
        targetPosition['BS'] = np.where(targetPosition['result_notional'] > 0, 1, -1)
        # 按标的以及对应策略配置的成交价格类型获取价格
        targetPosition['price'] = targetPosition.apply(self._fill_price, axis=1, priceType='closePrice')
        # 剔除没有价格的标的（停牌)
        targetPosition.dropna(axis=0, how='any', inplace=True)
        # 去掉价格为0的标的
        targetOrders = targetPosition[targetPosition['price'] != 0]
        # 计算初始下单量
        targetOrders['shares'] = np.abs(targetOrders['result_notional']).values / targetOrders['price'].values
        # 按标的获取最小下单量
        targetOrders['min_order_volume'] = targetOrders.apply(self._fill_multiplier, axis=1)
        # 计算按最小下单量整除之后的基础量
        targetOrders['basal'] = (targetOrders['shares'] // targetOrders['min_order_volume'])
        targetOrders['volume'] = targetOrders['basal'].values * targetOrders['min_order_volume']
        targetOrders = targetOrders[['strategy_id', 'trade_date', 'BS', 'LS', 'windcode', 'volume', 'price']]
        return targetOrders

    def dealPrePosition(self, prePosition):
        """
        处理做如持仓，主要筛选要用的列，重命名持仓量字段，避免持仓量跟目标量字段冲突，将日期改为当前处理的日期
        如果是prod模式，从交易接口拿当前持仓
        :param prePosition:
        :return:
        """
        prePosition = prePosition[['strategy_id', 'trade_date', 'LS', 'windcode', 'volume', 'amount']].copy()
        prePosition = prePosition.rename(columns={'volume': 'position'})
        prePosition.loc[:, 'trade_date'] = self.trade_date
        return prePosition

    @classmethod
    def updateWindInfoTables(self, windInfo: dict, strategyConfigs, position: pd.DataFrame, securities: set):
        """
        策略配置中的成交价格字段
        """
        self.prePosition = position
        self.strategyConfigs = strategyConfigs
        securities.update(position.windcode.values.tolist())

    def _fill_price(self, row: pd.Series, priceType=''):
        """
        获取最新价
        """
        windcode = row['windcode']
        if windcode.endswith(FUTURE_ENDS):
            redis_cli = redis.StrictRedis(**liveMarketRedisConfig)
            marketinfo = redis_cli.lrange(windcode, 0, 0)
            if not marketinfo:
                price = 0
            else:
                price = eval(marketinfo[0])['lastPrice'] / 10000
        else:
            row = self.liveMarketData.query('windcode=="{}"'.format(windcode))['lastPrice'].values.tolist()
            if row:
                price = row[0]
            else:
                price = 0
        return float(price)

    def _getAssetInfo(self):

        return self.assetInfo[self.assetInfo['trade_date'].str.replace("-", "") == self.pre_date]


    def _initTargetOrder(self):
        columns = ['strategy_id', 'trade_date', 'BS', 'LS', 'windcode', 'volume', 'price']
        return pd.DataFrame(columns=columns)
