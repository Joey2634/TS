import time
import arrow
import traceback
from tradingSystem.CATS.catsserverapi.models.Account import LocalOsInfo
from tradingSystem.CATS.catsserverapi.RootNetToCats import RootNetToCats
from configs.Database import mysql


def getInstances(env, trade_acct, type, trade_date):
    """

    :param trade_acct:
    :param type:
    :param trade_date:
    :return:
    """
    sql = "select instanceid from instanceid_record where trade_acct = %s and trade_date = %s and type = %s"
    with mysql(env) as cursor:
        cursor.execute(sql, (trade_acct, trade_date, type))
        data = cursor.fetchall()
        if data:
            return [row[0] for row in data]
        else:
            return []


def stop(env='dev',mode='test', trade_accounts: list = None, type='twap', algoType='AITWAP3'):
    """
    停止已经启动的算法实例
    :param env:
    :param trade_account: 要停止的实例的列表，可为空，代表停止所有账户的实例
    :param type: 要停止的算法实例的类型
    :return:
    """
    trade_date = str(arrow.now().date())
    rntc = RootNetToCats(env=env,mode=mode)
    accountAndstrategy = rntc.getAccountInfoByDB()
    time.sleep(0.5)
    for account, strategy_id in accountAndstrategy:
        if trade_accounts and account.tradeAcct not in trade_accounts: continue
        localInfo = LocalOsInfo()
        if rntc.login(account, localInfo):
            instanceids = getInstances(env, account.tradeAcct, type=type, trade_date=trade_date)
            for instanceId in instanceids:
                print('stop:{}'.format(instanceId))
                try:
                    rntc.catsServer.catsStopAlgo(algoType=algoType, algoInstanceId=instanceId)
                except:
                    traceback.print_exc()

    if rntc.rootNet:
        rntc.close()


if __name__ == '__main__':
    stop(env='prod',mode='prod', type='twap')
