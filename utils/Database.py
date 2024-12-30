import pymysql
import cx_Oracle
import contextlib


class Database():
    def __init__(self, db_info,cursor_type = None):
        if db_info['DBTYPE'] == 'oracle':
            self.conn = cx_Oracle.connect(db_info['USER'], db_info['PASSWORD'],
                                          db_info['HOST'] + ':' + str(db_info['PORT']) + '/' + db_info['DBNAME'])
        elif db_info['DBTYPE'] == 'mysql':
            self.conn = pymysql.connect(db_info['HOST'], db_info['USER'], db_info['PASSWORD'], db_info['DBNAME'],db_info['PORT'], charset='utf8')
        if  cursor_type == 'dict':
            self.cursor = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
        else:
            self.cursor = self.conn.cursor()

    def close(self,commit=False):
        if commit:
            self.conn.commit()
        self.cursor.close()
        self.conn.close()

    

WIND_DB = dict(DBTYPE='oracle', HOST='10.23.153.15', USER='xuchangze', PASSWORD='xuchangze', DBNAME='wind',PORT=21010)
WIND_DB_INFO = dict(DBTYPE='oracle', HOST='172.23.122.14', USER='ai', PASSWORD='citics600030', DBNAME='aidb',PORT=21001)

AI_DB_INFO_COMMON = dict(DBTYPE='mysql', HOST='172.23.122.238', USER='aidata', PASSWORD='Aidatactcs630', DBNAME='aidatabase',PORT=3306)
AI_DB_INFO_MOCK = {'DBTYPE': 'mysql', 'HOST': '172.23.122.238', 'USER': 'aimock', 'PASSWORD': 'aimock123','DBNAME': 'aimockdb', 'PORT': 3306}

AI_DB_INFO_DEV = {'DBTYPE': 'mysql', 'HOST': '172.23.122.18',
                             'USER': 'ai_investment_manager',
                             'PASSWORD': 'ai_investment_manager',
                             'DBNAME': 'ai_investment_manager', 'PORT': 3306}

# AI_DB_INFO_FUT = {'DBTYPE': 'mysql', 'HOST': '172.23.122.18',
#                              'USER': 'ai_arbitrage',
#                              'PASSWORD': 'ai_arbitrage',
#                              'DBNAME': 'ai_arbitrage', 'PORT': 3306}

AI_DB_INFO_PROD = dict(DBTYPE='mysql', HOST='172.23.122.238', USER='aiprod', PASSWORD='aiprod123', DBNAME='aiproddb', PORT=3306)

AI_DB = dict(
            dev=AI_DB_INFO_DEV, # the env to develop new strategy, generate backtest result
            mock=AI_DB_INFO_MOCK, # the
            common=AI_DB_INFO_COMMON,
            prod = AI_DB_INFO_PROD
             )

DEV='dev'
MOCK='mock'
COMMON='common'
PROD = 'prod'

@contextlib.contextmanager
def mysql(env='dev'):
    db=Database(AI_DB[env])
    cursor = db.cursor
    try:
        yield cursor
    finally:
        db.conn.commit()
        cursor.close()
        db.conn.close()


@contextlib.contextmanager
def mysql_conn(env='dev'):
    db=Database(AI_DB[env])
    conn = db.conn
    try:
        yield
    finally:
        conn.commit()
        conn.close()

# mysql 返回字典类型数据
@contextlib.contextmanager
def mysql_Dict(env='dev'):
    db = Database(AI_DB[env],cursor_type='dict')
    cursor = db.cursor
    try:
        yield cursor
    finally:
        db.conn.commit()
        cursor.close()
        db.conn.close()

