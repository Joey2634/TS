from datetime import datetime
import pandas as pd
import numpy as np
from configs.Database import mysql
from configs.tableConfig import account, asset, fee
from utils.AiData import getCommission, fill_account_type
from utils.Date import getTradeSectionDates


class AssetManagementFee(object):
    def __init__(self, env, am_configs, commissionRate={}):
        self.env = env
        self.am_configs = am_configs
        self.nowAssetFee = pd.DataFrame()
        self.allFee = pd.DataFrame(columns=['strategy_id', 'pay'])
        self.commissionRate = commissionRate

    def run(self, trade_date, trade, asset, cash):
        self.setTradeDate(trade_date)
        if not set(asset['strategy_id'].values.tolist()) & set(self.am_configs.keys()):
            return
        self.getData(list(self.am_configs.keys()))
        assetFee = self.calCommission(trade)
        # 计算管理费\托管费\业绩报酬
        self.calAssetFee(asset, assetFee)
        # 计算业绩报酬
        assetDF = asset.drop(columns='cash')
        assetDF = pd.merge(assetDF, cash)
        self._calAllFee(assetDF)

    def getAmFee(self):
        '''
        今日am_fee表数据
        '''
        assetFee = self.nowAssetFee.reset_index()
        assetFee['trade_date'] = self.trade_date
        assetFee = assetFee[fee['columns']]
        assetFee = assetFee[assetFee['strategy_id'].isin(self.am_configs)]
        return assetFee

    def setTradeDate(self, trade_date):
        self.trade_date = trade_date
        self.pre_day = getTradeSectionDates(self.trade_date, -2)[0]
        self.tomorrow = getTradeSectionDates(self.trade_date, 2)[-1]

    def calCommission(self, trade):
        '''
        计算佣金
        '''
        if trade.empty:
            return pd.DataFrame(columns=['commission', 'commission_future'])
        tmp = trade.copy()
        tmp['account_type'] = tmp.apply(fill_account_type, axis=1)
        tmp['commission_rate'] = tmp.apply(getCommission, axis=1, commission=self.commissionRate)
        tmp['commission'] = np.where(tmp['account_type'] == 'CASH', round(tmp['notional'] * tmp['commission_rate'], 2),0)
        tmp['commission_future'] = np.where(tmp['account_type'] == 'FUTURE', round(tmp['notional'] * tmp['commission_rate'], 2),0)
        res = tmp[['strategy_id', 'commission_future', 'commission']].groupby('strategy_id').sum()
        return res

    def calAssetFee(self, assetTable, assetFee):
        '''
        计算管理费、托管费、业绩报酬
        '''
        assetTable = assetTable.apply(self._calManagementAndCustodian, axis=1)
        tmp = assetTable[['strategy_id', 'management_fee_payable', 'custodian_fee_payable']].groupby('strategy_id').sum()
        assetFee = pd.merge(assetFee, tmp, left_index=True, right_index=True, how='outer')
        self.calPerformanceFee(assetTable[asset['columns']], assetFee)

    def _calManagementAndCustodian(self, row):
        '''
        计算管理费和托管费,按sod_total_asset计提，即前一交易日费后总资产，非交易日费用算在后一天
        '''
        days = (datetime.strptime(self.trade_date,'%Y%m%d') - datetime.strptime(self.pre_day,'%Y%m%d')).days
        row['management_fee_payable'] = round(row['sod_total_asset'] * self.am_configs.get(row['strategy_id'],{}).get('management_fee', 0) * days/365,2)
        row['custodian_fee_payable'] = round(row['sod_total_asset'] * self.am_configs.get(row['strategy_id'],{}).get('custodian_fee', 0) * days/365,2)
        return row

    def _calAllFee(self, assetTable):
        '''
        计算实际可转出的资管费用,可用现金以现货现金为准
        '''
        self.allFee = pd.DataFrame(columns=['strategy_id', 'pay'])
        payCondition = datetime.strptime(self.trade_date, '%Y%m%d').month == datetime.strptime(self.tomorrow, '%Y%m%d').month
        if not payCondition and not self.assetFee.empty:
            # 算历史累计费用
            assetFee = self.assetFee.groupby('strategy_id').sum()
            assetFee['m'] = assetFee['management_fee_payable'] - assetFee['management_fee']
            assetFee['c'] = assetFee['custodian_fee_payable'] - assetFee['custodian_fee']
            assetFee['i'] = assetFee['incentive_fee_payable'] - assetFee['incentive_fee']
            self.nowAssetFee = pd.merge(self.nowAssetFee, assetFee[['m','c','i']], left_index=True, right_index=True, how='left')
            self.nowAssetFee.fillna(0, inplace=True)
            # 历史累计+今日
            self.nowAssetFee['management_fee_payable_cumulative'] += self.nowAssetFee['m'] + self.nowAssetFee['management_fee_payable']
            self.nowAssetFee['custodian_fee_payable_cumulative'] += self.nowAssetFee['c'] + self.nowAssetFee['custodian_fee_payable']
            self.nowAssetFee['incentive_fee_payable_cumulative'] += self.nowAssetFee['i'] + self.nowAssetFee['incentive_fee_payable']
            return
        # 有累计应付费用才付费
        if self.preAssetFee.empty or sum(self.preAssetFee['management_fee_payable_cumulative'] + self.preAssetFee['custodian_fee_payable_cumulative'] \
                + self.preAssetFee['incentive_fee_payable_cumulative']) == 0:
            return
        tmp = assetTable.copy().set_index('strategy_id')
        tmp = pd.merge(self.nowAssetFee, tmp, left_index=True, right_index=True, how='left')
        tmp['total_fee'] = tmp['management_fee_payable_cumulative']+tmp['custodian_fee_payable_cumulative']+tmp['incentive_fee_payable_cumulative']
        tmp['need_cash'] = tmp.apply(lambda row: round(row['total_fee'] - row['cash'],2) if row['total_fee'] - row['cash']>0 else 0, axis=1)
        if self.env == 'dev' and not tmp[tmp['need_cash'] > 0].empty:  # 回测才需要self.need_cash
            self.need_cash = tmp[tmp['need_cash'] > 0].copy()
            self.need_cash['trade_date'] = self.tomorrow
            self.need_cash = self.need_cash[['trade_date', 'need_cash']].reset_index()
        tmp = tmp.reset_index().apply(self._adjNowAssetFee, axis=1)
        tmp['trade_date'] = self.trade_date
        self.nowAssetFee = tmp[fee['columns']].set_index('strategy_id')
        tmp['pay'] = tmp.apply(lambda row: row['total_fee'] if row['total_fee'] <= row['cash'] else row['cash'],axis=1)
        self.allFee = tmp[['strategy_id', 'pay']]

    def getTomorrowAssetAndAccount(self, trade_date, strategy_ids):
        '''
        mock prod策略计算第二日sod_total_asset
        :param trade_date: 当前交易日
        :param strategy_ids: 策略id
        :param accountTable: 今日account表数据
        :param assetTable:  今日asset表数据
        :return:
        '''
        self.setTradeDate(trade_date)
        with mysql(self.env) as cursor:
            cursor.execute("select strategy_id,management_fee+custodian_fee+incentive_fee from am_fee where strategy_id in ({}) and trade_date='{}'".format(strategy_ids, trade_date))
            self.allFee = pd.DataFrame(list(cursor.fetchall()), columns=['strategy_id', 'pay'])
            cursor.execute("select * from account where strategy_id in ({}) and trade_date='{}'".format(strategy_ids, trade_date))
            accountTable = pd.DataFrame(list(cursor.fetchall()), columns=account['columns'])
            cursor.execute("select * from asset where strategy_id in ({}) and trade_date='{}'".format(strategy_ids, trade_date))
            assetTable = pd.DataFrame(list(cursor.fetchall()), columns=asset['columns'])
        accountTable, assetTable = self._adjFee(accountTable, assetTable)
        return accountTable, assetTable


    def _adjFee(self, accountTable, assetTable):
        '''
        计算T+1日sod_total_asset
        '''
        accountTable = self._adjTable(accountTable)[account['columns']]
        assetTable = self._adjTable(assetTable)[asset['columns']]
        return accountTable, assetTable

    def _adjNowAssetFee(self, row):
        '''
        调整资管费用的数额
        '''
        if row['need_cash'] == 0:
            for i in ['management_fee', 'custodian_fee', 'incentive_fee']:
                row[i] = row[i + '_payable_cumulative']
                row[i + '_payable_cumulative'] = 0
        else:
            cash = row['cash']
            for i in ['management_fee', 'custodian_fee', 'incentive_fee']:
                if row[i + '_payable_cumulative'] <= cash:
                    row[i] = row[i + '_payable_cumulative']
                    cash -= row[i + '_payable_cumulative']
                    row[i + '_payable_cumulative'] = 0
                else:
                    row[i] += cash
                    row[i + '_payable_cumulative'] -= cash
                    break
        return row

    def _adjTable(self, df):
        '''
        扣除管理费\托管费\业绩报酬, 只调现货
        '''
        df = pd.merge(df, self.allFee, on='strategy_id', how='left')
        if 'account_type' in df.columns:
            df.loc[df[df['account_type'] == 'FUTURE'].index, 'pay'] = 0
        df.fillna(0, inplace=True)
        df['cash'] -= df['pay']
        df['total_asset'] -= df['pay']
        df['sod_total_asset'] = df['total_asset']
        df['trade_date'] = self.tomorrow
        return df

    def incentivePeriodCondition(self, period):
        '''
        业绩报酬计提周期判断
        '''
        if period == '12':
            self.thisYear = self.timeNow.year
            periodCondition = datetime.strptime(self.tomorrow, '%Y%m%d').year - self.thisYear == 1
        elif period == '4':
            thisMonth = self.timeNow.month
            nextMonth = datetime.strptime(self.tomorrow, '%Y%m%d').month
            periodCondition = nextMonth - thisMonth != 0 and thisMonth in [3, 6, 9, 12]
        elif period == '6':  # 半年
            thisMonth = self.timeNow.month
            nextMonth = datetime.strptime(self.tomorrow, '%Y%m%d').month
            periodCondition = nextMonth - thisMonth != 0 and thisMonth in [6, 12]
        else:
            periodCondition = False
        return periodCondition

    def getData(self, strategy_ids:list):
        '''
        读取asset及am_fee历史数据
        :param strategy_ids:
        :return:
        '''
        strategy_ids = str(strategy_ids).replace('[', '').replace(']', '')
        with mysql(self.env) as cursor:
            cursor.execute("select * from am_fee where strategy_id in ({})".format(strategy_ids))
            self.assetFee = pd.DataFrame(list(cursor.fetchall()), columns=fee['columns'])
            cursor.execute("select * from asset where strategy_id in ({})".format(strategy_ids))
            self.asset = pd.DataFrame(cursor.fetchall(), columns=asset['columns'])
        self.preAssetFee = self.assetFee[self.assetFee['trade_date'] == self.pre_day].set_index('strategy_id')

    def getIncentiveData(self, row, method):
        tmp = pd.DataFrame(self.asset, columns=asset['columns'])
        if method in ['HighWaterThreshold', 'HighWater']:  # 高水位门槛法及高水位法
            am_fee = self.assetFee.copy()
            am_fee = am_fee[am_fee['incentive_fee'] > 0]
            # (扣款日，下一个扣款日]，首次扣款是左闭右闭
            if am_fee.empty:
                last_incentive_fee_day = tmp.loc[0, 'trade_date']
                row['ratio'] = ((datetime.strptime(self.tomorrow, '%Y%m%d') - datetime.strptime(tmp.loc[0, 'trade_date'],'%Y%m%d')).days+1) / 365
            else:
                last_incentive_fee_day = am_fee.iloc[-1, 1]
                row['ratio'] = (datetime.strptime(self.tomorrow, '%Y%m%d') - datetime.strptime(last_incentive_fee_day,'%Y%m%d')).days / 365
            date_list = getTradeSectionDates(last_incentive_fee_day, 2)
            # 高水位门槛法：计算业绩报酬的期初总资产取业绩报酬划款的下一交易日sod_total_asset，高水位法：期初总资产取扣款日sod_total_asset
            incentive_fee_day = date_list[-1] if method == 'HighWaterThreshold' else last_incentive_fee_day
            start_date = incentive_fee_day
        else:
            # 门槛法 目前仅支持按年计提
            _tmp = tmp[tmp['strategy_id'] == tmp['strategy_id'].unique()[0]]
            _tmp['year'] = _tmp['trade_date'].map(lambda x: datetime.strptime(x, '%Y%m%d').year)
            _index = _tmp[_tmp['year'] == self.thisYear].index[0]
            start_date = tmp.loc[_index, 'trade_date']
            # 拿上一交易日计算净值
            if _index > 0:
                row['ratio'] = 1
            else:
                row['ratio'] = ((self.timeNow - datetime.strptime(tmp.loc[_index, 'trade_date'], '%Y%m%d')).days + 1) \
                             / ((self.timeNow - datetime(self.thisYear, 1, 1)).days + 1)
        res = tmp[(tmp['strategy_id'] == row['strategy_id']) & (tmp['trade_date'] == start_date)]
        row['sod_total_asset_begin'] = 0 if res.empty else tmp.loc[res.index[0], 'sod_total_asset']
        return row

    def calPerformanceFee(self, assetTable, assetFee):
        '''
        业绩报酬计算
        期末总资产以最后一个交易日total_asset为准
        期初总资产以上一个业绩报酬付款日的下一日sod_total_asset为准
        '''
        res = pd.DataFrame()
        self.timeNow = datetime.strptime(self.trade_date, '%Y%m%d')
        for index, row in assetTable.iterrows():
            method, period, requireReturn, incentiveRatio = self.am_configs.get(row['strategy_id'], {}).get('incentive_fee', 'null:0:0:0').split(':')
            periodCondition = self.incentivePeriodCondition(period)
            if periodCondition:
                row['requireReturn'], row['incentiveRatio'] = float(requireReturn), float(incentiveRatio)
                row = self.getIncentiveData(row, method)
                row = self._calPerformanceFee(row)
            else:
                row['incentive_fee_payable'] = 0
            res = res.append(row[['strategy_id', 'incentive_fee_payable']])
        assetFee = pd.merge(assetFee, res.set_index('strategy_id'), left_index=True, right_index=True, how='outer')
        assetFee.fillna(0, inplace=True)
        if self.preAssetFee.empty:
            assetFee['management_fee_payable_cumulative'] = 0
            assetFee['custodian_fee_payable_cumulative'] = 0
            assetFee['incentive_fee_payable_cumulative'] = 0
        else:
            assetFee['management_fee_payable_cumulative'] = self.preAssetFee['management_fee_payable_cumulative']
            assetFee['custodian_fee_payable_cumulative'] = self.preAssetFee['custodian_fee_payable_cumulative']
            assetFee['incentive_fee_payable_cumulative'] = self.preAssetFee['incentive_fee_payable_cumulative']
        assetFee['management_fee'], assetFee['custodian_fee'], assetFee['incentive_fee'] = 0, 0, 0
        self.nowAssetFee = assetFee

    def _calPerformanceFee(self, row):
        '''
        计算业绩报酬
        '''
        alpha = row['total_asset']/row['sod_total_asset_begin'] - 1 - row['requireReturn'] * row['ratio']
        row['incentive_fee_payable'] = round(alpha * row['incentiveRatio']*row['sod_total_asset_begin'], 2) if alpha > 0 else 0
        return row

