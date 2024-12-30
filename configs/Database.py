import contextlib
import cx_Oracle
import pymysql

DEV = 'dev'
PROD = 'prod'
SHARE = 'share'
TEST = 'test'
AITRADERTEST = 'aitradertest'
AITRADERPROD = 'aitraderprod'

WIND_DB = {'DBTYPE': 'mysql', 'HOST': 'localhost',
           'USER': 'root', 'PASSWORD': 'root', 'DBNAME': 'wind','PORT': 3306}

AI_SHARE = {'DBTYPE': 'mysql', 'HOST': 'localhost',
            'USER': 'root',
            'PASSWORD': 'root',
            'DBNAME': 'ai_share', 'PORT': 3306}
ai_investment_manager_DEV = {'DBTYPE': 'mysql', 'HOST': 'localhost',
            'USER': 'root',
            'PASSWORD': 'root',
            'DBNAME': 'ai_share', 'PORT': 3306}
ai_investment_manager_PROD = {'DBTYPE': 'mysql', 'HOST': 'localhost',
            'USER': 'root',
            'PASSWORD': 'root',
            'DBNAME': 'ai_share', 'PORT': 3306}




AI_DB = dict(
    dev=ai_investment_manager_DEV,
    prod=ai_investment_manager_PROD,
    share=AI_SHARE
)


class Database:
    def __init__(self, db_info, cursor_type=None):
        if db_info['DBTYPE'] == 'oracle':
            self.conn = cx_Oracle.connect(db_info['USER'], db_info['PASSWORD'],
                                          db_info['HOST'] + ':' + str(db_info['PORT']) + '/' + db_info['DBNAME'])
        elif db_info['DBTYPE'] == 'mysql':
            self.conn = pymysql.connect(host=db_info['HOST'],user= db_info['USER'], password=db_info['PASSWORD'], db=db_info['DBNAME'],
                                        port=db_info['PORT'], charset='utf8')

        if cursor_type == 'dict' and db_info['DBTYPE'] == 'mysql':
            self.cursor = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
        else:
            self.cursor = self.conn.cursor()

    def close(self, commit=False):
        if commit:
            self.conn.commit()
        self.cursor.close()
        self.conn.close()


@contextlib.contextmanager
def mysql(env='dev', cursor_type=None,commit=False):
    db = Database(AI_DB[env],cursor_type)
    cursor = db.cursor
    try:
        yield cursor
    finally:
        db.close(commit)

@contextlib.contextmanager
def oracle(cursor_type=None,commit=False):
    db = Database(WIND_DB, cursor_type)
    cursor = db.cursor
    try:
        yield cursor
    finally:
        db.close(commit)

