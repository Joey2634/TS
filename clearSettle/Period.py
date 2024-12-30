import datetime
from clearSettle.multiprocessingPage import  multiProcessings
from configs.Database import *
import pandas as pd
from utils.Date import getTradeSectionDates


class Period(object):

    def __init__(self, strategy_ids, env, mode='prod',  end_day=''):
        """
        获取策略净值、占资净值区间数据
        :param strategy_id:
        :param env:
        :param mode: 是否回测
        :param end_day: 结束日期
        """
        self.strategy_id = strategy_ids
        self.env = env
        self.mode = mode
        self.end_day = end_day
        # 需要计算的区间
        if self.mode == 'backtest':
            self.months = {'1Y': 30 * 12, '2Y': 30 * 24}
        else:
            self.months = {'1m': 30, '3m': 30 * 3, '6m': 30 * 6, '1Y': 30 * 12, 'SY': 0}  # 'SS': 0

    def getPeriodPerformance(self, clearSettle, performance_configs, am_configs, isProd='mock'):
        '''
        多进程计算区间绩效
        clearSettle:清算实例
        :return:
        '''
        paras = [[mode, clearSettle, performance_configs, am_configs, isProd] for mode in self.months]
        period_performance = multiProcessings(5, paras, self.getOnePeriodPerformance)
        return period_performance

    def getOnePeriodPerformance(self, mode, clearSettle, performance_configs, am_configs, isProd):
        data = self.getData(mode, trade_date=self.end_day)
        res = clearSettle.performance(data, performance_configs, isPeriod=True, am_config=am_configs)
        if isProd == 'prod':  # 生产模式算占资
            mi = self.getData(mode, isMI=True, trade_date=self.end_day)
            res.extend(clearSettle.performance(mi, []))
        [i.insert(2, mode) for i in res]
        return res

    def getData(self, mode, isMI=False, trade_date=''):
        '''
        获取分段数据
        :param mode:
        :param isMI:
        :return:
        '''
        res = pd.DataFrame()
        if not trade_date:
            trade_date = datetime.datetime.now().strftime('%Y%m%d')
        for id in self.strategy_id:
            begin_date, end_date = self.getTimePeriod(id, trade_date, mode)
            if isMI:
                data = self.getMNetValuePeriod(id, begin_date, end_date)
            else:
                data = self.getNetValuePeriod(id, begin_date, end_date)
            res = res.append(data)
        return res

    def getPeriod(self, mode, start, end_day):
        """
        调整开始、结束日期
        :param begindate:
        :param months:
        :return:
        """
        if mode == 'SY':
            start_day = end_day[:4] + '0101'
            start_day = getTradeSectionDates(start_day, -2)[-1]
        elif mode == 'SS':
            start_day = start
        else:
            start_day = datetime.datetime.strftime((datetime.datetime.strptime(end_day, '%Y%m%d') + datetime.timedelta(-self.months[mode])),'%Y%m%d')
        start_day = max(start_day, start)
        return start_day, end_day

    def getTimePeriod(self, strategy_id, trade_date, mode='SS'):
        '''
        获取分段开始、结束日期
        :param strategy_id:
        :param mode:
        :return:
        '''
        table = 'asset_backtest' if self.mode=='backtest' else 'asset'
        begin_end_date_sql = "select max(trade_date) as end_date,min(trade_date) as start_date from {} where " \
                             "strategy_id = '{}' and net_value > 0 and trade_date<='{}'".format(table, strategy_id, trade_date)
        with mysql(self.env, cursor_type='dict') as cursor:
            cursor.execute(begin_end_date_sql)
            res = cursor.fetchone()
        begin_date, end_date = str(res.get('start_date')).replace('-',''), str(res.get('end_date')).replace('-','')
        begin_date, end_date = self.getPeriod(mode, begin_date, end_date)
        return begin_date, end_date

    def getNetValuePeriod(self, strategy_id, begin_date, end_date):
        '''
        获取分段净值曲线
        :param strategy_id:
        :param begin_date:
        :param end_date:
        :return:
        '''
        table = 'asset_backtest' if self.mode=='backtest' else 'asset'
        strategy_line_sql = "select strategy_id, trade_date,net_value,net_value_holder from {} where trade_date >='{}' and " \
                            "trade_date<='{}' and strategy_id = '{}'".format(table, begin_date, end_date, strategy_id)
        with mysql(self.env) as cursor:
            cursor.execute(strategy_line_sql)
            strategy_line = cursor.fetchall()
        return pd.DataFrame(strategy_line, columns=['strategy_id', 'date', 'net_value', 'net_value_holder'])


    def getMNetValuePeriod(self, strategy_id, begin_date, end_date):
        '''
        获取分段占资数据
        :param strategy_id:
        :param begin_date:
        :param end_date:
        :return:
        '''
        select_sentence_sql = "select strategy_id, trade_date, position_value, total_pnl from asset where strategy_id='{}' and " \
                              "trade_date >='{}' and trade_date <='{}' ".format(strategy_id, begin_date, end_date)
        with mysql(self.env) as cursor:
            cursor.execute(select_sentence_sql)
            MI_df = pd.DataFrame(cursor.fetchall(), columns=['strategy_id', 'date', 'position_value', 'total_pnl'])
        MI_df['total_pnl'] = MI_df['total_pnl'] - MI_df.loc[0, 'total_pnl'] #分段要减期初收益
        MI_df['MI'] = MI_df['position_value'] - MI_df['total_pnl']
        MI_df.loc[0, 'MI'] = 0
        MI_df['sum_MI'] = MI_df['MI'].cumsum()
        MI_df['index_num'] = MI_df.index.tolist()
        MI_df['avg_MI'] = MI_df['sum_MI'] / MI_df['index_num']
        MI_df['m_net_value'] = round(MI_df['total_pnl'] / MI_df['avg_MI'], 4) + 1
        MI_df.fillna(1, inplace=True)  # 期初净值填充
        return MI_df[['strategy_id', 'date', 'm_net_value']]

