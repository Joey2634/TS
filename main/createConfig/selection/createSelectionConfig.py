from configs.Database import *
import csv


def createSelectionConfig(env='dev', strategy_configs_file='create_selection_config.csv'):
        with open(strategy_configs_file, mode='r') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            next(csv_reader)
            selection_config_list = []
            for row in csv_reader:
                selection_config_list.append(tuple(row))
        with mysql(env,None,True) as curser:
            sql = "insert into selection_config VALUES (%s,%s,%s,%s)"
            curser.executemany(sql, selection_config_list)


if __name__ == '__main__':
    # 环境
    env = DEV
    # env = PROD
    createSelectionConfig(env)



