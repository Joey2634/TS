import pandas as pd
from configs.Database import Database, AI_DB, DEV, mysql


class MultDelete():
    def __init__(self, condition, env):
        self.env = env
        self.tables = ['target_position_backtest', 'adjusted_target_position_backtest', 'asset_backtest',
                       'account_backtest', 'position_backtest', 'trade_backtest','target_order_backtest',
                       'performance_backtest','strategy_config']
        self.strategy_ids = self.getPerformance(condition)
        self.delete()

    def getPerformance(self, condition):
        with mysql(self.env, 'dict') as self.cursor:
            sql = "SELeCT * FROM ai_investment_manager.performance_backtest where strategy_id=benchmark_id"
            self.cursor.execute(sql)
            performance = self.cursor.fetchall()
            performance = pd.DataFrame(performance).query(condition)
            strategy_ids = performance['strategy_id'].tolist()
            return strategy_ids

    def delete(self):
        dataDB = Database(AI_DB[self.env])
        for table in self.tables:
            try:
                if len(self.strategy_ids) > 1:
                    sql = "delete from {} where strategy_id in {}".format(table, tuple(self.strategy_ids))
                elif len(self.strategy_ids) == 1:
                    sql = "delete from {} where strategy_id = '{}'".format(table, self.strategy_ids[0])
                else:
                    return
                dataDB.cursor.execute(sql)
                print(table, 'delete!')
            except Exception as e:
                print(table, e)
        dataDB.conn.commit()
        dataDB.cursor.close()
        dataDB.conn.close()

class MinusDelete():
    def __init__(self, id_like='', env=DEV):
        self.env = env
        self.tables = ['target_position_backtest', 'adjusted_target_position_backtest', 'asset_backtest',
                       'account_backtest', 'position_backtest', 'trade_backtest', 'target_order_backtest',
                       'performance_backtest', 'strategy_config', 'am_config', 'commission_rate']
        self.all_ids = self.find_ids(id_like, 'strategy_config')
        self.done_ids = self.find_ids(id_like,'performance_backtest')
        self.delete()
        pass

    def delete(self):
        dataDB = Database(AI_DB[self.env])
        # todo = set(self.all_ids) - set(self.done_ids)
        # todo = set(self.done_ids)
        todo = self.all_ids
        print(todo)
        for table in self.tables:
            try:
                if len(todo) > 1:
                    sql = "delete from {} where strategy_id in {}".format(table, tuple(todo))
                elif len(todo) == 1:
                    sql = "delete from {} where strategy_id = '{}'".format(table, todo[0])
                else:
                    return
                dataDB.cursor.execute(sql)
                print(table, 'delete!')
            except Exception as e:
                print(table, e)
        dataDB.conn.commit()
        dataDB.cursor.close()
        dataDB.conn.close()

    def find_ids(self, strategy_id, table):
        db = Database(AI_DB[self.env])
        if strategy_id:
            sql = "select distinct strategy_id from " + table + " where strategy_id like '{}';".format(strategy_id + '%')
            db.cursor.execute(sql)
        else:
            sql = "select distinct strategy_id from " + table
            db.cursor.execute(sql)
        do = db.cursor.fetchall()
        do = list([i[0] for i in do])
        db.cursor.close()
        db.conn.close()
        return do

if __name__ == '__main__':
    # MultDelete(condition="sharpe_ratio<1.6",env=DEV)
    MinusDelete('S-L-4|LastPrice|CLOSE|RISK-175|100M')