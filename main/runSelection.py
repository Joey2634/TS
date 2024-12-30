import os
import sys

now_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(now_path)
import multiprocessing
from selection.SecuritySelection import *

"""
定时任务
selection 入口

"""


def runSelection(env, security_selection_id, start_date, end_date, mode):
    """
    筛选选股策略标的池
    :param security_selection_id: 选股策略str
    :param start_date: 起始日期
    :param end_date: 结束日期
    """
    security_selection = SecuritySelection(security_selection_id, start_date, end_date, env,mode)
    security_selection.setSecurityPool()


def multiRun(env, func, security_selection_id_list, start_date, end_date, mode):
    """
    多进程调用函数
    :param func: 函数
    :param security_selection_id_list: 选股策略list
    :param start_date: 起始日期
    :param end_date: 结束日期

    """
    result = []
    pool = multiprocessing.Pool()
    for security_selection_id in security_selection_id_list:
        result.append(pool.apply_async(func, (env, security_selection_id, start_date, end_date, mode)))
    pool.close()
    pool.join()


def run(env, security_selection_id_list, start_date, end_date=datetime.date.today().strftime("%Y%m%d"), mode='backtest'):
    """
    更新策略或条件结果
    """
    multiRun(env, runSelection, security_selection_id_list, start_date, end_date, mode)


if __name__ == '__main__':
    # 1.设置选股策略🆔id
    security_selection_id_list = ['S-L-4','S-L-6', 'S-L-11', 'S-L-13', 'S-L-30','S-L-31']
    # 起止日期
    end_date = datetime.date.today().strftime("%Y%m%d")
    # 起始日期默认设当日一周前的周一
    start_date = (datetime.date.today()-datetime.timedelta(weeks=1))
    while start_date.weekday() != 0:
        start_date -= datetime.timedelta(days=1)
    start_date = start_date.strftime("%Y%m%d")
    # 环境
    # env = DEV
    env = PROD
    mode = 'live'

    # 2.run
    t = time.time()
    for i in security_selection_id_list:
        runSelection(env, i, start_date, end_date, mode)
    # 多进程
    # run(env, security_selection_id_list, start_date, end_date)
    print('time spend----', time.time() - t)










