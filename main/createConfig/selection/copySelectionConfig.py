from configs.Database import *


class CopyStrategyCondition:
    """
    根据已有选股策略条件生成新策略条件
    """

    def __init__(self, new_strategy, old_strategy, new_condition, old_condition, env):
        self.new_strategy = new_strategy
        self.old_strategy = old_strategy
        self.new_condition = new_condition
        self.old_condition = old_condition
        self.env = env

    def load_config(self):
        db = Database(AI_DB[self.env])
        sql_seg = "SELECT * FROM selection_config where selection_id='{}'"\
            .format(self.old_strategy)
        db.cursor.execute(sql_seg)
        allres = db.cursor.fetchall()
        db.cursor.close()
        db.conn.close()
        allres = [i[1]+':'+i[2] for i in allres]
        print(allres)
        return allres

    def set_config(self):
        res_conditions = self.load_config()
        for i in self.old_condition:
            c_index = res_conditions.index(i)
            res_conditions[c_index] = self.new_condition[self.old_condition.index(i)]

        reslist = [i.split(':') for i in res_conditions]
        for i in reslist:
            i.insert(0, self.new_strategy)
            i.append('')
            print(i)
        self.insert_config(reslist)
        return reslist

    def insert_config(self, conditions):
        """
        策略参数存mysql
        """
        db = Database(AI_DB[self.env])
        print(len(conditions))
        sql = """insert into selection_config values (%s,%s,%s,%s)"""
        db.cursor.executemany(sql, conditions)
        db.conn.commit()
        db.cursor.close()
        db.conn.close()


if __name__ == '__main__':
    # 设置new_strategy
    new_strategy = 'S-L-2'
    old_strategy = 'S-L-1'

    # 设置new_condition 需对应
    # new_condition = ['EPS_GROWTH_RATE:-1TD,>=,-10TD', 'EST_ROE_FY1:-1TD,>=,20222222222']
    # old_condition = ['EPS_GROWTH_RATE:-1TD,>=,-9TD', 'EST_ROE_FY1:-1TD,>=,20']
    new_condition = []
    old_condition = []

    # 环境
    env = 'dev'
    env = 'prod'

    # new_strategy old_strategy new_condition old_condition
    B = CopyStrategyCondition(new_strategy, old_strategy, new_condition, old_condition, env)
    b = B.set_config()
    print(b)







