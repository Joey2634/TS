# -*- coding: utf-8 -*-

'''
@Project : PyCharm
@File : RealTimeRatio.py
@Contact : cuiweijian@citics.com
@author : Simon
@Date : 2020/11/3
@AddTime 下午4:05
'''
from StockPairs.realtime.RealTimeData import getRealTimeNewPrice
from StockPairs.utils.Database import *
from apscheduler.schedulers.blocking import BlockingScheduler
import arrow
from dateutil.parser import parse
from StockPairs.utils.Wheels import TODAY
from StockPairs.utils.Config import ENV

class RealTimeRatio(object):

    def __init__(self):

        self.scheduler = BlockingScheduler()
        self.pairs_dict,self.params_dict = self.load_params_dict()
        self.pairs_ids = list(self.pairs_dict.keys())
        self.RUNTIME = '9-14'
        self.STOP_TIME = parse(TODAY + " 15:00")
        self.PAUSE_TIME = parse(TODAY + " 11:30")
        self.RESTART_TIME = parse(TODAY + " 13:00")
        self.job_id = 'main'

    def load_params_dict(self):
        pairs_dict,params_dict = {},{}
        db = Database(AI_DB[ENV])
        sql_seg = "SELECT pairs_id,stock_long,stock_short,mean,std FROM stockpairs_params;"
        db.cursor.execute(sql_seg)
        all_res = db.cursor.fetchall()
        for res in all_res:
            pairs_dict[res[0]] = [res[1],res[2]]
            params_dict[res[0]] = [float(res[3]),float(res[4])]

        return pairs_dict,params_dict

    def get_pairs_id(self,codeA,codeB):

        return codeA.split('.')[0]+codeB.split('.')[0]

    def getPairsRatio(self,pairs_id):

        codeA, codeB = self.pairs_dict[pairs_id]
        priceA = getRealTimeNewPrice(codeA)
        priceB = getRealTimeNewPrice(codeB)
        mean,std = self.params_dict[pairs_id]
        ratio = priceA/priceB
        zscore = (ratio - mean)/std
        return priceA,priceB,ratio,zscore

    def save_ratio(self):
        ratio_list = []
        now_time = arrow.now().format('HHmm')
        for id in self.pairs_ids:
            try:
                priceA,priceB,ratio,zscore = self.getPairsRatio(id)
                ratio_list.append([id,now_time,priceA,priceB,ratio,zscore])
            except Exception as e:
                print(e.__str__())
        db = Database(AI_DB[ENV])
        db.cursor.executemany("insert into stockpairs_realtime values(%s,%s,%s,%s,%s,%s)", ratio_list)
        db.conn.commit()
        db.cursor.close()
        db.conn.close()


    def run(self):
        self.scheduler.add_job(self.save_ratio, 'cron', day_of_week='mon-fri', hour=self.RUNTIME, minute='*/1', id=self.job_id)
        self.scheduler.add_job(self.pause_job, next_run_time=self.PAUSE_TIME,  id='pause')
        self.scheduler.add_job(self.restart_job, next_run_time=self.RESTART_TIME, id='restart')
        self.scheduler.add_job(self.shutdown, next_run_time=self.STOP_TIME)
        self.scheduler.start()

    def pause_job(self,):
        # 任务调度。午休暂停。
        job = self.scheduler.get_job(job_id=self.job_id)
        job.pause()

    def restart_job(self,):
        # 任务调度，午休重启。
        job = self.scheduler.get_job(job_id=self.job_id)
        job.resume()

    def shutdown(self):
        # 任务调度，收盘停止交易。
        self.scheduler.shutdown(wait=False)

if __name__ == '__main__':
    rt = RealTimeRatio()
    rt.run()