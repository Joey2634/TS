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

WIND_DB = dict(DBTYPE='oracle', HOST='172.23.122.14', USER='edm_base', PASSWORD='', DBNAME='aidb',PORT=21001)
CREDIT_TRADING_DEV = dict(DBTYPE='mysql', HOST='172.23.122.18', USER='root', PASSWORD='', DBNAME='ai_credit_trading', PORT=3306)
CREDIT_TRADING_PROD = dict(DBTYPE='mysql', HOST='172.23.122.238', USER='root', PASSWORD='', DBNAME='ai_credit_trading', PORT=3306)
AI_DB_INFO_COMMON = dict(DBTYPE='mysql', HOST='172.23.122.238', USER='aidata', PASSWORD='', DBNAME='aidatabase',PORT=3306)
AI_DB = {'PROD':CREDIT_TRADING_PROD,'DEV':CREDIT_TRADING_DEV}
AI_SHARE = {'DBTYPE': 'mysql', 'HOST': '172.23.122.238',
            'USER': 'ai_share',
            'PASSWORD': 'ai_share',
            'DBNAME': 'ai_share', 'PORT': 3306}


@contextlib.contextmanager
def mysql(para, cursor_type=None,commit=False):
    db = Database(para, cursor_type)
    cursor = db.cursor
    try:
        yield cursor
    finally:
        db.close(commit)

