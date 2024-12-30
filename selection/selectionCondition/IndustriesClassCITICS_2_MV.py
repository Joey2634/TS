import pandas as pd
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
from selection.selectionCondition.SELECTION_CONDITION import *


class IndustriesClassCITICS_2_MV(SelectionCondition):
    """
    中信二级行业 市值最大的2-3只股票
    """

    def __init__(self, paramaters, start_date, end_date, env, mode):
        super().__init__(paramaters, start_date, end_date, env, mode)

    def getData(self):
        with oracle() as cursor:
            cursor.execute(
                "select a.s_info_windcode,b.Industriesname,b.IndustriesCode from AShareIndustriesClassCITICS a ,"
                "AShareIndustriesCode b where substr(a.citics_ind_code,1,4) = substr(b.IndustriesCode,1,4) and "
                "b.levelnum = '2' and a.ENTRY_DT<='{}' "
                "and (a.REMOVE_DT>'{}' or a.REMOVE_DT is NULL) order by 1".format(self.day, self.day))
            data = cursor.fetchall()
            windcode_industry_df = pd.DataFrame(data, columns=['windcode', 'industryname', 'industrycode'])
            ####指数万得代码、行业数字代码
            cursor.execute("select S_INFO_INDEXCODE,S_INFO_INDUSTRYCODE from IndexContrastSector")
            industry_code_df = pd.DataFrame(cursor.fetchall(), columns=['indexcode', 'industrycode'])
            industry_df = pd.merge(windcode_industry_df, industry_code_df, on=['industrycode'], how='inner')
            cursor.execute("select S_INFO_WINDCODE, S_DQ_MV from wind.AShareEODDerivativeIndicator where TRADE_DT={}"
                           .format(self.day))
            mv_df = pd.DataFrame(cursor.fetchall(), columns=['windcode', 'mv'])
            res_df = pd.merge(industry_df, mv_df, on=['windcode'], how='left')
        res = res_df.groupby(['indexcode']).apply(lambda x: x.sort_values(by='mv', ascending=False)).reset_index(
            drop=True)
        res = res.groupby(['indexcode']).head(int(self.threshold))
        codes = res.windcode.values.tolist()
        indexcodes = res.indexcode.values.tolist()
        final_res = ['{}:{}'.format(indexcodes[i], codes[i]) for i in range(len(res))]
        return final_res

    def getSecurityPool(self, selection_condition):
        for i in self.trade_dates:
            self.current_day = i
            self.day = getTradeSectionDates(i, (self.d1 - 1))[0]  # 获取所求日日期
            print(i, '{}:从WIND数据库获取数据中...'.format(selection_condition))
            codes_res = self.getData()  # 筛选后的code
            self.codes_dict[i] = codes_res
        return self.codes_dict

    def setSecurityPool(self, codes_dict, selection_condition):
        condition_key, condition_value = selection_condition.split(':')
        res_list = sum(list(map(lambda x: [[x, condition_key, condition_value, i] for i in codes_dict[x]], self.trade_dates)), [])
        print('条件', selection_condition, '存入mysql中...')
        self.insertMysql(res_list, condition_key, condition_value)
        # 存redis
        if self.redisCli.hexists(ConditionRedisKey, str(selection_condition)):
            condition_redis = eval(self.redisCli.hget(ConditionRedisKey, str(selection_condition)))
            condition_redis.update(codes_dict)
            self.redisCli.hset(ConditionRedisKey, str(selection_condition), str(condition_redis))
        else:
            self.redisCli.hset(ConditionRedisKey, str(selection_condition), str(codes_dict))
        print('条件', selection_condition, '更新到redis中...')


if __name__ == '__main__':
    a = IndustriesClassCITICS_2_MV(['-1TD', 'TOP', '3'], '20150105', '20210316', 'dev', 'backtest')
    codes_dict = a.getSecurityPool('IndustriesClassCITICS_2_MV:-1TD,TOP,3')
    a.setSecurityPool(codes_dict, 'IndustriesClassCITICS_2_MV:-1TD,TOP,3')
    print(1)










