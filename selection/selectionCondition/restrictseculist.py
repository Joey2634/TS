import os
import sys
now_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(now_path)

from utils.AiData import *
import os
import datetime
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

# ai数据源的数据表
mysql_aidata_config = {'DBTYPE': 'mysql', 'HOST': '172.23.122.238','USER': 'aidata',
                       'PASSWORD': 'Aidatactcs630', 'DBNAME': 'aidatabase','PORT': 3306}
# ai自己的自建表
oracle_aidb_config = {'DBTYPE': 'oracle', 'HOST': '172.23.122.14','USER': 'ai',
                      'PASSWORD': 'citics600030', 'DBNAME': 'AIDB','PORT': 21001}
"""
每日禁买池oracle-->ai_share定时任务
"""


def getForbidden():
    # 禁买池
    aidb_oracle = Database(oracle_aidb_config)
    sql = "select * from v_root_restrictseculist_new"
    aidb_oracle.cursor.execute(sql)
    data = aidb_oracle.cursor.fetchall()

    return data


def insertMysql(res_list, table):
    """当日禁买池，日刷替换"""
    db = Database(AI_SHARE)
    sql_del = "delete from ai_share.{}".format(table)
    db.cursor.execute(sql_del)
    if table == 'restrict_security_list':
        sql_ins = """insert into ai_share.{} values (%s,%s,%s,%s)""".format(table)
    else:
        sql_ins = """insert into ai_share.{} values (%s,%s,%s,%s,%s,%s,%s,%s)""".format(table)
    db.cursor.executemany(sql_ins, res_list)
    db.conn.commit()
    db.cursor.close()
    db.conn.close()

def insertMysql_his(res_list, table):
    """每日禁买池，历史数据"""
    db = Database(AI_SHARE)
    sql_del = "delete from ai_share.{}".format(table)
    db.cursor.execute(sql_del)
    sql_ins = """insert into ai_share.{} values (%s,%s,%s,%s,%s)""".format(table)
    db.cursor.executemany(sql_ins, res_list)
    db.conn.commit()
    db.cursor.close()
    db.conn.close()


# 查询备用万得代码,返回值元组类型
def getReplaceListDB():
    """查询代替windcode"""
    aiwind_oracle = Database(mysql_aidata_config)
    sql = "select * from replace_security_list"
    aiwind_oracle.cursor.execute(sql)
    data = aiwind_oracle.cursor.fetchall()
    aiwind_oracle.close()
    return data


if __name__ == '__main__':
    t = time.time()
    today = datetime.date.today().strftime("%Y%m%d")

    # 禁买池导入,每日替换
    table = 'restrict_security_list'
    res_list = getForbidden()
    insertMysql(res_list, table)
    print('{}, {}导入完成！'.format(today, table))

    # 存每日禁买池,带日期
    table = 'restrict_security_list_his'
    res_list = [list(i) for i in res_list]
    for i in res_list:
        i.insert(0, today)
    insertMysql_his(res_list, table)
    print('{}, {}导入完成！'.format(today, table))

    # 替换windcode
    res_list = getReplaceListDB()
    table = 'replace_security_list'
    insertMysql(res_list, table)
    print('{}, {}导入完成！'.format(today, table))
    print('time spend--', time.time()-t)







