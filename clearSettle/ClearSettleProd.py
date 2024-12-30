# -*- coding:utf-8 -*-

"""
@author: NanXu
@file: ClearSettleProd.py
@time: 2020-12-22
实盘环境清算
"""
from collections import defaultdict
from utils.AiData import loadFeeRate, which_table, getWindData, getCommission
from configs.tableConfig import *
from clearSettle.ClearSettle import ClearSettle
from configs.Database import mysql, oracle


class ClearSettleProd(ClearSettle):

    def __init__(self, strategy_configs, am_configs, env='dev', trade_date='', level='DEBUG'):
        super().__init__(strategy_configs, env, level)
        self.initInfo(trade_date, am_configs)
        self.setEXInfo(trade_date)

    def runClearSettle(self):
        """
        主程序入口：计算逻辑，昨日总资产 + 今日盈利 = 今日总资产，今日现金 = 今日总资产 - 今日持仓
        :param trade_date:
        :return: dict(df)
        """
        self.logger.debug('交易日:{}, 计算position和trade'.format(self.trade_date))
        position, trade, df_account = self.coreCal()
        self.logger.debug('交易日:{}, 计算asset'.format(self.trade_date))
        if not df_account.empty:  # 如果df_account为空，说明今天空仓
            df_account = pd.merge(self.account, df_account, on=['strategy_id', 'account_type'], how='left')
        asset = self._asset(df_account, self.asset, trade)
        result = {'asset': asset, 'position': position, 'trade': trade}
        am_fee = self.amf.getAmFee()
        if not am_fee.empty:
            result.update({'am_fee': am_fee})
        return result

    def getProdData(self, trade_date):
        '''
        获取实盘策略生产数据
        收盘生产系统插入trade, position, account
        '''
        # 读取今日trade
        self.cursor.execute("select * from trade where trade_date = '{}' and strategy_id in ({})".format(trade_date, self.id_mysql))
        self.trade = pd.DataFrame(list(self.cursor.fetchall()), columns=trade['columns'])
        # 读取今日position
        self.cursor.execute("select strategy_id,trade_date, windcode, LS, account_type,volume,amount from `position` where trade_date = '{}' and strategy_id in ({})".format(trade_date, self.id_mysql))
        self.position = pd.DataFrame(list(self.cursor.fetchall()), columns=['strategy_id','trade_date','windcode','LS','account_type','volume','amount'])
        # 读取昨日position
        self.cursor.execute("select strategy_id, windcode, LS, account_type,volume,avg_cost from `position` where trade_date = '{}' and volume>0 and strategy_id in ({})".format(self.pre_day, self.id_mysql))
        self.position_pre = pd.DataFrame(list(self.cursor.fetchall()),columns=['strategy_id','windcode','LS','account_type','pre_position','avg_cost'])
        # 读取今日account
        self.cursor.execute("select * from account where trade_date = '{}' and strategy_id in ({})".format(trade_date, self.id_mysql))
        self.account = pd.DataFrame(list(self.cursor.fetchall()), columns=account['columns'])
        # 读取今日asset
        self.cursor.execute("select * from asset where trade_date = '{}' and strategy_id in ({})".format(trade_date, self.id_mysql))
        self.asset = pd.DataFrame(list(self.cursor.fetchall()), columns=asset['columns'])

    def coreCal(self):
        """
        生产情况下只需补数，返回trade,position表以及用于计算asset表的pnl数据
        """
        if self.position.empty and self.trade.empty:
            return self.position, self.trade, pd.DataFrame()
        stock_list = set(self.position['windcode'].values.tolist() + self.trade['windcode'].values.tolist())
        self.fee_rate = loadFeeRate(stock_list, self.strategy_configs)
        #计算position
        df_position = pd.merge(self.position, self.position_pre, on=['strategy_id', 'LS', 'windcode', 'account_type'],how='outer')
        # 除权调整持仓
        EXInfo = self.EXInfo[['windcode', 'stock_bonus']]
        df_position = pd.merge(df_position, EXInfo, on='windcode', how='left')
        df_position.fillna(0, inplace=True)
        df_position['pre_position'] *= (1 + df_position['stock_bonus'])
        # 考虑期货乘数
        df_position['multi'] = df_position.apply(self._fill_multi, axis=1)
        df_position['pre_cost'] = df_position['avg_cost'] * df_position['pre_position'] * df_position['multi']
        df_position['position'] = df_position['volume']
        df_position['pre_close'] = df_position.apply(self._fill_price, axis=1, field='S_DQ_PRECLOSE')
        df_position['close'] = df_position.apply(self._fill_price, axis=1, field='S_DQ_CLOSE')
        df_position['pnl'] = round(df_position['multi'] * df_position['LS'] * (df_position['close'] - df_position['pre_close']) * df_position['pre_position'], 2)  # 持仓收益
        df_position['margin_rate'] = df_position.apply(self.getFutureMarginRate, axis=1)
        df_position['notional'] = df_position['amount'] / df_position['margin_rate']
        df_position['trade_date'].fillna(self.trade_date, inplace=True)
        df_position['trade_date'] = df_position['trade_date'].map(lambda x: str(x).replace('-', ''))
        df_position.fillna(0, inplace=True)
        # 计算trade
        self.trade['business_type'] = self.trade['strategy_id'].map(self.sys_id)
        self.trade['fee_rate'] = self.trade.apply(self._fill_fee_rate, axis=1)
        self.trade['commission_rate'] = self.trade.apply(getCommission, axis=1, commission=self.commissionRate)
        self.trade['fee_rate'] = self.trade['fee_rate'] + self.trade['commission_rate']
        df_trade = self.trade.copy()
        df_trade['close'] = df_trade.apply(self._fill_price, axis=1, field='S_DQ_CLOSE')
        df_trade['fee'] = round(df_trade['fee_rate'] * df_trade['notional'] * -1, 2)
        df_trade['margin_rate'] = df_trade.apply(self.getFutureMarginRate, axis=1)
        df_trade['amount'] = df_trade['margin_rate'] * df_trade['notional']
        # 考虑期货乘数
        df_trade['multi'] = df_trade.apply(self._fill_multi, axis=1)
        #直接与notional计算更准确
        df_trade['trade_earn'] = round(df_trade['multi'] * df_trade['LS'] * df_trade['BS'] * (df_trade['close'] * df_trade['volume'] - df_trade['notional']), 2)
        df_trade['account_type'] = df_trade['windcode'].map(lambda x: 'FUTURE' if x.split('.')[1] in self.FUTURE_END else 'CASH')

        df_trade_tmp = df_trade[['strategy_id','windcode','LS','BS','notional']].copy()
        df_trade_tmp['trade_notional'] = df_trade_tmp['notional'] * df_trade_tmp['BS']
        #合并买卖
        df_trade_tmp = df_trade_tmp[['strategy_id','windcode','LS','trade_notional']].groupby(['strategy_id','windcode', 'LS']).sum().reset_index()
        if not df_trade_tmp.empty:
            df_position=pd.merge(df_position,df_trade_tmp,on=['strategy_id','windcode','LS'],how='left')
            df_position['trade_notional'].fillna(0, inplace=True)
            df_position['avg_cost'] = df_position.apply(self.getAvgCost, axis=1)

        # 调整数据
        df_position, df_trade = self.adjPositionAndTrade(df_position, df_trade)
        df_position = df_position[position['columns']]
        trade_sum = pd.DataFrame(columns=['strategy_id', 'account_type','fee', 'trade_earn'])
        position_sum = pd.DataFrame(columns=['strategy_id', 'account_type', 'pnl'])
        trade_sum = trade_sum.append(df_trade[['strategy_id', 'account_type', 'fee', 'trade_earn']].groupby(['strategy_id', 'account_type']).sum().reset_index())
        position_sum = position_sum.append(df_position[['strategy_id', 'account_type', 'pnl']].groupby(['strategy_id', 'account_type']).sum().reset_index())
        total_sum = pd.merge(trade_sum, position_sum,on=['strategy_id', 'account_type'],how='outer')
        total_sum.fillna(0, inplace=True)
        total_sum['earn_sum'] = total_sum['trade_earn'] + total_sum['fee'] + total_sum['pnl']
        df_trade = df_trade[['strategy_id', 'trade_date', 'windcode', 'BS', 'LS', 'amount', 'volume', 'price', 'fee', 'notional','trade_earn']]
        return df_position, df_trade, total_sum[['strategy_id', 'account_type', 'earn_sum']]

    def setEXInfo(self, trade_date):
        '''
        初始化送转股信息，A股和港股
        :param start_day:
        :return:
        '''
        columns = ['date', 'windcode', 'stock_bonus']
        result = pd.DataFrame(columns=columns)
        with oracle() as cursor:
            sql = "select EX_DATE, S_INFO_WINDCODE, BONUS_SHARE_RATIO+ CONVERSED_RATIO from AShareEXRightDividendRecord where ex_date='{}'".format(trade_date)
            cursor.execute(sql)
            A_stock = pd.DataFrame(cursor.fetchall(), columns=columns)
            sql = "select F_INFO_SPLITANNOECDATE, S_INFO_WINDCODE, F_INFO_SPLITINC from CMFundSplit where F_INFO_SPLITANNOECDATE='{}'".format(trade_date)
            cursor.execute(sql)
            ETF = pd.DataFrame(cursor.fetchall(), columns=columns)
            ETF['stock_bonus'] = ETF['stock_bonus'] - 1  # ETF拆分算法区别配股
            sql = "select S_INFO_WINDCODE, EX_DATE, BONUS_SHARE_RATIO from HKshareEvent where ex_date='{}'".format(trade_date)
            cursor.execute(sql)
            HK = pd.DataFrame(cursor.fetchall(), columns=columns)
        result = result.append(A_stock[['date', 'windcode', 'stock_bonus']])
        result = result.append(ETF[['date', 'windcode', 'stock_bonus']])
        result = result.append(HK[['date', 'windcode', 'stock_bonus']])
        result.fillna(0, inplace=True)
        result = result[result['stock_bonus'] != 0]
        self.EXInfo = result.set_index('date')

    def getMarketDataDict(self):
        '''
        行情数据,今日收盘从mysql拿，昨日收盘从wind行情拿，mysql的数据没考虑除权除息
        '''
        # windInfoDict = defaultdict(list)
        with mysql(self.env) as self.cursor:
            self.cursor.execute("select windcode, `close`, pre_close from ai_stock_price where trade_date = '{}'".format(self.trade_date))
            self.marketData = pd.DataFrame(list(self.cursor.fetchall()),columns=['S_INFO_WINDCODE','S_DQ_CLOSE','S_DQ_PRECLOSE'])
        # codes = set(self.marketData['S_INFO_WINDCODE'].values.tolist())-set(['000001.SH','000300.SH','399001.SZ'])
        # for code in codes:
        #     windInfoDict[which_table(code)].append(code)
        # pd_data = pd.DataFrame()
        # for table, info in windInfoDict.items():
        #     tmp = getWindData(table=table, code_list=info, start_date=self.pre_day, end_date=self.pre_day,
        #                       fields=['S_DQ_CLOSE'])
        #     pd_data = pd_data.append(tmp)
        # pd_data = pd_data.rename(columns={'S_DQ_CLOSE': 'S_DQ_PRECLOSE'})
        # pd_data = pd_data[['S_INFO_WINDCODE','S_DQ_PRECLOSE']]
        # pd_data.reset_index(inplace=True, drop=True)
        # self.marketData = pd.merge(self.marketData, pd_data, on=['S_INFO_WINDCODE'],how='left')
        return self.marketData.set_index('S_INFO_WINDCODE').to_dict()

    def modifyFee(self, trade, diff, position):
        '''
        调整费用,不交易调整持仓收益，交易调整费用，均摊原则，剩余分给费用最多的标的，持仓收益兜底
        '''
        if trade.empty or diff + trade['fee'].sum() > 0:
            index = position[position['pnl'] == max(position['pnl'])].index[0]
            position.loc[index, 'pnl'] += diff
            return trade, position
        n = trade.shape[0] - len(self.no_fee)  # 当日有交易的标的数
        fee = round(diff / n, 2) #平摊到费用
        if fee != 0:
            for index in trade.index:
                if trade.loc[index, 'windcode'] in self.no_fee: continue
                if trade.loc[index, 'fee'] + fee < 0:
                    trade.loc[index, 'fee'] += fee
                    diff -= fee
                    if diff == 0: return trade, position
        if diff != 0:
            index = trade[trade['fee'] == min(trade['fee'])].index[0]
            if trade.loc[index, 'fee'] + diff < 0:
                trade.loc[index,'fee'] += diff
            else:
                index = position[position['pnl'] == max(position['pnl'])].index[0]
                position.loc[index, 'pnl'] += diff
        return trade, position

    def adjPositionAndTrade(self, df_position, trade_info):
        '''
        调整position和trade里面的持仓收益、费用，与系统总损益保持一致
        '''
        ids = set(df_position['strategy_id'].values.tolist() + trade_info['strategy_id'].values.tolist())
        position_df, trade_df = pd.DataFrame(), pd.DataFrame()
        for strategy_id in ids:
            position_id = df_position[df_position['strategy_id'] == strategy_id].copy()
            trade_id = trade_info[trade_info['strategy_id'] == strategy_id].copy()
            cal_pnl = round(position_id['pnl'].sum() + trade_id['trade_earn'].sum() + trade_id['fee'].sum(),2)
            with mysql(self.env) as cursor:
                cursor.execute("select sum(total_asset) from account "
                               "where trade_date <='{}' and trade_date >='{}' and strategy_id ='{}'"
                               "group by strategy_id, trade_date order by trade_date ".format(self.trade_date, self.pre_day, strategy_id))
                res = cursor.fetchall()
                real_pnl = round(res[1][0] - res[0][0], 2)
            diff = round(real_pnl - cal_pnl, 2)
            if diff == 0:
                position_df = position_df.append(position_id)
                trade_df = trade_df.append(trade_id)
                continue
            print("今日实际收益：{}，测算收益：{}，需调整：{}".format(real_pnl, cal_pnl, diff))
            stock_list = set(df_position['windcode'].values.tolist() + trade_info['windcode'].values.tolist())
            self.no_fee = ['511880.SH'] if '511880.SH' in stock_list else []
            trade_id, position_id = self.modifyFee(trade_id, diff, position_id)
            position_df = position_df.append(position_id)
            trade_df = trade_df.append(trade_id)
        return position_df, trade_df

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
        return self.marketDataDict[field].get(row['windcode'], 0)