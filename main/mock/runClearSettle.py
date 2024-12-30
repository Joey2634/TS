import os
import sys
import datetime
now_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(now_path)
from utils.Date import getTradeSectionDates
from clearSettle.DailyReport import DailyReport

def revertTodaySod(env, today, strategy_id):
    '''
    重刷今日日初数据
    :return:
    '''
    pre_day = getTradeSectionDates(today, -2)[0]
    DailyReport.dealAMFee(env, pre_day, strategy_id)


if __name__ == '__main__':
    env = 'dev'
    # strategy_id = ['smart_beta_sz50-1', 'smart_beta_hs300-1',
    #                'S-L-4|LastPrice|CLOSE|RISK-38',
    #                'turing_1-1', 'turing_2-1', 'turing_3-1',
    #                'S-L-4|LastPrice|CLOSE|RISK-169',
    #                'stock_long_2-1','stock_long_1-1',
    #                'L-M-D-1', 'S-L-4|LastPrice|CLOSE|RISK-175-1|100M|2']
    strategy_id = ['M-L|LastPrice|CLOSE|RISK-175-2|100M|m19',
                   'M-L|LastPrice|CLOSE|RISK-175-2|100M|lm']
    today = datetime.datetime.now().strftime('%Y%m%d')
    if today in getTradeSectionDates(today, -1):
        # revertTodaySod(env, today, strategy_id)  # 用于重刷清算
        daily_report = DailyReport(strategy_id, env, trade_date=today, mode='mock')
        daily_report.run()
        daily_report.dealAMFee(env, today, strategy_id)  # 今日asset和account扣费
