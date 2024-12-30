import cx_Oracle
import pymysql
import os

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


WIND_DB = {'DBTYPE': 'oracle', 'HOST': '10.23.153.15',
           'USER': 'xuchangze', 'PASSWORD': 'xuchangze', 'DBNAME': 'wind', 'PORT': 21010}

AI_SHARE = {'DBTYPE': 'mysql', 'HOST': '172.23.122.238',
            'USER': 'ai_share',
            'PASSWORD': 'ai_share',
            'DBNAME': 'ai_share', 'PORT': 3306}

aidata = {'DBTYPE': 'mysql', 'HOST': '172.23.122.238',
            'USER': 'aidata',
            'PASSWORD': 'Aidatactcs630',
            'DBNAME': 'aidatabase', 'PORT': 3306}


class Database:
    def __init__(self, db_info, cursor_type=None):
        if db_info['DBTYPE'] == 'oracle':
            self.conn = cx_Oracle.connect(db_info['USER'], db_info['PASSWORD'],
                                          db_info['HOST'] + ':' + str(db_info['PORT']) + '/' + db_info['DBNAME'])
        elif db_info['DBTYPE'] == 'mysql':
            self.conn = pymysql.connect(db_info['HOST'], db_info['USER'], db_info['PASSWORD'], db_info['DBNAME'],
                                        db_info['PORT'], charset='utf8')

        if cursor_type == 'dict' and db_info['DBTYPE'] == 'mysql':
            self.cursor = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
        else:
            self.cursor = self.conn.cursor()

    def close(self, commit=False):
        if commit:
            self.conn.commit()
        self.cursor.close()
        self.conn.close()

db = Database(WIND_DB)

# A股
A_sql = """select s_info_windcode, s_info_name from AshareDescription"""
# 港股
HK_sql = """select s_info_windcode, s_info_name from HKsharedescription where securityclass='100001000' 
and s_info_status='101001000' and securitysubclass='100001001' and is_hksc='1'"""
# 美股
M_sql = """select s_info_windcode, s_info_name from USShareWindCustomCode"""

# 港股指数
H_index_sql = """select s_info_windcode, s_info_name from HKIndexDescription where s_info_index_style='旗舰指数'"""

# 债券
zq_sql = """select s_info_windcode, s_info_name from cbonddescription where s_info_windcode like '%SH' or s_info_windcode like '%SZ'"""

# 期货
qh = """select s_info_windcode, s_info_name from cfuturesdescription"""

# A股指数
A_index_sql = """select s_info_windcode, s_info_name from aindexdescription where expire_date is null and (s_info_windcode like '%SH' or s_info_windcode like '%SZ')"""

# 港股
db.cursor.execute(HK_sql)
result = db.cursor.fetchall()
print(result)
# 债券
db.cursor.execute(zq_sql)
result += db.cursor.fetchall()
# 港股指数
db.cursor.execute(H_index_sql)
result += db.cursor.fetchall()

# 美股
# db.cursor.execute(M_sql)
# result += db.cursor.fetchall()
# A股
db.cursor.execute(A_sql)
result += db.cursor.fetchall()
# 期货
db.cursor.execute(qh)
result += db.cursor.fetchall()
# A股指数
db.cursor.execute(A_index_sql)
result += db.cursor.fetchall()
# print(result, len(result))

db.cursor.close()
db.conn.close()

# db2 = Database(aidata)
db2 = Database(AI_SHARE)

# aaa = """update ai_share.security_static_info set exchange_id='HK' where windcode like '%HK'"""
success = 0
fail = 0
# db2.cursor.execute(aaa)
# db2.conn.commit()
# db2.cursor.close()
# db2.conn.close()
# tem = []
# for i in result:
#     if i[0].startswith('600'):
#         tem.append(i)
#
#
# print(tem, len(tem))
# result = tem



update_sql = """insert into security_static_info(windcode, security_name, exchange_id) values (%s, %s, %s)"""

for i in result:
    i = list(i) + [i[0].split('.')[1]]

    try:
        db2.cursor.execute(update_sql, i)
        db2.conn.commit()
        success +=1
    except Exception as e:
        print(e)

        fail +=1
    # exit()
print(success, fail)
db2.cursor.close()
db2.conn.close()







