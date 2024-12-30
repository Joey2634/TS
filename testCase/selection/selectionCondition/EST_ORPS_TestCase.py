from selection.selectionCondition.EST_ORPS import *
import unittest
from testCase.selection.selectionCondition import *


class EST_ORPS_TEST(unittest.TestCase):
    def setUp(self):
        self.start_date = '2020-10-29'  # 开始日期

        self.end_date = '2020-10-29'  # 结束日期

        self.env = 'dev'  # 环境

        self.condition = 'EST_ORPS:-1TD,>=,0'  # 条件

        self.security_pool = '000906.SH'  # 成份股代码
        self.name = ConditionRedisKey  # redis key

        self.template, self.para = self.condition.split(':')
        self.para_list = self.para.split(',')
        self.ob = EST_ORPS(self.para_list, self.start_date, self.end_date, self.env)
        self.redis = eval(redisCli.hget(self.name, str(self.condition)))
        self.mysql = getMysql(self.condition, self.start_date, self.end_date, self.env)

    def test_redis(self):
        """
        得到对应日期筛选的标的池
        与redis所存相比
        """
        res_dict = self.ob.getSecurityPool()
        print('测试了', len(res_dict), '天')
        for i in res_dict:
            print(i, '日有', len(res_dict[i]), '个标的')
            print(i, '日redis有', len(self.redis[i]), '个标的')
            self.assertEqual(sorted(res_dict[i]), sorted(self.redis[i]))

    def test_mysql(self):
        """
        得到对应日期筛选的标的池
        与mysql所存相比
        """
        res_dict = self.ob.getSecurityPool()
        print('测试了', len(res_dict), '天')
        for i in res_dict:
            print(i, '日有', len(res_dict[i]), '个标的')
            print(i, '日mysql有', len(self.mysql[i]), '个标的')
            self.assertEqual(sorted(res_dict[i]), sorted(self.mysql[i]))


if __name__ == '__main__':
    unittest.main()


