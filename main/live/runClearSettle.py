import os
import sys
now_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(now_path)
import datetime
from tradingSystem.CATS.catsserverapi.storeEodData import useRootNet
from clearSettle.DailyReport import DailyReport
from utils.Date import getTradeSectionDates

if __name__ == '__main__':
    env = 'prod'
    strategy_id = ['turing_1-3','smart_beta_mult-35']
    today = datetime.datetime.now().strftime('%Y%m%d')
    if today in getTradeSectionDates(today, -1):
        useRootNet(env='prod', mode='prod', commit=True)
        daily_report = DailyReport(strategy_id, env, trade_date=today, mode='prod')
        daily_report.run()
