# -*- coding:utf-8 -*-

"""
@author: NanXu
@file: ClearSettle.py
@time: 2020-11-16
"""
import math
import sys
import logging
import datetime
import os
from clearSettle.Performance import Performance
from clearSettle.assetManagement.AssetManagementFee import AssetManagementFee
from configs.Database import oracle, mysql
from utils.AiData import getWindData, loadCommissionRate
from utils.Date import getTradeSectionDates
from configs.tableConfig import *


class ClearSettle(object):

    def __init__(self, strategy_configs, env='dev', level='INFO'):
        self.strategy_configs = strategy_configs
        self.strategy_id = [strategy_config['strategy_id'] for strategy_config in strategy_configs]
        self.id_mysql = str(self.strategy_id).replace("[", "").replace("]", "").strip(",")  # 查询格式
        self.sys_id, self.performance_dict = self.getBusinessAndPerformance(strategy_configs)
        self.env = env
        self.logger = logging.getLogger(self.strategy_id[0])
        self._logSetting(level=level)
        self.FUTURE_END = ('CFE', 'CZC', 'SHF', 'DCE')

    def runClearSettle(self):
        """
        主程序入口
        """
        pass

    def initInfo(self, trade_date, am_configs):
        '''
        初始化日期、期货保证金率、生产数据、标的行情数据
        '''
        self.trade_date = self.setTradeDate(trade_date)
        self.pre_day = getTradeSectionDates(self.trade_date, -2)[0]
        self.getMulti()
        self.getMarginRate()
        with mysql(self.env) as self.cursor:
            self.getProdData(self.trade_date)
        self.marketDataDict = self.getMarketDataDict()
        self.commissionRate = loadCommissionRate(list(am_configs.keys()), env=self.env)  # 佣金，仅支持资管策略
        self.amf = AssetManagementFee(self.env, am_configs, commissionRate=self.commissionRate)

    def getProdData(self, trade_date):
        '''
        从数据库读取数据
        '''
        pass

    def setTradeDate(self, trade_date):
        '''
        交易日期
        :param trade_date:
        :return:
        '''
        return trade_date if trade_date else datetime.datetime.now().strftime('%Y%m%d')

    def getMarginRate(self):
        '''
        期货合约保证金，生产取交割日晚于交易日的合约
        '''
        with oracle() as cursor:
            sql = "select S_INFO_WINDCODE, TRADE_DT, MARGINRATIO/100 as MARGIN_RATIO from CFUTURESMARGINRATIO "
            cursor.execute(sql)
            result = pd.DataFrame(list(cursor.fetchall()), columns=['S_INFO_WINDCODE', 'TRADE_DT', 'margin_ratio'])
            result.set_index('S_INFO_WINDCODE', inplace=True)
            result.sort_values(by='TRADE_DT', inplace=True)
            self.margin_ratio = result

    def getMulti(self):
        """
        获取合约乘数
        """
        with oracle() as cursor:
            sql = "select S_INFO_WINDCODE,  nvl(S_INFO_PUNIT,1)*nvl(s_info_cemultiplier,1)*nvl(s_info_rtd,1)  from " \
                  "CFUTURESCONTPRO where substr(s_info_windcode, -3)='CFE'"
            cursor.execute(sql)
            data = cursor.fetchall()
        self.multi = pd.DataFrame(data, columns=['code', 'multi']).set_index(['code']).to_dict()['multi']


    def getFutureMarginRate(self, row: pd.Series):
        '''
        填充保证金率
        '''
        if row.empty or row['windcode'].split('.')[1] not in self.FUTURE_END:
            return 1
        return self.margin_ratio.query("S_INFO_WINDCODE=='{}' and TRADE_DT<='{}'".format(row['windcode'], self.trade_date)).iloc[-1, -1]

    def setEXInfo(self, trade_date):
        '''
        初始化配股信息，不考虑分红
        '''
        pass

    def getMarketDataDict(self):
        '''
        初始化行情数据
        :param codes:
        :return:
        '''
        pass

    def coreCale(self, df_position, trade):
        """
        Description: 昨日持仓数据和今日交易数据合并
        核心计算逻辑：每只股票分三个方向计算：多空：多是1，空是-1， 买是1， 卖是-1，
        1，持仓计算收益： 多/空 * 买/卖 * 持仓数量 * （今日收盘价（期货是结算价） - 昨日收盘价（期货是结算价））* 合约乘数
        2，交易计算收益： 多/空 * 买/卖 * 交易数量 * （今日收盘价（期货是结算价） - 交易价）
        3，费率计算： 交易数量 * 交易价 * 费率
        注意：
        股票会出现除权除息：持仓数量=今日持仓数量*送转比例 并取整。除权除息日前一天清算调整
        持仓收益：多/空*昨日持仓数量*昨日收盘价 * 涨跌幅
        期货合约乘数已在order里考虑
        只考虑除权情况，除息的红利仍在持仓里，不考虑加入绩效分析的position_earn
        平均成本 = （昨日持仓成本*昨日持仓 + 今日成交金额*买/卖）/(昨日持仓+今日交易量*买/卖)
        """
        if df_position.empty and trade.empty: return df_position, trade
        columns = ['strategy_id', 'trade_date', 'windcode', 'BS', 'LS', 'amount', 'volume', 'price', 'fee', 'notional',
                   'trade_earn']
        if trade.empty:
            trade = pd.DataFrame(columns=columns)
        # 计算交易收益，按照策略、多空和股票合并
        # 考虑期货乘数
        trade['multi'] = trade.apply(self._fill_multi, axis=1)
        trade['close'] = trade.apply(self._fill_price, axis=1, field='S_DQ_CLOSE')
        trade['fee'] = trade['fee'] * -1
        trade['trade_earn'] = trade['LS'].values * trade['BS'].values * (trade['close'].values - trade['price'].values
                                                            ) * trade['volume'].values * trade['multi'].values# 交易收益
        trade_info = trade[columns]
        trade['volume'] = trade['volume'].values * trade['BS'].values  # volume买卖调整
        trade['trade_notional'] = trade['notional'].values * trade['BS'].values  # 交易金额买卖调整
        if not trade.empty:
            trade = trade[['strategy_id', 'LS', 'windcode', 'volume', 'fee', 'trade_earn', 'trade_notional']].copy()
            trade['fee'] = trade['fee'].astype('float')
            trade['trade_earn'] = trade['trade_earn'].astype('float')
            trade['trade_notional'] = trade['trade_notional'].astype('float')
            trade = trade.groupby(['strategy_id', 'LS', 'windcode']).sum()
            trade.reset_index(drop=False, inplace=True)
        # 合并数据,计算持仓收益
        data = pd.merge(trade, df_position, on=['windcode', 'LS', 'strategy_id'], how='outer')
        data = data.fillna(0)
        # 考虑期货乘数
        data['multi'] = data.apply(self._fill_multi, axis=1)
        data['pre_cost'] = data['avg_cost'] * data['position'] * data['multi']  # 计算昨日持仓成本
        data['account_type'] = data['windcode'].map(lambda x: 'FUTURE' if x.split('.')[1] in self.FUTURE_END else 'CASH')
        data['pre_close'] = data.apply(self._fill_price, axis=1, field='S_DQ_PRECLOSE')
        data['close'] = data.apply(self._fill_price, axis=1, field='S_DQ_CLOSE')
        data['pnl'] = data['LS'] * (data['close'] - data['pre_close']) * data['position'] * data['multi']
        data['position'] = data['position'] + data['volume']  # 根据今日交易调整持仓
        data['earn_sum'] = data['pnl'] + data['trade_earn'] + data['fee']
        data['margin_rate'] = data.apply(self.getFutureMarginRate, axis=1)
        data['notional'] = data.apply(self.adjNotional, axis=1)
        data['amount'] = data['margin_rate'] * data['notional']
        data['avg_cost'] = data.apply(self.getAvgCost, axis=1) #计算平均成本

        # 除权除息调整持仓
        self.tomorrow = getTradeSectionDates(self.trade_date, 2)[-1]
        EXInfo = self.EXInfo.query("date=='{}'".format(self.tomorrow))[['windcode', 'stock_bonus']]
        data = pd.merge(data, EXInfo, on='windcode', how='left')
        XRstock = set(data['windcode'].values.tolist()) & set(EXInfo['windcode'].values.tolist())
        if XRstock:
            data.fillna(0, inplace=True)
            data['position'] = data.apply(self.getXRPosition, axis=1)  # 送转股调整持仓
            data['position'].fillna(0, inplace=True)
            data['avg_cost'] = data['avg_cost'] / (1 + data['stock_bonus'])
        df = data[['strategy_id', 'account_type', 'windcode', 'LS', 'earn_sum', 'position', 'close', 'pre_close',
                   'pnl', 'notional', 'amount', 'avg_cost']]
        return df, trade_info

    def adjNotional(self, row):
        '''
        如果行情为0,取前一交易日市值
        :param row:
        :return:
        '''
        res = row['notional_pre'] if row['close'] == 0 else row['position'] * row['close'] * row['multi']
        return res

    def getXRPosition(self, row):
        '''
        除权持仓调整，多减1防止资金为负
        :param row:
        :return:
        '''
        res = math.floor(row['position'] * (1 + row['stock_bonus']))-1 if row['stock_bonus'] and row['position'] else row['position']
        return res

    def getAvgCost(self, row):
        '''
        计算平均持仓成本
        平均成本 = （昨日持仓成本*昨日持仓*合约乘数 + 今日成交金额*买/卖）/(昨日持仓+今日交易量*买/卖)/合约乘数
        :param row:
        :return:
        '''
        res = 0
        if row['position'] > 0:
            res = (row['pre_cost'] + row['trade_notional']) / row['position'] / row['multi']
        return res

    def performance(self, asset, config, isPeriod=False, am_config={}):
        '''
        绩效指标分析
        :param asset: asset表
        :param config: performance_config表
        :return:
        '''
        # self.logger.debug('计算策略绩效指标')
        self.getBenchmarkPrice(config) #加载行情数据
        if isinstance(asset, list):
            asset = pd.DataFrame(asset, columns=['strategy_id', 'date', 'a', 'b', 'c', 'd', 'e','net_value','net_value_holder'])[['date', 'strategy_id', 'net_value','net_value_holder']]
        asset['date'] = asset['date'].map(lambda x: str(x).replace('-',''))
        result = []
        for id in asset.strategy_id.unique():
            data = asset[asset.strategy_id == id].copy()
            rf, relative_benchmark, absolute_benchmark, capm_benchmark = self.getPerformanceConfig(id, config)
            if 'm_net_value' in data.columns:  # 占资
                data['strategy_m'] = data['m_net_value'] / data['m_net_value'].shift(1) - 1
                data = data[['date', 'strategy_m']]
            else:  # 正常
                data['strategy'] = data['net_value'] / data['net_value'].shift(1) - 1
                data = data[['date', 'strategy']]
                if absolute_benchmark > 0:
                    data = self.getAbsPct(data, absolute_benchmark)[['date', 'strategy', 'absolute']]
            performanc_kpi = Performance(id, relative_benchmark, self.benchmarkPrice, capm_benchmark)
            result.extend(performanc_kpi.getPerformanceAssessment(rf, data).values.tolist())
            # 有资管参数的策略计算持有人绩效
            if am_config and id in am_config:
                result = self.getHolderPerformance(asset[asset.strategy_id == id].copy(), performanc_kpi, rf, result)
            # 按年统计绩效 分段绩效不统计
            if isPeriod:
                continue
            result = self.getYearPerformance(data, performanc_kpi, rf, result)
        return result

    def getHolderPerformance(self, data, performanc_kpi, rf, result):
        '''
        计算持有人绩效指标
        :param data:
        :param performanc_kpi:
        :param rf:
        :param result:
        :return:
        '''
        if 'net_value_holder' in data.columns:
            index_ids = performanc_kpi.performace_metrics_name_dict.keys()
            data['strategy_holder'] = data['net_value_holder'] / data['net_value_holder'].shift(1) - 1
            data = data[['date', 'strategy_holder']].set_index('date')
            result.extend(performanc_kpi.calPerformanceIndex(data.index, data, index_ids, rf).values.tolist())
        return result

    def getYearPerformance(self, data, performanc_kpi, rf, result):
        '''
        按年统计策略绩效
        :param data:
        :param performanc_kpi:
        :param rf:
        :param result:
        :return:
        '''
        data = data.reset_index()
        if 'strategy' in data.columns:
            data['year'] = data['date'].map(lambda x: datetime.datetime.strptime(x, '%Y%m%d').year)
            for i in data['year'].unique():
                tmp = data[data['year'] == i][['date', 'strategy']].copy()
                if tmp.shape[0] < 2:
                    continue
                if tmp.index[0] - 1 >= 0:
                    tmp = tmp.append(data[['date', 'strategy']].iloc[tmp.index[0] - 1])
                tmp.rename(columns={'strategy': 'year-'+str(i)}, inplace=True)
                result.extend(performanc_kpi.getPerformanceAssessment(rf, tmp.sort_index()).values.tolist())
        return result
    def getBenchmarkPrice(self, performance_configs):
        '''
        比较基准行情
        :return:
        '''
        performance_codes = []
        self.benchmarkPrice = {}
        if not performance_configs: return
        for per_conf in performance_configs.values():
            performance_codes.extend(per_conf.get('relative_benchmark').split(","))
            performance_codes.extend(per_conf.get('capm_benchmark').split(","))
        fields = ['S_INFO_WINDCODE', 'TRADE_DT','S_DQ_PRECLOSE', 'S_DQ_CLOSE']
        table = 'AIndexEODPrices'
        self.benchmarkPrice[table] = getWindData(table=table, code_list=set(performance_codes), start_date='20100401',end_date=self.trade_date, fields=fields)
        if self.trade_date not in set(self.benchmarkPrice[table]['TRADE_DT'].values.tolist()):
            with mysql(self.env) as cursor:
                cursor.execute("select windcode, trade_date, pre_close, close from ai_stock_price where trade_date = '{}'".format(self.trade_date))
                marketData = pd.DataFrame(list(cursor.fetchall()),columns=fields)
            marketData = marketData[marketData['S_INFO_WINDCODE'].isin(performance_codes)]
            marketData['TRADE_DT'] = marketData['TRADE_DT'].map(lambda x: str(x).replace('-', ''))
            if marketData.empty:
                raise Exception('比较基准无今日行情')
            self.benchmarkPrice[table] = self.benchmarkPrice[table].append(marketData)
        self.benchmarkPrice[table].set_index(['TRADE_DT', 'S_INFO_WINDCODE'], inplace=True)

    def getBusinessAndPerformance(self, strategy_configs):
        '''
        获得business和performance id
        :param strategy_configs: 策略参数
        :return: dict, dict
        '''
        trading_system, performance_dict = {}, {}
        for config in strategy_configs:
            trading_system[config['strategy_id']] = config['business_type']
            performance_dict[config['strategy_id']] = config['performance_id']
        return trading_system, performance_dict

    def getAbsPct(self, data, rf):
        """
        Description: 获取绝对收益比较基准的涨跌幅数据
        :param data: df
        :param rf: risk free rate
        :return: Dataframe格式
        """
        start_day = datetime.datetime.strptime(data.iloc[0]['date'], '%Y%m%d')
        data['date_num'] = data['date'].map(lambda x: (datetime.datetime.strptime(x, '%Y%m%d') - start_day).days)
        data['PCTCHANGE'] = data['date_num'].map(lambda x: pow(1 + rf, x / 365))
        data['absolute'] = (data['PCTCHANGE'] / data['PCTCHANGE'].shift(1) - 1)
        data.fillna(0, inplace=True)
        return data

    def getPerformanceConfig(self, strategy_id, config):
        '''
        获得无风险利率、相对比较基准、绝对比较基准
        :param strategy_id: 策略ID
        :param config: performan_config表数据
        :return:
        '''
        if config:
            id_config = config[self.performance_dict[strategy_id]]
            rf = float(id_config['risk_free_rate'])
            relative_benchmark = [i for i in id_config['relative_benchmark'].split(',')]
            absolute_benchmark = float(id_config['absolute_benchmark'])
            capm_benchmark = id_config['capm_benchmark'].split(',')
        else:
            rf, relative_benchmark, absolute_benchmark, capm_benchmark = 0.0001, [], [], []  # 默认无风险日利率0.0001
        return rf, relative_benchmark, absolute_benchmark, capm_benchmark

    def addStrategyData(self, pre_df, df):
        '''
        清仓的策略加入df，用于account和asset表
        :param pre_df:
        :param df:
        :return:
        '''
        tmp = pre_df[~(pre_df['strategy_id'].isin(df['strategy_id']))].copy()
        if not tmp.empty:
            tmp['trade_date'] = self.trade_date
            df = df.append(tmp)
        return df

    def _asset(self, account, pre_asset, trade_info):
        '''
        计算asset数据
        total_pnl = pre_total_pnl+daily_pnl
        net_value = total_asset/sod_total_asset * pre_net_value
        :param account: 今日account信息 df
        :param pre_asset: 前一交易日asset df
        param amf: assetManagerFee class
        :return:trade_info 今日trade df
        '''
        pre_asset['trade_date'] = self.trade_date
        asset = account[['strategy_id', 'position_value', 'cash', 'total_asset', 'sod_total_asset', 'earn_sum']].groupby('strategy_id').sum()
        asset.reset_index(drop=False, inplace=True)
        asset = pd.merge(asset, pre_asset[['strategy_id', 'total_pnl', 'net_value', 'net_value_holder', 'trade_date']],on='strategy_id')
        asset['total_pnl'] = asset['total_pnl'].values + asset['earn_sum'].values
        # 扣除资管费用
        self.amf.run(self.trade_date, trade_info, asset, account[account['account_type']=='CASH'][['strategy_id', 'cash']])
        asset = pd.merge(asset, self.amf.allFee, on='strategy_id', how='left')
        asset.fillna(0, inplace=True)
        asset['net_value'] = asset['net_value'].values * asset['total_asset'].values / asset['sod_total_asset'].values
        asset['net_value_holder'] = asset['net_value_holder'].values * (asset['total_asset'].values-asset['pay'].values) / asset['sod_total_asset'].values
        asset = asset[['strategy_id', 'trade_date', 'position_value', 'cash','total_asset', 'sod_total_asset', 'total_pnl', 'net_value', 'net_value_holder']]
        return asset

    def _account(self, position_trade, pre_account):
        '''
        计算account
        有期货标的生成FUTURE和CASH的账户，且策略现金全放入FUTURE账户,期货平仓现金放入现货
        无期货标的只生成CASH账户，策略现金全放入CASH账户
        策略今日总盈亏通过df_position_today计算， 前一交易日总资产从Asset表中取，标的总持仓资产由本函数计算
        1、 有期货
        (1)cash
        期货 = 策略今日总盈亏 + 前一交易日总资产 - 标的总持仓资产
        现货 = 0
        （2）total_asset
        期货 = cash + future_position
        现货 = cash_position
        2、 无期货
        (1)cash
        现货 = 策略今日总盈亏 + 前一交易日总资产 - 标的总持仓资产
        (2)total_asset:
        现货 = cash + cash_position
        3、sod_total_asset 回测逻辑等于前一日总资产，生产需要早盘重新插入
        :param position_trade: 今日交易、持仓汇总数据 df
        :param pre_account: 前一交易日account df
        :return: df_account（计算asset表基础数据）, account表数据 df
        '''
        if position_trade.empty:
            pre_account['trade_date'] = self.trade_date
            df_account = self.addStrategyData(pre_account, pd.DataFrame(columns=['strategy_id', 'position_value', 'cash', 'total_asset', 'sod_total_asset', 'earn_sum']))
            df_account.fillna(0, inplace=True)
            return df_account, pre_account
        position_trade['position_value'] = position_trade['amount']
        df_account = position_trade[['strategy_id', 'account_type', 'earn_sum', 'position_value']].groupby(
            ['strategy_id', 'account_type']).sum()
        df_account.reset_index(drop=False, inplace=True)
        # 回测逻辑下前一日总资产=sod_total_asset
        sod_asset = pre_account[['strategy_id', 'account_type', 'sod_total_asset']]
        df_account = pd.merge(sod_asset, df_account, on=['strategy_id', 'account_type'], how='left')
        df_account.fillna(0, inplace=True)
        df_account['cash'] = df_account['sod_total_asset'].values + df_account['earn_sum'].values - df_account['position_value'].values
        df_account['total_asset'] = df_account['cash'].values + df_account['position_value'].values
        df_account['trade_date'] = self.trade_date
        if not df_account[df_account['cash'] < -0.001].empty:
            raise Exception('{}现金为负:\n{}'.format(self.trade_date, df_account.to_string()))
        account = df_account[
            ['strategy_id', 'trade_date', 'account_type', 'position_value', 'cash', 'total_asset', 'sod_total_asset']]
        account = self.addStrategyData(pre_account, account)
        df_account = self.addStrategyData(pre_account, df_account)
        df_account.fillna(0, inplace=True)
        return df_account, account


    def _position(self, position_trade):
        '''
        计算position
        :param position_trade: position和account公用数据
        :return:position表数据 df
        '''
        if position_trade.empty: return pd.DataFrame(columns=position['columns'])
        position_df = position_trade.copy()
        position_df['trade_date'] = self.trade_date
        df_tmp = position_df[position_df.position < 0]
        if not df_tmp.empty: raise Exception('策略持仓为负数')
        position_df = position_df.rename(columns={'position': 'volume'})
        position_df = position_df[['strategy_id', 'trade_date', 'LS', 'windcode', 'account_type', 'amount',
                                   'volume', 'notional', 'pre_close', 'close', 'pnl', 'avg_cost']]
        return position_df

    def _logSetting(self, level):
        """Description: 初始化日志"""
        logs_path = os.path.join(os.environ['HOME'], 'AI_investment_Data/data/dailyReport/logs')
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
        log_dir_path = os.path.join(logs_path)
        if os.path.exists(log_dir_path):
            pass
        else:
            os.system('mkdir -p {}'.format(log_dir_path))
        log_path = os.path.join(logs_path, '{}_logs'.format(today))
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.formatter = formatter
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            self.logger.setLevel(level)

    def _fill_price(self, row: pd.Series, field='', priceType={}):
        """
        按策略配置里的价格类型，填充成交价
        :param row:
        :return:
        """
        if row.empty:
            return 0
        elif priceType:
            field = priceType[row['strategy_id']]
            if row['windcode'].split('.')[1] in self.FUTURE_END and 'CLOSE' in field:
                field = field.replace('CLOSE', 'SETTLE')
        elif row['windcode'].split('.')[1] in self.FUTURE_END and 'CLOSE' in field:
            field = field.replace('CLOSE', 'SETTLE')
        return self.marketDataDict[field].get(row['windcode'], 0)

    def _fill_multi(self, row: pd.Series):
        """
        填充合约乘数，现货是1
        :param row:
        :return:
        """
        if row.empty:
            return 0
        return self.multi.get(row['windcode'], 1)

    def _fill_fee_rate(self, row: pd.Series):
        if row.empty: return 0
        windcode = row['windcode']
        if row['windcode'].endswith(self.FUTURE_END):
            maincode = windcode[:2] + windcode[-4:]
        else:
            maincode = windcode
        fee_rate = self.fee_rate.query("windcode=='{}'".format(maincode)).query(
            "business_type=='{}'".format(row['business_type'])).query("BS=='{}'".format(row['BS'])).fee_rate.values[0]
        return fee_rate


