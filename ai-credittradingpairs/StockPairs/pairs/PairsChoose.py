# -*- coding: utf-8 -*-
from utils.Wheels import getWindcodesByIndex, load_data, standardization
import numpy as np
from pykalman import KalmanFilter
import statsmodels.api as sm


class PairsChoose(object):
    """
    get stock pairs for hedge.
    """
    def __init__(self, start_date, end_date, long_pool_index='000906.SH', short_pool_index='000906.SH', thre=0.01):

        self.start_date = start_date
        self.end_date = end_date
        self.long_pool = getWindcodesByIndex(long_pool_index)
        self.short_pool = getWindcodesByIndex(short_pool_index)
        self.thre = thre
        self.data_dict = {}

    def calcu_p(self, segA, segB):
        return sm.tsa.stattools.coint(segA, segB)[1]

    def load_data(self, wind_code):

        if wind_code in self.data_dict:
            return self.data_dict.get(wind_code)
        else:
            # print(wind_code)
            self.data_dict[wind_code] = load_data(wind_code, self.start_date, self.end_date)
            return self.data_dict.get(wind_code)

    # 保存数据的协整相关性，越小，相关性越强，保存到字典
    def get_pairlist(self, precision=2):

        rslist = []
        pairs_dict = {}
        for codeA in self.long_pool:
            dataA = self.load_data(codeA)
            pairs_dict[codeA] = []
            for codeB in self.short_pool:
                if codeA != codeB:
                    try:
                        dataB = self.load_data(codeB)
                        p1 = self.calcu_p(dataA, dataB)  # P数值越小，相关性越大
                        p2 = self.calcu_p(dataB, dataA)
                        if p1 <= self.thre and p2 <= self.thre:
                            if not pairs_dict[codeA] or pairs_dict[codeA][1] > p1:
                                [slope, intercept] = np.polyfit(dataB, dataA, 1).round(precision)
                                # pairs_dict[codeA] = [codeB, p1]
                                pairs_dict[codeA] = [codeB, slope, intercept]
                    except:
                        pass
        for k, v in pairs_dict.items():
            if v:
                rslist.append([k, v[0]])
        return rslist

    def Future_test_threading(self, codeA, codeB):

        dataA = self.load_data(codeA)
        # dataB = self.load_data(codeB)
        # dd = pd.merge(dataA, dataB, on='timestamp')
        print(dataA)
        # data['zscore'] = (data['spread'] - data['spread'].mean()) / data['spread'].std()



if __name__ == '__main__':
    p = PairsChoose('2019-01-01', '2020-09-30', long_pool_index='000016.SH', short_pool_index='000016.SH')
    p.Future_test_threading('600016.SH', '601360.SH')
    # rslist = p.get_pairlist()
    # print(rslist)
