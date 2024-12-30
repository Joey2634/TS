# -*- coding:utf-8 -*-
import re
import numpy as np
from datetime import datetime
from CTSlib.ApiUtils import *
from dateutil.parser import parse
from tradingSystem.Trading import Trading
from apscheduler.schedulers.background import BackgroundScheduler
from tradingSystem.innerconfig import tradingSysInfo, rootNet, WIndCodeType, get_time_slot, exchID2name
from tradingSystem.rootNet.DMA import DMA
from tradingSystem.rootNet.AIGenerator import SchedulerNum, SingleLock, OrderCache
from tradingSystem.TradingHelpers import BuildPositionsDF, BuildTradesDF, BuildOrdersDF, \
    BuildOriginalOrdersDF


class RootNetTrading(Trading):
    def __init__(self, env='test'):
        self.__setLog()
        print("Trading 初始化!")
        Logger.info("Trading 初始化!")

        super(RootNetTrading, self).__init__(env)

        self.tradeServer = CtsServer()
        connInfo = self.tradeServer.connect(tradingSysInfo['rootNet']['serverHosts'][env],
                                            tradingSysInfo['rootNet']['serverPorts'][env])
        # self.tradeServer.onOrderNew = self.__onOrderNewReturn
        # self.tradeServer.onQueryPositionList = self.__onQueryPositionInfoReturn
        # self.tradeServer.onQueryKnockList = self.__onQueryKnockInfoReturn

        # printObject (connInfo, '系统连接：')
        # 账户信息
        self.account = {}  #:account={acc1:{acctid:'',pwd:''},acc2:{acctid:"",pwd:""},...}
        # 持仓
        self.positions = []
        # 成交
        self.trades = dict()
        # 委托
        self.orders = dict()
        #
        self.numCreater = SchedulerNum()
        # 标记调用次数

        self.num = 0
        # 根据查询次序形成对应的锁
        self.RLOCK = {}
        # 一个全局单一锁
        self.LOCK = threading.Lock()
        self.stkLock = threading.Lock()
        #
        self.SLOCK = threading.Lock()
        # 日志
        # self.logger = logging.getLogger(__name__)
        # 净委托缓存
        self.ordersCache = None
        # 定时任务启动标志
        self.startAble = True
        # algo stop time
        self.algo_stoptime = None

        self.scheduler = BackgroundScheduler()

        self.TWAP_LOCK = threading.Lock()
        # 当前TWAP正在处理的标的
        # self.current_security = None
        # 同步方法锁
        self.synFun_Lock = threading.Lock()

        #
        self.requestid = 0

        self.singleLock = SingleLock().singleLock

        # order 缓存
        self.order_cache = OrderCache().order_cache
        # 更新order缓存全局锁
        self.singleOrderLock = OrderCache().singleLockOfOrder
        # 启动更新缓存
        # self.caching_orders()

    # 设置日志
    def __setLog(self, log_level=Logger.logLevelDebug, log_path='./logs'):
        # 设置日志路径
        Logger.setLogPath(log_path)
        # 设置日志级别
        Logger.setLogLevel(log_level)
        # 打开控制台输出
        Logger.setLogOutputFlag(False)

    # 账户登录
    def login(self, acctId=None, acctPwd=None, optId=None, optPwd=None):
        try:
            optInfo = self.tradeServer.optLogin(optId, optPwd)
            printObject(optInfo, '柜员登录:')
            acctInfo = self.tradeServer.accountLogin(acctId, acctPwd)
            printObject(acctInfo, '账户登录：')
            Logger.info("{}账户登录成功".format(acctId))
            Logger.info("{}柜员登录成功".format(optInfo))
            self.account[acctId] = acctInfo
            return True
        except Exception as e:
            Logger.error(str(e))
            print("登录异常 错误信息如下:\n{}".format(str(e)))

    # 缓存当前委托
    def caching_orders(self):

        df = self.getOrders()
        if not df.empty:
            # rows = df.shape[0]
            # for i in range(rows):
            #     row =df.iloc[i]
            #     account = row['ACCOUNT']

            for row in df.itertuples(index=True, name='pandas'):
                key = getattr(row, 'ACCOUNT') + "^" + getattr(row, 'WIND_CODE') + "^" + getattr(row, "TRADE_TYPE")
                value = int(getattr(row, 'ORDER_VOLUME'))
                current_valume = self.order_cache[key]
                if self.scheduler.running:
                    if current_valume != value:
                        Logger.warn(
                            "发现不一致的情况：本地{}的记录数量为{},查询到的数量为{}".format(getattr(row, 'WIND_CODE'), current_valume, value))
                        print(
                            "发现不一致的情况：本地{}的记录数量为{},查询到的数量为{}".format(getattr(row, 'WIND_CODE'), current_valume, value))
                with self.singleOrderLock:
                    self.order_cache[key] = value
            print("更新缓存!")

        if not self.scheduler.running:
            self.scheduler.start()
            self.scheduler.add_job(self.caching_orders, trigger='cron', minute="*/15", id="caching orders")
            endtime = parse("15:00:00")
            self.scheduler.add_job(self.scheduler_stop, next_run_time=endtime, id='caching orders stop')

    def scheduler_stop(self):
        self.scheduler.shutdown(wait=False)

    # 断开服务器
    def disconnect(self, close_time=None):
        if close_time:
            self.algo_stoptime = parse(close_time)

            if not self.scheduler.running:
                self.scheduler.start()
                self.scheduler.add_job(func=self.tradeServer.disConnect, next_run_time=self.algo_stoptime,
                                       id='disconnect to server')

        else:
            self.tradeServer.disConnect()
        # printString('断开Python API服务链接')

    # 查询实时行情
    def getStkInfo(self, windcode):

        with self.stkLock:
            stkId, exchId = windcode.split('.')
            exchId = rootNet['wind2ExchID'][exchId]
            stkInfo = self._queryStkInfo(stkId=stkId, exchId=exchId)
            return stkInfo

    def getStkInfo_without_lock(self, windcode):
        stkId, exchId = windcode.split('.')
        exchId = rootNet['wind2ExchID'][exchId]
        stkInfo = self._queryStkInfo(stkId=stkId, exchId=exchId)
        return stkInfo

    # 查询当前总资金金额
    def getCash(self, where=None):
        """
        # 资金账号查询
        :param where: 不为空时传一个字典{账户id:"账户id"}
        :return:一个字典,key是账号id,value为此账户的资金金额
        """
        result = {}
        if not where:
            for k, v in self.account.items():
                queryAccountResponse = self.tradeServer.queryAccountInfo(k)
                # T+1日可用金额 = T日可用金额+交易冻结金额
                result[
                    k] = queryAccountResponse.usableAmt + queryAccountResponse.currentStkValue + queryAccountResponse.tradeFrozenAmt
        else:
            acctids = where['acct']
            for acctid in acctids:
                queryAccountResponse = self.tradeServer.queryAccountInfo(acctid)
                # T+1日可用金额 = T日可用金额+交易冻结金额
                result[
                    acctid] = queryAccountResponse.usableAmt + queryAccountResponse.currentStkValue + queryAccountResponse.tradeFrozenAmt

        return result

    def getPositonValue(self, where=None):
        """

        :param where:
        :return:
        """
        result = {}
        if not where:
            for k, v in self.account.items():
                queryAccountResponse = self.tradeServer.queryAccountInfo(k)
                # T+1日可用金额 = T日可用金额+交易冻结金额
                result[k] = queryAccountResponse.currentStkValue
        else:
            acctids = where['acct']
            for acctid in acctids:
                queryAccountResponse = self.tradeServer.queryAccountInfo(acctid)
                # T+1日可用金额 = T日可用金额+交易冻结金额
                result[acctid] = queryAccountResponse.currentStkValue
        return result

    def getFundInfo(self, where=None):

        result = {}
        if not where:
            for k, v in self.account.items():
                queryAccountResponse = self.tradeServer.queryAccountInfo(k)
                # T+1日可用金额 = T日可用金额+交易冻结金额
                result[k] = obj2dic(queryAccountResponse)
        else:
            acctids = where['acct']
            for acctid in acctids:
                queryAccountResponse = self.tradeServer.queryAccountInfo(acctid)
                # T+1日可用金额 = T日可用金额+交易冻结金额
                result[acctid] = obj2dic(queryAccountResponse)
        return result

    # 查询可用金额
    def getAvaCash(self, where=None):
        """
        :param where: {acctid:"账户id'}
        :return:{acctid:金额}
        """
        result = {}
        if not where:
            for k, v in self.account.items():
                queryAccountResponse = self.tradeServer.queryAccountInfo(k)
                # T+1日可用金额 = T日可用金额+交易冻结金额
                result[k] = queryAccountResponse.usableAmt
        else:
            acctids = where['acct']
            for acctid in acctids:
                queryAccountResponse = self.tradeServer.queryAccountInfo(acctid)
                # T+1日可用金额 = T日可用金额+交易冻结金额
                result[acctid] = queryAccountResponse.usableAmt
        return result

    # 查询当前持仓

    def getPositions(self, where=None):
        """
        :param where: {acct:["120021313"],windcode:["600030.SH"],...}
        :return:
        """
        try:
            # self.requestid = sequenceManager.getNextId
            self.positions = []

            def inner_get(acctId, windcode=None):
                queryCond = QueryPositionCond()
                queryCond.acctId = acctId
                result = self.tradeServer.queryPositionList(queryCond, maxRowNum=10000, pageNum=1, syncFlag=True)
                if result:
                    for row in result:
                        returnData = row
                        try:
                            ls = 1
                            if returnData.exchId in WIndCodeType['future']:
                                # 从aidata2获取
                                # multiplier = 1
                                if returnData.realTimePositionQty == 0:  # 过滤掉开仓还未成交项
                                    continue

                                elif returnData.bsFlag == 'S':
                                    ls = -1
                                    returnData.realTimePositionQty = -returnData.realTimePositionQty

                                wind_exch_id = rootNet['exchID2wind'][returnData.exchId]
                                wind_code = returnData.stkId + '.' + wind_exch_id

                                # [[账户(多级)], 万得代码, 市场类型, 证券代码, 证券名称, 持仓数量, 持仓金额, 持仓成本]
                                position = [[returnData.acctId], wind_code, returnData.exchId, returnData.stkId,
                                            returnData.stkName,
                                            returnData.realTimePositionQty,
                                            returnData.ydContractAmt + returnData.todayContractAmt,
                                            returnData.realtimeCost,
                                            ls]
                            elif returnData.exchId in WIndCodeType['stock']:

                                if returnData.currentQtyForAsset == 0:  # 去除 已卖掉 未结算
                                    continue
                                if returnData.previousCost == 0:
                                    returnData.previousCost = returnData.currentStkValue / returnData.currentQtyForAsset

                                wind_exch_id = rootNet['exchID2wind'][returnData.exchId]
                                wind_code = returnData.stkId + '.' + wind_exch_id
                                # [[账户(多级)], 万得代码, 市场类型, 证券代码, 证券名称, 持仓数量, 持仓金额, 持仓成本]
                                position = [[returnData.acctId], wind_code, returnData.exchId, returnData.stkId,
                                            returnData.stkName,
                                            returnData.currentQtyForAsset,
                                            returnData.currentStkValue, returnData.previousCost,
                                            ls]
                            self.positions.append(position)
                        except Exception as e:
                            traceback.print_exc()
                            Logger.error("获取持仓信息失败" + repr(e))
                else:
                    Logger.info("当前账户还没有持仓信息!")


            if where:
                if "acct" in where:
                    acctIds = where['acct']
                    for acctid in acctIds:
                        with self.LOCK:
                            inner_get(acctid)

                else:
                    for k, v in self.account.items():
                        with self.LOCK:
                            inner_get(k)
            else:
                for k, v in self.account.items():
                    with self.LOCK:
                        inner_get(k)

            if not self.positions:
                self.positions.append([['NONE'], 'NONE', 'NONE', 'NONE', 'NONE', 0, 0.0, 0.0])
            # sequenceManager.getNextId = self.requestid
            return BuildPositionsDF(self.positions, ["ACCOUNT"], where)

        except Exception as e:
            Logger.error(str(e) + "获取持仓失败!")

    # 查询当日成交

    def getTrades(self, where=None):
        try:
            self.trades = dict()
            def inner_get(acctid, windcode=None):
                queryCond = QueryKnockCond()
                queryCond.acctId = acctid
                result = self.tradeServer.queryKnockList(queryCond, maxRowNum=10000, pageNum=1, syncFlag=True)
                if result:
                    for row in result:
                        returnData = row
                        try:
                            if returnData.exchId in WIndCodeType['future']:
                                orderType = returnData.bsFlag + '/' + returnData.f_offSetFlag
                                trade = np.array([returnData.knockQty, returnData.knockAmt], dtype=float)

                                key = returnData.acctId + '.' + returnData.stkName + '.' + orderType + '.' + returnData.stkId + '.' + returnData.exchId
                                if (self.trades.__contains__(key)):
                                    self.trades[key] += trade
                                else:
                                    self.trades[key] = trade

                            elif returnData.exchId in WIndCodeType['stock']:
                                orderType = returnData.orderType
                                if orderType == '0B':
                                    orderType = 'B'
                                if orderType == '0S':
                                    orderType = 'S'
                                trade = np.array([returnData.knockQty, returnData.knockAmt], dtype=float)

                                key = returnData.acctId + '.' + returnData.stkName + '.' + orderType + '.' + returnData.stkId + '.' + returnData.exchId
                                if returnData.tradingResultTypeDesc == u'买入成交' or returnData.tradingResultTypeDesc == u'卖出成交':
                                    if (self.trades.__contains__(key)):
                                        self.trades[key] += trade
                                    else:
                                        self.trades[key] = trade
                        except Exception as e:
                            traceback.print_exc()
                            Logger.error("获取成交信息失败" + repr(e))

                else:
                    print("当前账户{}没有成交信息!".format(acctid))

            # 如果传了账号
            if where:
                if "acct" in where:
                    acctids = where["acct"]
                    for acctid in acctids:
                        with self.LOCK:
                            inner_get(acctid)

                else:
                    for k, v in self.account.items():
                        with self.LOCK:
                            inner_get(k)

            # 如果什么也没传
            else:
                for k, v in self.account.items():
                    with self.LOCK:
                        inner_get(k)

            if not self.trades:
                return []
            trades_array = []
            for k, v in self.trades.items():
                key_list = k.split('.')
                acctid = key_list[0]
                windcode = key_list[3] + "." + rootNet['exchID2wind'][key_list[4]]

                trade = [[acctid]] + [windcode] + k.split('.')[1:] + v.tolist()
                trades_array.append(trade)

            return BuildTradesDF(trades_array, ['ACCOUNT'], where)

        except Exception as e:
            Logger.error(str(e) + "本次查询交易信息失败")


    def getOrders(self, where=None):

        try:
            self.orders = dict()
            queryCond = QueryOrderCond()

            def inner_get(acctid, windcode=None, ):

                queryCond.acctId = acctid
                if windcode:
                    stkId, exchId = windcode.split(".")
                    queryCond.stkId = stkId
                    queryCond.exchId = rootNet['wind2ExchID'][exchId]
                queryCond.withdrawFlag = 'F'
                # 将异步查询转化为同步查询
                # result = NoSyn.syncExecuteNoSyncFunction(self.tradeServer, acctid, self.tradeServer.queryOrderList,[queryCond, 1000000, 1], 'onQueryOrderList')
                result = self.tradeServer.queryOrderList(queryCond, maxRowNum=10000, pageNum=1, syncFlag=True)
                if result:
                    for returnData in result:
                        # 将返回的字典转化为类对象
                        try:
                            if returnData.exchId in WIndCodeType['future']:
                                orderType = returnData.bsFlag + '/' + returnData.f_offSetFlag

                            elif returnData.exchId in WIndCodeType['stock']:
                                orderType = returnData.orderType
                                if orderType == '0B':
                                    orderType = 'B'
                                if orderType == '0S':
                                    orderType = 'S'

                            key = returnData.acctId + '.' + orderType + '.' + returnData.stkId + '.' + returnData.exchId

                            if returnData.validFlag == 0:
                                if (self.orders.__contains__(key)):
                                    self.orders[key] += (returnData.orderQty - returnData.withdrawQty)
                                else:
                                    self.orders[key] = (returnData.orderQty - returnData.withdrawQty)
                            else:
                                if returnData.validFlagDesc == "不合法":

                                    print("委托不合法,信息如下")
                                    printObject(returnData)
                                else:
                                    Logger.warn(self._getObjectInfo(returnData))
                                    print(returnData.validFlagDesc)

                        except Exception as e:
                            traceback.print_exc()
                            Logger.error("获取委托失败" + repr(e))
                else:
                    print("当前账户{}还没有委托！".format(acctid))

            try:
                if where:
                    if "acct" in where:
                        acctids = where["acct"]
                        for acctid in acctids:
                            if "windcode" in where:
                                windcodes = where["windcode"]
                                for windcode in windcodes:
                                    with self.LOCK:
                                        inner_get(acctid, windcode=windcode)
                            else:
                                with self.LOCK:
                                    inner_get(acctid)
                    else:
                        for k, v in self.account.items():
                            with self.LOCK:
                                inner_get(k)
                else:
                    if self.account:
                        for k, v in self.account.items():
                            with self.LOCK:
                                inner_get(k)


            except Exception as e:
                Logger.error(str(e) + "给定查询条件出错")

            if (not self.orders):
                return BuildOrdersDF([], ["ACCOUNT"], where)
            orders_array = []
            for k, v in self.orders.items():
                keys = k.split('.')
                acctid = keys[0]
                windcode = keys[2] + '.' + rootNet['exchID2wind'][keys[3]]
                order = [[acctid]] + [windcode] + k.split('.')[1:] + [v]
                orders_array.append(order)

            return BuildOrdersDF(orders_array, ["ACCOUNT"], where)
        except Exception as e:
            Logger.error(str(e) + "查询委托失败!")

    def sendOrder(self, orders, algo=DMA(), syncFlag=True):
        """
        :param orders:订单集合
        :param algo: 算法
        :param syncFlag: True为同步,False为异步
        :return:
        """
        try:

            if not orders:
                print("不能传入空订单")
                return
            for k, v in orders.items():
                if k not in self.account:
                    print("请先登录此账户{}!".format(k))
                    continue
                for order in v:
                    order.acctId = k
                    self._sendOrderHelper(order, algo=algo, syncFlag=syncFlag)
            # 发送完成,启动任务
            # print(algo.__class__.__name__)
            if self.startAble:
                if algo.__class__.__name__ == "TWAP":
                    if not algo.scheduler.running:
                        algo.start()


        except Exception as e:
            Logger.error(str(e) + "发送订单失败")

    # def sendNotionalOrder(self, orders, algo=DMA(), syncFlag=False):
    #     """
    #     :param orders:订单集合
    #     :param algo: 算法
    #     :param syncFlag: True为同步,False为异步
    #     :return:
    #     """
    #     try:
    #
    #         if not orders:
    #             print("不能传入空订单")
    #             return
    #         for k, v in orders.items():
    #             if k not in self.account:
    #                 print("请先登录此账户{}!".format(k))
    #                 continue
    #             for notional_order in v:
    #                 notional_order.acctId = k
    #                 self._sendNotionalOrderHelper(notional_order, algo=algo, syncFlag=syncFlag)
    #         # 发送完成,启动任务
    #         # print(algo.__class__.__name__)
    #
    #         if algo.__class__.__name__ == "TWAP":
    #             if not algo.scheduler.running:
    #                 algo.start()
    #
    #
    #     except Exception as e:
    #         Logger.error(str(e) + "发送订单失败")

    # 获取原始委托
    def getOriginalOrder(self, where=None):
        """
        根据条件获取相应的原始委托单据
        :param where:条件{}
        :return:dataframe
        """
        try:

            # self.tradeServer.onQueryOrderList = self.__onQueryOrderInfoReturnDataFrame
            self.ordersCache = []
            # self.requestid = sequenceManager.getNextId
            queryCond = QueryOrderCond()

            def inner_get(acctid, windcode=None):
                # num = int(next(self.numCreater.num))

                # self.RLOCK[num] = threading.Event()
                # sequenceManager.getNextId = lambda: num
                queryCond.acctId = acctid
                if windcode:
                    stkId, exchId = windcode.split(".")
                    queryCond.stkId = stkId
                    queryCond.exchId = rootNet['wind2ExchID'][exchId]
                queryCond.isCancellable = 'Y'
                queryCond.withdrawFlag = 'F'
                # result = NoSyn.syncExecuteNoSyncFunction(self.tradeServer, acctid, self.tradeServer.queryOrderList,
                #                                          [queryCond, 1000000, 1], 'onQueryOrderList')
                result = self.tradeServer.queryOrderList(queryCond, maxRowNum=10000, pageNum=1, syncFlag=True)
                # self.tradeServer.queryOrderList(queryCond, maxRowNum=100000, pageNum=1)
                # printString("waiting...")
                # self.RLOCK[num].wait()
                if result:
                    for row in result:
                        returnData = row
                        try:
                            if returnData.validFlag == 0:
                                Logger.info("该笔委托的合同号是" + str(returnData.batchNum))
                                windcode = returnData.stkId + "." + rootNet["exchID2wind"][returnData.exchId]

                                if returnData.exchId in WIndCodeType['future']:
                                    orderType = returnData.bsFlag + '/' + returnData.f_offSetFlag
                                    self.ordersCache.append(
                                        [[returnData.acctId], windcode, orderType, returnData.stkId, returnData.exchId,
                                         returnData.orderQty, returnData.knockQty, returnData.futureOrderPrice,
                                         returnData.isCancellable,
                                         returnData.acctId + '^^' + returnData.exchId + '^^' + returnData.contractNum])

                                elif returnData.exchId in WIndCodeType['stock']:
                                    orderType = returnData.orderType
                                    if orderType == '0B':
                                        orderType = 'B'
                                    if orderType == '0S':
                                        orderType = 'S'

                                    self.ordersCache.append(
                                        [[returnData.acctId], windcode, orderType, returnData.stkId, returnData.exchId,
                                         returnData.orderQty, returnData.knockQty, returnData.orderPrice,
                                         returnData.isCancellable,
                                         returnData.acctId + '^^' + returnData.exchId + '^^' + returnData.contractNum,
                                         returnData.orderTime, returnData.orderStatus
                                         ])

                            else:
                                if returnData.validFlagDesc == "不合法":

                                    print("委托不合法,信息如下")
                                    printObject(returnData)
                                else:
                                    Logger.warn(self._getObjectInfo(returnData))
                                    print(returnData.validFlagDesc)
                        except Exception as e:
                            traceback.print_exc()
                            print("获取原始委托信息失败" + repr(e))

                else:
                    print("当前账户{}还没有委托".format(acctid))

            # 将查询限定条件变为参数
            try:
                if where:
                    if "acct" in where:
                        acctids = where["acct"]
                        for acctid in acctids:
                            if "windcode" in where:
                                windcodes = where["windcode"]
                                for windcode in windcodes:
                                    with self.LOCK:
                                        inner_get(acctid, windcode=windcode)

                            else:
                                with self.LOCK:
                                    inner_get(acctid)

                    else:
                        for k, v in self.account.items():
                            with self.LOCK:
                                inner_get(k)
                else:
                    for k, v in self.account.items():
                        with self.LOCK:
                            inner_get(k)


            except Exception as e:
                Logger.error(str(e) + "给定查询条件有误!")
            order_list = self.ordersCache
            # sequenceManager.getNextId = self.requestid
            return BuildOriginalOrdersDF(order_list, ["ACCOUNT"], where)
        except Exception as e:
            Logger.error(str(e) + "获取原始委托信息失败!")

    def cancelOrder(self, ids=list()):
        """
        通过传入的特定id列表,取消相应的委托
        :param ids:
        :return:
        """
        for id in ids:
            acctid, exchid, contractNum = id.split("^^")
            self._cancelOrderHelper(acctid, exchid, contractNum)

    def _cancelOrderHelper(self, acctid, exchid, contractNum):
        """
        接收必须参数,组建ordercancelinfo类,调取消订单接口
        :param acctid:账号
        :param exchid:市场代码
        :param contractNum:合同号
        :return:
        """
        orderCancelInfo = OrderCancelInfo()
        orderCancelInfo.acctId = acctid
        orderCancelInfo.exchId = exchid
        orderCancelInfo.contractNum = contractNum
        with self.LOCK:
            MsgOrdercancel = self.tradeServer.orderCancel(orderCancelInfo)
        print("""撤单结果:
              合同号:{}
              委托时间:{}
              成功笔数:{}""".format(MsgOrdercancel.contractNum, MsgOrdercancel.orderTime, MsgOrdercancel.completeNum))

    # ------------------ --------- ---------  非公开函数 -----------------------------------------------------
    # 发送订单
    def _sendOrderHelper(self, order, algo=DMA(), syncFlag=False):
        '''
        :param order: 订单信息
        :param algo: 下单算法
        :param syncFlag: 是否异步（当前默认异步）
        :return: None
        '''
        # 将统一格式订单转化成根网格式订单
        with self.LOCK:
            try:
                orderInfo = OrderNewInfo()
                orderInfo.acctId = order.acctId
                [stkId, exchId] = order.windCode.split('.')
                orderInfo.stkId = stkId
                orderInfo.exchId = rootNet['wind2ExchID'][exchId]

                if orderInfo.exchId in WIndCodeType['future']:
                    orderInfo.currencyId = self.account[order.acctId].currencyId
                    orderInfo.orderQty = order.orderQty
                    orderInfo.orderPrice = order.orderPrice
                    orderInfo.bsFlag, orderInfo.f_offSetFlag = order.orderType.split('/')
                    orderInfo.f_orderPriceType = order.tradeType

                else:
                    orderInfo.orderQty = order.orderQty
                    orderInfo.orderType = order.orderType
                    orderInfo.orderPrice = order.orderPrice
                # orderInfo.batchNum = 10000000

                # 订单数量小于 0 不下单
                if (orderInfo.orderQty <= 0):
                    print('账户[%s] 交易所[%s] 标的[%s]: 未委托订单数量是0. 不需要再下订单', orderInfo.acctId, exchID2name[exchId],
                          orderInfo.stkId)
                    # 不启动任务
                    self.startAble = False
                    return
                # 获取交易所交易时段信息
                morning_open = get_time_slot(exchId, 'morning_open')
                morning_close = get_time_slot(exchId, 'morning_close')
                afternoon_open = get_time_slot(exchId, 'afternoon_open')
                afternoon_close = get_time_slot(exchId, 'afternoon_close')
                now = datetime.now()
                # 收市后不下单
                if (now >= afternoon_close):
                    printString('%s: 已经收市了', exchID2name[exchId])
                    self.startAble = False
                    return
                # 非交易时段不下单
                if (now < morning_open or (now >= morning_close and now < afternoon_open)):
                    printString('%s: 非交易时段不下单', exchID2name[exchId])
                    self.startAble = False
                    return
                stkInfo = self.tradeServer.queryStkInfo(orderInfo.exchId, orderInfo.stkId)
                # 标的停牌了
                if not orderInfo.exchId in WIndCodeType['future']:
                    if (stkInfo.closeFlag != 'F'):
                        printObject(stkInfo, '此标的停牌了：')
                        return
                # 根据交易算法下委托
                algo.execute(self.tradeServer, orderInfo, syncFlag)
            except Exception as e:
                Logger.error(e)


    def __onQueryPositionInfoReturn(self, returnData, msgRespond):
        num = sequenceManager.getNextId()

        try:
            if (msgRespond.successFlg != 0):
                self.RLOCK[num].set()
                printString('%s,%s', (msgRespond.errorCode, msgRespond.errorMsg))
            else:
                if not hasattr(returnData, 'previousCost'):
                    printString('无持仓')
                    self.RLOCK[num].set()
                    return
                if (returnData.previousCost == 0):
                    returnData.previousCost = returnData.currentStkValue / returnData.currentQtyForAsset
                wind_exch_id = rootNet['exchID2wind'][returnData.exchId]
                wind_code = returnData.stkId + '.' + wind_exch_id
                # [[账户(多级)], 万得代码, 市场类型, 证券代码, 证券名称, 持仓数量, 持仓金额, 持仓成本]
                position = [[returnData.acctId], wind_code, returnData.exchId, returnData.stkId, returnData.stkName,
                            returnData.currentQtyForAsset,
                            returnData.currentStkValue, returnData.previousCost]
                self.positions.append(position)
                if (msgRespond.lastFlag):
                    # printString('查询数据全部返回')
                    self.RLOCK[num].set()
        except Exception as e:
            Logger.error(e)
            self.RLOCK[num].set()

    # 异步获取成交回报
    # 成交查询
    def __onQueryKnockInfoReturn(self, returnData, msgRespond):
        num = sequenceManager.getNextId()

        try:
            if (msgRespond.successFlg != 0):

                Logger.warn('{},{}'.format(msgRespond.errorCode, msgRespond.errorMsg))
                self.RLOCK[num].set()
            else:
                if not hasattr(returnData, 'exchId'):
                    printString('无持仓')
                    self.RLOCK[num].set()
                    return
                trade = np.array([returnData.knockQty, returnData.knockAmt], dtype=float)
                orderType = returnData.orderType
                if orderType == '0B':
                    orderType = 'B'
                if orderType == '0S':
                    orderType = 'S'
                key = returnData.acctId + '.' + returnData.stkName + '.' + orderType + '.' + returnData.stkId + '.' + returnData.exchId
                if returnData.tradingResultTypeDesc == u'买入成交' or returnData.tradingResultTypeDesc == u'卖出成交':
                    if (self.trades.__contains__(key)):
                        self.trades[key] += trade
                    else:
                        self.trades[key] = trade
                if (msgRespond.lastFlag):
                    self.RLOCK[num].set()
                    # printString('查询数据全部返回')
            return
        except Exception as e:
            self.RLOCK[num].set()
            Logger.error(e)

    # 异步获取净已委托信息
    def __onQueryOrderInfoReturn(self, returnData, msgRespond):
        num = sequenceManager.getNextId()
        # print(num)
        try:
            if (msgRespond.successFlg != 0):
                printString('报单查询：')
                printString('%s,%s', (msgRespond.errorCode, msgRespond.errorMsg))
                self.RLOCK[num].set()
            else:
                if not hasattr(returnData, 'exchId'):
                    Logger.info('当前账户没有委托信息')
                    self.RLOCK[num].set()
                    return
                orderType = returnData.orderType
                if orderType == '0B':
                    orderType = 'B'
                if orderType == '0S':
                    orderType = 'S'
                key = returnData.acctId + '.' + orderType + '.' + returnData.stkId + '.' + returnData.exchId

                if returnData.validFlag == 0:
                    if (self.orders.__contains__(key)):
                        self.orders[key] += (returnData.orderQty - returnData.withdrawQty)
                    else:
                        self.orders[key] = (returnData.orderQty - returnData.withdrawQty)
                else:
                    if returnData.validFlagDesc == "不合法":

                        print("委托不合法,信息如下")
                        printObject(returnData)
                    else:
                        Logger.warn(self._getObjectInfo(returnData))
                        print(returnData.validFlagDesc)
                if (msgRespond.lastFlag):
                    # printString('查询数据全部返回')
                    self.RLOCK[num].set()
        except Exception as e:
            self.RLOCK[num].set()
            Logger.error(e)

    # 异步缓存委托信息
    def __onQueryOrderInfoReturnDataFrame(self, returnData, msgRespond):
        num = sequenceManager.getNextId()
        try:
            if (msgRespond.successFlg != 0):
                printString('报单查询：')
                printString('%s,%s', (msgRespond.errorCode, msgRespond.errorMsg))
                self.RLOCK[num].set()
            else:
                if not hasattr(returnData, 'exchId'):
                    printString('当前账户没有委托信息')
                    self.RLOCK[num].set()
                    return
                if returnData.validFlag == 0:
                    print(returnData.batchNum)
                    windcode = returnData.stkId + "." + rootNet["exchID2wind"][returnData.exchId]
                    orderType = returnData.orderType
                    if orderType == '0B':
                        orderType = 'B'
                    if orderType == '0S':
                        orderType = 'S'
                    self.ordersCache.append(
                        [[returnData.acctId], windcode, orderType, returnData.stkId, returnData.exchId,
                         returnData.orderQty, returnData.knockQty, returnData.orderPrice,
                         returnData.isCancellable,
                         returnData.acctId + '^^' + returnData.exchId + '^^' + returnData.contractNum])

                else:
                    if returnData.validFlagDesc == "不合法":

                        print("委托不合法,信息如下")
                        printObject(returnData)
                    else:
                        Logger.warn(self._getObjectInfo(returnData))
                        print(returnData.validFlagDesc)
                if (msgRespond.lastFlag):
                    # printString('查询数据全部返回')
                    self.RLOCK[num].set()
        except Exception as e:
            self.RLOCK[num].set()
            Logger.error(e)

    # 异步获取委托返回信息
    # 新委托创建后，此回调函数将被调用
    def __onOrderNewReturn(self, returnData, msgRespond, msgHead):
        if (msgRespond.successFlg != 0):
            printString('报单有误,结果如下：')
            printString('%s,%s', (msgRespond.errorCode, msgRespond.errorMsg))
            # 委托信息有误,更新本地委托数量
            self.caching_orders()
            Logger.error('本次委托 报单有误,结果如下：%s,%s' % (msgRespond.errorCode, msgRespond.errorMsg))
        else:
            Logger.info("报单结果：{}报单返回头:{}".format(self._getObjectInfo(returnData), self._getObjectInfo(msgHead)))

            print("下委托成功!")

    # 获取类属性和值的str
    def _getObjectInfo(self, obj):
        attrs = dir(obj)
        result = ""
        p = re.compile("__.*__")
        for attr in attrs:
            m = p.search(attr)
            if m == None:
                result += "." + str(attr) + "=" + str(getattr(obj, attr)) + "\n"
        return result

    def _queryAccountInfo(self, acctid):

        return self.tradeServer.queryAccountInfo(acctid)

    def _queryStkInfo(self, exchId, stkId):

        return self.tradeServer.queryStkInfo(exchId=exchId, stkId=stkId)


# 将字典变为类
def dic2obj(d):
    top = type('new', (object,), d)
    seqs = tuple, list, set, frozenset
    for i, j in d.items():
        if isinstance(j, dict):
            setattr(top, i, dic2obj(j))
        elif isinstance(j, seqs):
            setattr(top, i,
                    type(j)(dic2obj(sj) if isinstance(sj, dict) else sj for sj in j))
        else:
            setattr(top, i, j)
    return top


def obj2dic(obj):
    attrs = dir(obj)
    result = {}
    p = re.compile("__.*__")
    for attr in attrs:
        m = p.search(attr)
        if m == None:
            # result += "." + str(attr) + "=" + str(getattr(obj, attr)) + "\n"
            result[attr] = getattr(obj, attr)
    return result
