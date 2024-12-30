from clearSettle.ClearSettleMock import ClearSettleMock
from clearSettle.ClearSettleProd import ClearSettleProd
from clearSettle.Period import Period
from clearSettle.assetManagement.AssetManagementFee import AssetManagementFee
from clearSettle.multiprocessingPage import multiProcessings
from clearSettle.performanceIndex import PerformanceIndex
from configs.Database import mysql
from utils.Decorator import func_timer
import pandas as pd

class DailyReport(object):
    def __init__(self, strategy_ids, env, trade_date=None, mode='mock'):
        self.env = env
        self.mode = mode
        self.strategy_ids = strategy_ids
        self.trade_date = trade_date
        self.id_mysql = str(self.strategy_ids).replace("[", "").replace("]", "").strip(",")  # 查询格式
        with mysql(env, 'dict') as self.cursor:
            self.strategy_configs = self._getStrategyConfig()
        with mysql(env) as self.cursor:
            self.performance_configs = self._getConfig('performance_config', 'performance_id')
            self.am_configs = self._getAssetManagementInfo()
        clearSettle = ClearSettleProd if self.mode in ('prod', 'test') else ClearSettleMock
        self.clearSettle = clearSettle(self.strategy_configs, self.am_configs, env=env, trade_date=trade_date, level='DEBUG')
        self.period = Period(strategy_ids, env, end_day=self.trade_date)

    @classmethod
    def dealAMFee(cls, env, trade_date, strategy_ids:list):
        '''
        扣除资管费用，生成明日asset和account
        :return:
        '''
        amf = AssetManagementFee(env, {})
        strategy_ids = str(strategy_ids).replace("[", "").replace("]", "").strip(",")
        account_tomorrow, asset_tomorrow = amf.getTomorrowAssetAndAccount(trade_date, strategy_ids)
        res = {'asset': asset_tomorrow, 'account': account_tomorrow}
        for table, data in res.items():
            cls.insertToMysql(env, table, data.values.tolist(), strategy_ids, amf.tomorrow)

    @func_timer
    def run(self):
        '''
        主程序
        :return:
        '''
        result = self.clearSettle.runClearSettle()
        for table, data in result.items():
            self.insertToMysql(self.env, table, data.values.tolist(), self.id_mysql, self.clearSettle.trade_date)
        performance = self.clearSettle.performance(self.getAsset(), self.performance_configs, am_config=self.am_configs)
        if self.mode == 'prod':  # 生产环境算占资
            mi = self.period.getData('SS', isMI=True)
            performance.extend(self.clearSettle.performance(mi, []))
        self.insertToMysql(self.env, 'performance', performance, self.id_mysql)
        self.getPeriodPerformance()
        self.calTurnover()


    def calTurnover(self):
        '''
        计算换手率
        :return:
        '''
        paras = []
        modes = list(self.period.months) + ['SS']
        for mode in modes:
            for id in self.strategy_ids:
                start_date, end_date = self.period.getTimePeriod(id, self.trade_date, mode)
                paras.append({'strategy_ids': [id], 'env': self.env, 'start_date': start_date, 'end_date': end_date,
                              'mode': mode, 'backtest': False})
                # res = PerformanceIndex.turnover(**paras[-1])
        res = multiProcessings(20, paras, PerformanceIndex.turnover)
        with mysql(self.env, commit=True) as cursor:
            values = str(('%s',) * len(res[0])).replace("'", "")
            cursor.execute("delete from turnover where strategy_id in ({}) and mode in ({})".format(
                str(self.strategy_ids).replace("[", "").replace("]", ""), str(modes).replace('[', '').replace(']', '')))
            cursor.executemany("insert into turnover values {}".format(values), res)

    def _getAssetManagementInfo(self):
        self.cursor.execute("select * from am_config ")
        res = pd.DataFrame(list(self.cursor.fetchall()),columns=['strategy_id','management_fee','custodian_fee','incentive_fee'])
        res = {i.pop('strategy_id'): i for i in list(res.to_dict('index').values())}
        # 填补资管策略默认参数
        for config in self.strategy_configs:
            if config['strategy_id'] not in res and config['business_type']=='A6':
                res.update({config['strategy_id']:res['default']})
        return res

    def getPeriodPerformance(self):
        '''
        计算区间绩效
        :return:
        '''
        res = self.period.getPeriodPerformance(self.clearSettle, self.performance_configs, self.am_configs, isProd=self.mode)
        self.insertToMysql(self.env, 'period_performance', res, self.id_mysql)

    def getAsset(self):
        '''
        获取策略asset信息，用于计算绩效指标
        :return:
        '''
        with mysql(self.env) as cursor:
            cursor.execute("select * from asset where strategy_id in ({}) and trade_date<='{}'".format(self.id_mysql, self.clearSettle.trade_date))
            return list(cursor.fetchall())

    @staticmethod
    def insertToMysql(env, table, data, id_mysql, trade_date=''):
        '''
        插入数据库
        :param table:
        :param data:
        :return:
        '''
        if data:
            sql = "and trade_date>='{}'".format(trade_date) if trade_date else ""
            with mysql(env, commit=True) as cursor:
                values = str(('%s',) * len(data[0])).replace("'", "")
                cursor.execute("delete from {} where strategy_id in ({}) ".format(table, id_mysql) + sql)
                cursor.executemany("insert into {} values {}".format(table, values), data)

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