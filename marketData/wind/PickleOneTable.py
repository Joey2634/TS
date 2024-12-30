import gzip
import os
import sys
now_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(now_path)

import _pickle
import os
from configs.Database import *
import time
import pandas as pd
from marketData.wind import *

"""
整表录入pickle
"""


def pickleWindData(table):
    """
    wind oracle ---> pickle
    """
    oracle = Database(WIND_DB)

    # 字段名
    print('获取{}表字段名...'.format(table))
    sql1 = "select COLUMN_NAME from all_tab_columns where table_name =upper('{}')".format(table)
    oracle.cursor.execute(sql1)
    columns = oracle.cursor.fetchall()
    columns = [i[0] for i in columns]
    data_res = []
    if columns:
        sql = "select count(1) from wind.{}".format(table)
        oracle.cursor.execute(sql)
        count_num = oracle.cursor.fetchall()
        i = 1
        while i <= count_num[0][0]:
            # 当前年份数据
            print('获取--{}表数据...'.format(table))
            sql = "select {} from (select rownum rn, t.* from wind.{} t where rownum<{}) where rn>={}"\
                .format(','.join(columns), table, i+500000, i)
            oracle.cursor.execute(sql)
            data = oracle.cursor.fetchall()
            i += 500000
            data_res += data

        oracle.cursor.close()
        oracle.conn.close()

        # 剔除 字段OBJECT_ID
        # print('剔除字段OBJECT_ID...')

        df = pd.DataFrame(data_res, columns=columns)  # 拿到全年数据df
        if 'OBJECT_ID' in columns:
            df.drop(['OBJECT_ID'], axis=1, inplace=True)
            columns.remove('OBJECT_ID')

        dir_name = getDirName(table)
        os.system('cd /home/li/Market_Data && mkdir -p {}/{} '.format(dir_name, table))
        # os.system('cd /data2/Market_Data && mkdir {} '.format(table))

        print('存储{}表,中...'.format(table))
        print('-'*30)
        try:
            file_name = table + '.pkl'
            with open('/home/li/Market_Data/{}/{}/'.format(dir_name, table)+file_name, 'wb') as f:
            # with open('/data2/Market_Data/{}/'.format(table)+file_name, 'wb') as f:
                _pickle.dump(df, f, protocol=-1)
        except Exception as e:
            print(e, '{}表数据不存在...'.format(table))
    else:
        print('{}表不存在---------------------------------------'.format(table))


if __name__ == '__main__':
    # table = 'AShareConseption'
    # t = time.time()
    # table = table.upper()
    # dir_name = getDirName(table)
    # # with gzip.open('/data2/Market_Data/{}/{}/{}.pkl'.format(dir_name, table, table), 'rb') as f:
    # with open('/home/li/Market_Data/{}/{}/{}.pkl'.format(dir_name, table, table), 'rb') as f:
    #     dd = _pickle.load(f)
    #     # print(dd)
    # print('本地耗时:---', time.time()-t)

    t = time.time()
    table_names = wind_0419
    table_names = ['AIndexMembers']

    for table in table_names:
        if table not in stock_futures:
            # print('pickle---', table.upper())
            pickleWindData(table)
    print('耗时:---', time.time()-t)













