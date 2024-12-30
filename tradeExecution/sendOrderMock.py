# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/12/23 下午3:07
# @Author : lxf
# @File : sendOrderMock.py
# @Project : ai-investment-manager

import redis
import arrow
import warnings
import logging
import traceback
import pandas as pd
import numpy as np
from utils import eod_data,daily_data
from configs.Redis import liveMarketRedisConfig
from configs.Database import mysql,SHARE
from configs.tableConfig import account as accountTable
from collections import defaultdict
from utils.AiData import getWindData, getFuturesContractMultiplierDB, getMarginRate
from allocation.Allocation import Allocation
from risk.riskManagerLive import riskManagerLive
from utils.Date import getTradeSectionDates
from tradeExecution.createOrder.targetOrderMock import targetOrderMock


class sendOrderMock():

    def __init__(self, env='dev', mode='mock', strategy_ids = None):
        """
        生产或模拟环境，过风控，生成order，发单
        mode:   'mock' 模拟程序不发单或发单到模拟撮合系统,
                'test' trading system  发单到测试环境
                'prod' trading system  发单到生产环境
        """
        self.env = env
        self.mode = mode
        self.trade_date = arrow.now().date().__format__('%Y%m%d') # 当前交易日日期
        self.pre_date = getTradeSectionDates(self.trade_date,
                                             -2)[0]             # 前一个交易日日期
        self.strategy_ids = self._getStrategyIds(strategy_ids)
        self.logger = logging.getLogger('sendOrderMock')
        self._loadConfigs()                                     # 加载各种所需配置
        self._loadTodaySecurityPool()                           # 加载今日标的池
        self.prePosition = self._loadPrePosition()              # 昨日结算持仓明细
        self._setWindInfo()                                     # 加载所需历史数据
        self.assetInfos = self._loadAssetInfo()                 # 加载策略资产信息
        self.accountInfos = self._loadAccountInfo()             # 加载账户资产信息
        self.allcationLive = Allocation(strategy_configs=self.strategy_configs,
                                        allocation_configs=self.allocation_configs,
                                        trade_dates=[self.trade_date],
                                        security_pool=self.security_pool,
                                        market_quotes=self.windInfo,
                                        env=self.env, mode='live')
        self.riskManagerLive = riskManagerLive(env=env,
                                               mode = mode,
                                               assetInfos=self.assetInfos,
                                               marketData=self.windInfo,
                                               trade_date=self.trade_date,
                                               pre_date=self.pre_date,
                                               strategy_configs=self.strategy_configs,
                                               risk_configs=self.risk_configs)

        self.targetOrderLive = targetOrderMock(env=self.env,
                                               mode=self.mode,
                                               trade_date=self.trade_date,
                                               pre_date=self.pre_date,
                                               assetInfo=self.assetInfos,
                                               strategyConfigs=self.strategy_configs,
                                               windData=self.windInfo,
                                               security_list=self.security_list,
                                               futureManager=self.futureManager)

    def run(self):
        """

        """
        self.target_position = self.allcationLive.run()
        self.logger.info('targetPosition:\n{}'.format(self.target_position.to_string()))
        preAsset = self.assetInfos[self.assetInfos['trade_date'].str.replace('-', "") == self.pre_date]
        todayAsset = self.assetInfos[self.assetInfos['trade_date'].str.replace('-', "") == self.trade_date]
        self.adjusted_target_position = self.riskManagerLive.run(todayTargetPosition=self.target_position,
                                                                 prePosition=self.prePosition,
                                                                 preAsset=preAsset,
                                                                 todayAsset=todayAsset,
                                                                 todayAccount=self.accountInfos)
        self.logger.info('adjustTargetPosition:\n{}'.format(self.adjusted_target_position.to_string()))
        self.target_order, T0_target_order= self.targetOrderLive.run(targetPosition=self.adjusted_target_position,
                                                                     T0targetPostion=self.riskManagerLive.T0TargetPosition,
                                                                     todayAsset=todayAsset)
        self.logger.info('targetOrders:\n{}'.format(self.target_order.to_string()))
        self.logger.info('T0targetOrders:\n{}'.format(T0_target_order.to_string))
        self.saveData()

    def saveData(self):
        """
        将结果存入数据库
        """
        tables = ['target_position', 'adjusted_target_position', 'target_order']
        with mysql(self.env,commit=True) as cursor:
            for table in tables:
                data = eval("self.{}".format(table))
                values_s = ''.join('%s,'*data.shape[1]).strip(",")
                sql = "insert into {} values ({})".format(table,values_s)
                try:
                    cursor.executemany(sql,data.values.tolist())
                except:
                    print('insert table :{} data error:{}'.format(table,traceback.format_exc()))
        self.futureManager.save_cash_info(self.strategy_ids)



    def _getStrategyIds(self,strategy_ids=None):
        """
        根据 env和 mode 从数据库获取需处理策略id
        """
        if strategy_ids:return strategy_ids

        with mysql(self.env) as cursor:
            sql = "select distinct strategy_id from strategy_config where mode = %s"
            cursor.execute(sql,self.mode)
            data = cursor.fetchall()
            return [row[0] for row in data]

    # ---------------------------------------- private func ------------------------------------------------------------
    def _getStrategyConfig(self):
        """
        读取策略参数
        """
        sql = "select strategy_id,business_type,selection_id,allocation_id,trade_price,risk_id,amount,performance_id from strategy_config where strategy_id "
        if len(self.strategy_ids) > 1:
            strategy_ids = tuple(self.strategy_ids)
            sql = sql + "in {0}".format(tuple(strategy_ids))
        elif len(self.strategy_ids) == 1:
            sql = sql + "= '{0}'".format(self.strategy_ids[0])
        else:
            exit("No strategy_id")
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def _getConfig(self, table, key):
        result = {}
        ids = set(config[key] for config in self.strategy_configs)
        if 'NONE' in ids:
            ids.remove('NONE')
        sql = "SELECT * FROM " + table + " where " + key
        if len(ids) > 1:
            sql = sql + " in {0}".format(tuple(ids))
        elif len(ids) == 1:
            sql = sql + " = '{0}'".format(ids.pop())
        else:
            return
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        for res in data:
            if res[0] not in result:
                result[res[0]] = {}
            result[res[0]][res[1]] = res[2]
        return result

    def _setWindInfo(self):
        """
        遍历每个系统，获取需要加载的历史行情
        :return: {'tablename1':{'codes':set(),'fields':set()},
                    'tablename2':{'codes':set(),'fields':set()},...
                    }
        """
        windInfoDict = defaultdict(lambda: defaultdict(set))
        Allocation.updateWindInfoTables(windInfoDict, security_pool=self.security_list,
                                            allocation_configs=self.allocation_configs, mode='live')
        riskManagerLive.updateWindInfoTables(windInfoDict, strategy_configs=self.strategy_configs,
                                             risk_configs=self.risk_configs, security_list=self.security_list)
        targetOrderMock.updateWindInfoTables(windInfoDict, strategyConfigs=self.strategy_configs,
                                             position = self.prePosition, securities=self.security_list)
        self.windInfo = {}
        sample_size = max(
            set(int(self.allocation_configs[config]['sample_size']) for config in self.allocation_configs)) + 1
        sample_size = max(sample_size,riskManagerLive.maxPreDays)
        market_quotes_start_date = getTradeSectionDates(self.trade_date, -int(sample_size))[0]
        # 如果需要，加载期货行情
        self.futureManager = riskManagerLive.loadFutureInfo(self.windInfo, market_quotes_start_date, self.trade_date,
                                                            windInfoDict, self.env, self.mode)
        for table, info in windInfoDict.items():
            self.windInfo[table] = getWindData(
                table=table, code_list=info['codes'], start_date=market_quotes_start_date,
                end_date=self.trade_date, fields=info['fields'])
            if table in daily_data:
                self.windInfo[table].set_index(['TRADE_DT', 'S_INFO_WINDCODE'], inplace=True)
            elif table == 'CFuturesContPro':
                self.windInfo['multiplier'] = getFuturesContractMultiplierDB(self.windInfo, market_quotes_start_date,self.trade_date)
            elif table == 'CFuturesmarginratio':
                self.windInfo['margin_ratio'] = getMarginRate(self.windInfo, market_quotes_start_date, self.trade_date)
        self.windInfo['liveMarketInfo'] = self._setLiveMarketInfo() # 根据标的池获取实时行情最新价


    def _setLiveMarketInfo(self):
        """
        根据标的池获取实时行情
        """
        redis_cli = redis.StrictRedis(**liveMarketRedisConfig)
        datas = []
        for windcode in self.security_list:
            marketinfo = redis_cli.lrange(windcode, 0, 0)
            if not marketinfo:
                self.logger.warning('windcode:{} got livemarket empty!'.format(windcode))
                continue
            price = eval(marketinfo[0])['lastPrice'] / 10000
            if price == 0:
                self.logger.warning('got price is 0,will got preClose')
                price = eval(redis_cli.get(windcode + 'preAndClose'))['preclose'] / 10000
            datas.append([windcode, price])
        return pd.DataFrame(datas, columns=['windcode', 'lastPrice'], dtype=np.float).set_index('windcode')

    def _loadAssetInfo(self):
        """
        加载策略的assetinfo，position，account
        """
        strategys_str = str(self.strategy_ids).replace("[", "").replace("]", "").strip(",")
        sql = "SELECT strategy_id,trade_date,position_value,cash,total_asset,sod_total_asset,total_pnl,net_value" \
              " FROM asset where strategy_id in ({}) order by trade_date".format(
            strategys_str)
        with mysql(self.env) as cursor:
            cursor.execute(sql)
            data = cursor.fetchall()
            df = pd.DataFrame(list(data),
                                columns=['strategy_id', 'trade_date', 'position_value', 'cash', 'total_asset',
                                         'sod_total_asset', 'total_pnl', 'net_value'])
            df['trade_date'] = df['trade_date'].astype(str)
            return df
    def _loadAccountInfo(self):
        """
        加载策略的accountInfo
        """
        strategys_str = str(self.strategy_ids).replace("[", "").replace("]", "").strip(",")
        sql = "select strategy_id,trade_date,account_type,position_value,cash,total_asset,sod_total_asset " \
              "from account where strategy_id in ({}) and trade_date = '{}'".format(strategys_str,self.trade_date)
        with mysql(self.env) as cursor:
            cursor.execute(sql)
            data = cursor.fetchall()
            df = pd.DataFrame(list(data),columns=accountTable['columns'])
            df['trade_date'] = df['trade_date'].astype('str')
            return df


    def _loadPrePosition(self):
        """
        加载当前持仓信息
        """
        strategys_str = str(self.strategy_ids).replace("[", "").replace("]", "").strip(",")
        sql = "select strategy_id,trade_date,LS,windcode,account_type,amount,volume,notional,pre_close,`close`,pnl " \
              "from  position where strategy_id in ({}) and trade_date = %s".format(
            strategys_str)
        with mysql(self.env) as cursor:
            cursor.execute(sql, self.pre_date)
            data = cursor.fetchall()
            df = pd.DataFrame(list(data),
                                columns=['strategy_id', 'trade_date', 'LS', 'windcode', 'account_type', 'amount',
                                         'volume', 'notional', 'pre_close', 'close', 'pnl'])
            df['trade_date'] = df['trade_date'].astype('str')
            return df

    def _loadTodaySecurityPool(self):
        self.security_pool = {}
        self.security_list = set()
        selection_ids = list(set(config['selection_id'] for config in self.strategy_configs))
        for selection_id in selection_ids:
            self.security_pool[selection_id] = self.getCodesFromMysqlStrategy(selection_id)
            for value in self.security_pool[selection_id].values():
                self.security_list.update(value)
        if self.security_list.__contains__('CASH'):
            self.security_list.remove('CASH')

    def getCodesFromMysqlStrategy(self, selection_id):
        """
        从mysql取出策略筛选的codes
        :return:date_dict
        """
        sql = """select trade_date, windcode from security_pool where security_selection_id='{}' and trade_date='{}' """ \
            .format(selection_id, self.trade_date)
        with mysql(self.env) as cursor:
            cursor.execute(sql)
            data = cursor.fetchall()
        date_dict = {}
        for (trade_date, windcode) in data:
            if date_dict.__contains__(trade_date):
                date_dict[trade_date].append(windcode)
            else:
                date_dict[trade_date] = [windcode]
        return date_dict

    def _loadConfigs(self):
        """
        加载所需各种配置信息
        """
        with mysql(self.env, 'dict') as self.cursor:
            self.strategy_configs = self._getStrategyConfig()
        with mysql(self.env) as self.cursor:
            self.allocation_configs = self._getConfig('allocation_config', 'allocation_id')
            self.risk_configs = self._getConfig('risk_config', 'risk_id')

if __name__ == '__main__':
    som = sendOrderMock(env='dev', mode='mock', strategy_ids=['S-L-4|LastPrice|CLOSE|RISK-169'])
    som.run()