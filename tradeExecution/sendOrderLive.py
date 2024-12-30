# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/12/23 下午3:07
# @Author : lxf
# @File : sendOrderMock.py
# @Project : ai-investment-manager
import re

import arrow
import redis
import logging
import warnings
import traceback
import pandas as pd
import numpy as np
from utils import daily_data
from configs.Database import mysql
from collections import defaultdict
from utils.Date import getTradeSectionDates
from allocation.Allocation import Allocation
from configs.Redis import liveMarketRedisConfig
from risk.riskManagerLive import riskManagerLive
from configs.tableConfig import account as accountTableInfo
from tradingSystem.rootNet.RootNetTrading import RootNetTrading
from tradeExecution.createOrder.targetOrderLive import targetOrderLive
from tradingSystem.CATS.catsserverapi.catsConfig import CatsTypeTotradeAcct, Afuture_exp
from utils.AiData import getWindData, getFuturesContractMultiplierDB, getMarginRate
from tradingSystem.CATS.catsserverapi.sendOrder import run as sendOrderToCats


class sendOrderLive():

    def __init__(self, env='dev', mode='test'):
        """
        生产或模拟环境，过风控，生成order，发单
        mode:   'mock' 模拟程序不发单或发单到模拟撮合系统,
                'test' trading system  发单到测试环境
                'prod' trading system  发单到生产环境
        """
        self.env = env
        self.mode = mode
        self.sendSysId = 'CATS'
        self.userAcctInfo = defaultdict(dict)
        self.logger = logging.getLogger('sendOrderLive')
        self.accountToStrategyid = {}                               # 匹配账户与策略id
        self.accountType = {}                                       # 账户的账户类型
        self.tradingServer = RootNetTrading(env=mode)               # 交易接口
        self.trade_date = arrow.now().date().__format__('%Y%m%d')   # 当前交易日日期
        self.pre_date = getTradeSectionDates(self.trade_date,
                                             -2)[0]                 # 前一个交易日日期
        self.strategy_ids = self._getStrategyIds()                  # 根据env与mode获取当前需处理的策略id

        self._getAccountInfoByStrategyidsAndLogin()                 # 根据策略id获取账户并登录
        try:
            self._loadConfigs()                                         # 加载各种所需配置
            self._loadTodaySecurityPool()                               # 加载今日标的池
            self.prePosition = self._loadPrePosition()                  # 昨日结算持仓明细
            self.assetInfos = self._loadAssetInfo()                     # 加载策略历史资产信息
            self._setWindInfo()                                         # 加载所需历史数据
            self.allcationLive = Allocation(strategy_configs=self.strategy_configs,
                                            allocation_configs=self.allocation_configs,
                                            trade_dates=[self.trade_date],
                                            security_pool=self.security_pool,
                                            market_quotes=self.windInfo,
                                            env=self.env, mode='live')
            self.riskManagerLive = riskManagerLive(env=self.env,
                                                   mode=self.mode,
                                                   assetInfos=self.assetInfos,
                                                   marketData=self.windInfo,
                                                   trade_date=self.trade_date,
                                                   pre_date=self.pre_date,
                                                   strategy_configs=self.strategy_configs,
                                                   risk_configs=self.risk_configs,
                                                   tradingServer=self.tradingServer)
            self.targetOrderLive = targetOrderLive(env=self.env,
                                                   mode=self.mode,
                                                   trade_date=self.trade_date,
                                                   pre_date=self.pre_date,
                                                   assetInfo=self.assetInfos,
                                                   strategyConfigs=self.strategy_configs,
                                                   windData=self.windInfo,
                                                   security_list=self.security_list,
                                                   tradingServer=self.tradingServer,
                                                   nowAssetInfo=self.nowAssetInfo)
        except:
            self.close()
            raise Exception(traceback.format_exc())


    def run(self, orderType='CASH'):
        """
        """
        self.target_position = self.allcationLive.run()
        self.logger.info('targetPosition:\n{}'.format(self.target_position.to_string()))
        preAsset = self.assetInfos[self.assetInfos['trade_date'].str.replace('-', "") == self.pre_date]
        self.adjusted_target_position = self.riskManagerLive.run(todayTargetPosition=self.target_position,
                                                                 prePosition=self.prePosition,
                                                                 preAsset=preAsset,
                                                                 todayAsset=self.nowAssetInfo,
                                                                 todayAccount=self.nowAccount)
        self.logger.info('adjustTargetPosition:\n{}'.format(self.adjusted_target_position.to_string()))
        self.target_order,T0_target_order = self.targetOrderLive.run(targetPosition=self.adjusted_target_position,
                                                                     T0TargetPosition=self.riskManagerLive.T0TargetPosition,
                                                                     nowAsset=self.nowAssetInfo)
        self.logger.info('targetOrders:\n{}'.format(self.target_order.to_string()))
        self.logger.info('T0targetOrders:\n{}'.format(T0_target_order.to_string()))
        # sendOrder
        sendOrderToCats(self.env, mode=self.mode,
                        strategyids=self.strategy_ids,
                        targetOrders=self.target_order,
                        T0TargetOrder=T0_target_order,
                        accountType=orderType)
        if orderType == 'CASH':
            self.saveData()
        else:
            self.updateFutureInfo()

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

    def updateFutureInfo(self):
        regexp = Afuture_exp
        futureOrder = self.target_order[self.target_order['windcode'].apply(lambda x:bool(re.match(regexp,x)))]
        values_s = ''.join('%s,'*futureOrder.shape[1]).strip(",")
        with mysql(self.env, commit=True) as cursor:
            for index, row in futureOrder.iterrows():
                sql = "insert into target_order values ({}) ON DUPLICATE KEY UPDATE volume = '{}',price= '{}'".\
                    format(values_s, row['volume'], row['price'])
                cursor.execute(sql, row.values.tolist())
        self.futureManager.update_Cash_info()
        pass

    def close(self):
        if getattr(self, 'tradingServer'):
            print("close tradingServer connect!")
            self.tradingServer.disconnect()

    # ---------------------------------------- private func ------------------------------------------------------------

    def _getAccountInfoByStrategyidsAndLogin(self):
        """
        根据策略id获取账户信息
        """
        sql_user = "select sys_id,user_acct,user_acct_pwd from user_account"
        with mysql(self.env) as cursor:
            cursor.execute(sql_user)
            data = cursor.fetchall()
            for row in data:
                self.userAcctInfo[row[0]]['user_acct'] = row[1]
                self.userAcctInfo[row[0]]['user_acct_pwd'] = row[2]

        strategids_str = str(self.strategy_ids).replace("[", "").replace("]", "").strip(",")
        sql_cash = "select strategy_id,sys_id,acct_type,cats_acct_type,trade_acct,trade_acct_pwd from cash_account where strategy_id in ({})".format(
            strategids_str)
        with mysql(self.env, cursor_type='dict') as cursor:
            cursor.execute(sql_cash)
            data = cursor.fetchall()
            for row in data:
                if row['sys_id'] == 'rootNet':
                    self.tradingServer.login(acctId=row['trade_acct'],
                                             acctPwd=row['trade_acct_pwd'],
                                             optId=self.userAcctInfo[row['sys_id']]['user_acct'],
                                             optPwd=self.userAcctInfo[row['sys_id']]['user_acct_pwd'],
                                             acctType=row['acct_type'])
                    self.accountToStrategyid[row['trade_acct']] = row['strategy_id']
                    self.accountType[row['trade_acct']] = CatsTypeTotradeAcct[row['cats_acct_type']]
                else:
                    warnings.warn("not support sys_id:{} of strategy:{}".format(row['sys_id'], row['strategy_id']))

    def _setLiveMarketInfo(self):
        """
        根据标的池获取实时行情
        """
        redis_cli = redis.StrictRedis(**liveMarketRedisConfig)
        datas = []
        for windcode in self.security_list:
            marketinfo = redis_cli.lrange(windcode, 0, 0)
            if not marketinfo:
                warnings.warn('windcode:{} got livemarket empty!'.format(windcode))
                continue
            datas.append([windcode, (eval(marketinfo[0])['lastPrice']) / 10000])
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
        rows = []
        nowFundInfos = self.tradingServer.getFundInfo()
        self.nowAccount = self._createAccountInfo(nowFundInfos)
        funds_by_strategy_id = defaultdict(lambda: defaultdict(lambda: 0))
        # 合并同一个策略的信息
        for account, info in nowFundInfos.items():
            strategy_id = self.accountToStrategyid[account]
            if self.accountType[account] == 'CASH':
                position_value = info['currentStkValue']
            elif self.accountType[account] == "FUTURE":
                position_value = info['marginUsedAmt']
            else:
                self.logger.error('unsuport account type! acctid:{}'.format(account))
                position_value = 0
            # position_value = info.get('currentStkValue') + info.get('marginUsed')
            cash = info['usableAmt']
            total_asset = position_value + cash
            funds_by_strategy_id[strategy_id]['position_value'] += position_value
            funds_by_strategy_id[strategy_id]['cash'] += cash
            funds_by_strategy_id[strategy_id]['total_asset'] += total_asset

        for strategy_id, values in funds_by_strategy_id.items():
            position_value = values['position_value']
            cash = values['cash']
            total_asset = values['total_asset']
            pre_net_value = \
                df[(df['trade_date'].str.replace("-", "") == self.pre_date) & (df['strategy_id'] == strategy_id)].net_value.values[0]
            sod_total_asset = \
                df[(df['trade_date'].str.replace("-", "") == self.pre_date) & (df['strategy_id'] == strategy_id)].total_asset.values[0]
            net_value = total_asset / sod_total_asset * pre_net_value
            rows.append([strategy_id, self.trade_date, position_value, cash, total_asset, sod_total_asset, 0, net_value])
        self.nowAssetInfo = pd.DataFrame(rows,
                                         columns=['strategy_id', 'trade_date', 'position_value', 'cash', 'total_asset',
                                                  'sod_total_asset', 'total_pnl', 'net_value'])
        return df

    def _loadPrePosition(self):
        """
        加载当前持仓信息
        """
        position = self.tradingServer.getPositions()
        if isinstance(position, pd.DataFrame):
            position.rename(columns={
                'WIND_CODE': 'windcode',
                'POSITION': 'volume',
                'AMOUNT': 'amount',
            }, inplace=True)
            position = position[['ACCOUNT', 'windcode', 'volume', 'amount', 'LS']]
            position['strategy_id'] = position['ACCOUNT'].map(self.accountToStrategyid)
            position['trade_date'] = self.trade_date
        else:
            return pd.DataFrame(columns=['strategy_id', 'windcode', 'volume', 'amount', 'LS'])
        return position

    def _getStrategyIds(self, strategy_ids=None):
        """
        根据 env和 mode 从数据库获取需处理策略id
        """
        if strategy_ids: return strategy_ids

        with mysql(self.env) as cursor:
            sql = "select distinct strategy_id from strategy_config where mode = %s"
            cursor.execute(sql, self.mode)
            data = cursor.fetchall()
            return [row[0] for row in data]

    def _loadConfigs(self):
        """
        加载所需各种配置信息
        """
        with mysql(self.env, 'dict') as self.cursor:
            self.strategy_configs = self._getStrategyConfig()
        with mysql(self.env) as self.cursor:
            self.allocation_configs = self._getConfig('allocation_config', 'allocation_id')
            self.risk_configs = self._getConfig('risk_config', 'risk_id')

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
        targetOrderLive.updateWindInfoTables(windInfoDict, strategyConfigs=self.strategy_configs,
                                             position=self.prePosition, securities=self.security_list)
        self.windInfo = {}
        sample_size = max(
            set(int(self.allocation_configs[config]['sample_size']) for config in self.allocation_configs)) + 1
        sample_size = max(sample_size, riskManagerLive.maxPreDays)
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
                self.windInfo['multiplier'] = getFuturesContractMultiplierDB(self.windInfo, market_quotes_start_date,
                                                                             self.trade_date)
            elif table == 'CFuturesmarginratio':
                self.windInfo['margin_ratio'] = getMarginRate(self.windInfo, market_quotes_start_date, self.trade_date)
        self.windInfo['liveMarketInfo'] = self._setLiveMarketInfo()  # 根据标的池获取实时行情最新价

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

    def _createAccountInfo(self, nowFundInfos):
        """
        根据从交易系统查到的信息，组成昨日accout信息
        """
        columns = accountTableInfo['columns']
        data = []
        for account, info in nowFundInfos.items():
            if self.accountType[account] == 'CASH':
                position_value = info['currentStkValue']
                cash = info['usableAmt']
                total_asset = position_value + cash + info['tradeFrozenAmt']
            elif self.accountType[account] == "FUTURE":
                position_value = info['marginUsedAmt']
                cash = info['usableAmt']
                total_asset = position_value + cash + info['tradeFrozenAmt']
            else:
                total_asset = position_value = cash = 0
                self.logger.error('unsuport account type! acctid:{}'.format(account))
            data.append([self.accountToStrategyid[account], self.trade_date, self.accountType[account], position_value,
                         cash, total_asset, total_asset])
        preAccount = pd.DataFrame(data=data, columns=columns)
        return preAccount

