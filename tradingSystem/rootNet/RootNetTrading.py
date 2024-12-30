# !/usr/bin/python3
# -*- coding: utf-8 -*-
import re
from collections import defaultdict
from datetime import datetime
from CTSlib.ApiUtils import *
from dateutil.parser import parse
from tradingSystem.Trading import Trading
from apscheduler.schedulers.background import BackgroundScheduler
from tradingSystem.innerconfig import tradingSysInfo, rootNet, WIndCodeType, get_time_slot, exchID2name
from tradingSystem.rootNet.DMA import DMA
from tradingSystem.rootNet.AIGenerator import OrderCache


class RootNetTrading(Trading):
    def __init__(self, env='test', log_level=Logger.logLevelInfo, log_path='./log', consoleOut=False):
        self.__setLog(log_level=log_level, log_path=log_path, consoleOut=consoleOut)
        super(RootNetTrading, self).__init__(env)
        print("rootNet Trading 初始化!")
        self.tradeServer = CtsServer()
        connInfo = self.tradeServer.connect(tradingSysInfo['rootNet']['serverHosts'][env],
                                            tradingSysInfo['rootNet']['serverPorts'][env])
        Logger.info(obj2dic(connInfo))
        # 账户信息 account={acctId:acctInfo,...}
        self.account = {}
        self.acctType = {}
        # 定时任务启动标志
        self.startAble = True
        # 异步接口锁
        self.LOCK = threading.Lock()
        # 行情查询锁，不支持并发
        self.stkLock = threading.Lock()
        # 定时任务调度器
        self.scheduler = BackgroundScheduler()
        # 隔一段时间，缓存一次的委托信息
        self.order_cache = OrderCache().order_cache
        # 更新order缓存全局锁
        self.singleOrderLock = OrderCache().singleLockOfOrder
        # 多空转化
        self.LS = {'S': -1, 'B': 1}

    # 设置日志
    def __setLog(self, log_level=Logger.logLevelDebug, log_path='./log', consoleOut=False):
        # 设置日志路径
        Logger.setLogPath(log_path)
        # 设置日志级别
        Logger.setLogLevel(log_level)
        # 打开控制台输出
        Logger.setLogOutputFlag(consoleOut)

    # 账户登录
    def login(self, acctId=None, acctPwd=None, optId=None, optPwd=None, acctType='CASH'):
        try:
            optInfo = self.tradeServer.optLogin(optId, optPwd)
            printObject(optInfo, '柜员登录:')
            acctInfo = self.tradeServer.accountLogin(acctId, acctPwd)
            printObject(acctInfo, '账户登录：')
            Logger.info("{}账户登录成功".format(acctId))
            Logger.info("{}柜员登录成功".format(optInfo))
            self.account[acctId] = acctInfo
            self.acctType[acctId] = acctType
            return True
        except Exception as e:
            Logger.traceback.format_exc()
            print("登录异常 错误信息如下:\n{}".format(str(e)))

    # 缓存当前委托
    def caching_orders(self):
        df = self.getOrders()
        if not df.empty:
            for row in df.itertuples(index=True, name='pandas'):
                key = getattr(row, 'ACCOUNT') + "^" + getattr(row, 'WIND_CODE') + "^" + getattr(row, "TRADE_TYPE")
                value = int(getattr(row, 'ORDER_VOLUME'))
                current_volume = self.order_cache[key]
                if self.scheduler.running:
                    if current_volume != value:
                        Logger.warn(
                            "发现不一致的情况：本地{}的记录数量为{},查询到的数量为{}".format(getattr(row, 'WIND_CODE'), current_volume, value))
                        print(
                            "发现不一致的情况：本地{}的记录数量为{},查询到的数量为{}".format(getattr(row, 'WIND_CODE'), current_volume, value))
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
            algo_stoptime = parse(close_time)
            if not self.scheduler.running:
                self.scheduler.start()
                self.scheduler.add_job(func=self.tradeServer.disConnect, next_run_time=algo_stoptime,
                                       id='disConnect server')
        else:
            self.tradeServer.disConnect()

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

    def getFutureInfo(self, windcode):
        code, ends = windcode.split(".")
        exchId = rootNet['wind2ExchID'][ends]
        f_productId = code[:2]
        futureInfo = self._queryFutureInfo(exchId=exchId,f_productId=f_productId)
        for info in futureInfo:
            if info.stkId == code:
                return obj2dic(info)

    # 查询当前总资金金额
    def getTotalAsset(self, where=None):
        """
        # 资金账号查询
        :param where: 不为空时传一个字典{账户id:"账户id"}
        :return:一个字典,key是账号id,value为此账户的资金金额
        """
        result = {}
        if where:
            acctIds = where.get('acct')
            if isinstance(acctIds, str):
                acctIds = [acctIds]
        else:
            acctIds = self.account.keys()
        for acctid in acctIds:
            queryAccountResponse = self._get_acct_info(acctid)
            if self.acctType[acctid] == 'CASH':
                totalAsset = queryAccountResponse.usableAmt + queryAccountResponse.currentStkValue + queryAccountResponse.tradeFrozenAmt
            elif self.acctType[acctid] == 'FUTURE':
                totalAsset = queryAccountResponse.realtimeAmt
            else:
                raise Exception('accountType error! acct:{}'.format(acctid))
            result[acctid] = totalAsset
        return result

    # 查询持仓市值
    def getPositonValue(self, where=None):
        """
        :param where:
        :return:
        """
        result = {}
        if where:
            acctIds = where.get('acct')
            if isinstance(acctIds, str):
                acctIds = [acctIds]
        else:
            acctIds = self.account.keys()
        for acctid in acctIds:
            queryAccountResponse = self._get_acct_info(acctid)
            if self.acctType[acctid] == 'CASH':
                positionValue = queryAccountResponse.currentStkValue
            elif self.acctType[acctid] == 'FUTURE':
                positionValue = queryAccountResponse.marginUsedAmt
            else:
                raise Exception('accountType error! acct:{}'.format(acctid))
            result[acctid] = positionValue
        return result
    # 查询可用金额
    def getAvaCash(self, where=None):
        """
        :param where: {acctid:"账户id'}
        :return:{acctid:金额}
        """
        result = {}
        if where:
            acctIds = where.get('acct')
            if isinstance(acctIds, str):
                acctIds = [acctIds]
        else:
            acctIds = self.account.keys()
        for acctid in acctIds:
            queryAccountResponse = self._get_acct_info(acctid)
            result[acctid] = queryAccountResponse.usableAmt
        return result
    # 查询资产信息
    def getFundInfo(self, where=None):
        """
        获取账户状态，包括现金，持仓市值等信息！
        """
        result = {}
        if where:
            acctIds = where.get('acct')
            if isinstance(acctIds, str):
                acctIds = [acctIds]
        else:
            acctIds = self.account.keys()
        for acctid in acctIds:
            queryAccountResponse = self._get_acct_info(acctid)
            result[acctid] = obj2dic(queryAccountResponse)
        return result

    # 按类型获取账户信息
    def _get_acct_info(self, acctid):
        if self.acctType.get(acctid) == 'CASH':
            return self.tradeServer.queryAccountInfo(acctid)
        elif self.acctType.get(acctid) == 'FUTURE':
            return self.tradeServer.queryFutAcctInfo(acctid)
        else:
            return defaultdict(lambda : 'not support acctType')

    # 查询当前持仓
    def getPositions(self, where=None, ignore_type=True):
        """
        :param where: {acct:["120021313"],windcode:["600030.SH"],...}
        :param ignore_type: 不区分今日持仓和昨日持仓
        :return:
        """
        try:
            positions = []
            if where and where.get('acct'):
                acctIds = where['acct']
            else:
                acctIds = self.account.keys()
            for acct in acctIds:
                self._get_position_data(acct, positions)
            return BuildPositionsDF(positions, ["ACCOUNT"], where, ignore_type=ignore_type)
        except :
            Logger.error(traceback.format_exc())
    # 查询当日成交
    def getTrades(self, where={}):
        try:
            trades = defaultdict(lambda: np.array([0, 0, 0], dtype=float))
            acctIds = where.get('acct',self.account.keys())
            for acct in acctIds:
                self._get_trades_data(acct, trades)
            trades_array = []
            for k, v in trades.items():
                #  key = acctid:stkName:orderType:stkId:exchId , v:[tradeVolume,tradeAmount]
                key_list = k.split(':')
                acctid = key_list[0]
                windcode = key_list[3] + "." + rootNet['exchID2wind'][key_list[4]]
                stkName = key_list[1]
                order_type = key_list[2]
                trade_notional = v[1]
                trade_volume = v[0]
                trade_amt = v[2]
                trade_price = trade_amt/trade_volume
                # [account,windcode,name,tradeType,volume,amount,price
                trade = [[acctid]] + [windcode, stkName, order_type ,trade_volume, trade_notional, trade_price]
                trades_array.append(trade)
            return BuildTradesDF(trades_array, ['ACCOUNT'], where)
        except Exception as e:
            print(str(e))
            Logger.error(str(e) + "本次查询交易信息失败")
    # 查询委托
    def getOrders(self, where={}):
        try:
            orders = defaultdict(lambda: 0)
            acctIds = where.get('acct', self.account.keys())
            for acct in acctIds:
                self._get_orders_data(acct, orders)
            orders_array = []
            for k, v in orders.items():
                #key = returnData.acctId + '.' + orderType + '.' + returnData.stkId + '.' + returnData.exchId
                keys = k.split('.')
                acctid = keys[0]
                windcode = keys[2] + '.' + rootNet['exchID2wind'][keys[3]]
                order_type = keys[1]
                order = [[acctid]] + [windcode, order_type, v]
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

    # ------------------ --------- ---------  private func -----------------------------------------------------

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

    def _queryFutureInfo(self,exchId, f_productId):
        queryCond = QueryFutureCond()
        queryCond.exchId = exchId
        queryCond.f_productId = f_productId
        return self.tradeServer.queryFutureInfo(queryCond=queryCond)

    def _get_position_data(self, acctId, positions:list):
        queryCond = QueryPositionCond()
        queryCond.acctId = acctId
        result = self.tradeServer.queryPositionList(queryCond, maxRowNum=10000, pageNum=1, syncFlag=True)
        for returnData in result:
            wind_exch_id = rootNet['exchID2wind'].get(returnData.exchId)
            if not wind_exch_id:
                Logger.warn('not support exch_id:{}, data:{}'.format(returnData.exchId,obj2dic(returnData)))
                continue
            wind_code = returnData.stkId + '.' + wind_exch_id
            # [[账户(多级)], 万得代码, 证券名称, 持仓数量, 保证金, 合约金额, 合约方向]
            if returnData.exchId in WIndCodeType['future']:
                positionQty = returnData.todayPositionUsableQty + returnData.ydPositionUsableQty +\
                        returnData.todayOffsFrozPositionQty + returnData.ydOffsFrozPositionQty
                if positionQty == 0: continue
                # contractTimes = self.getStkInfo(wind_code).contractTimes
                row = [
                    [returnData.acctId], wind_code,
                    returnData.stkName,
                    positionQty,
                    returnData.marginUsedAmt,
                    returnData.todayContractAmt + returnData.ydContractAmt,
                    self.LS.get(returnData.bsFlag, 1)
                ]
                positions.append(row)
            elif returnData.exchId in WIndCodeType['stock']:
                row = [
                    [returnData.acctId], wind_code,
                    returnData.stkName,
                    returnData.currentQtyForAsset,
                    returnData.currentStkValue,
                    returnData.currentStkValue,
                    self.LS.get(returnData.bsFlag, 1)
                ]
                positions.append(row)

    def _get_trades_data(self, acctid, trades: dict):
        queryCond = QueryKnockCond()
        queryCond.acctId = acctid
        result = self.tradeServer.queryKnockList(queryCond, maxRowNum=10000, pageNum=1, syncFlag=True)
        for returnData in result:
            if returnData.knockQty == 0 or returnData.knockPrice == 0 : continue
            if returnData.exchId in WIndCodeType['future']:
                orderType = returnData.bsFlag + '/' + returnData.f_offSetFlag
                wind_exch_id = rootNet['exchID2wind'].get(returnData.exchId)
                wind_code = returnData.stkId + '.' + wind_exch_id
                # contractTimes = self.getStkInfo(wind_code).contractTimes
                trade = np.array([returnData.knockQty, returnData.knockAmt, returnData.knockPrice*returnData.knockQty], dtype=float)
                # acctid:stkName:orderType:stkId:exchId
                key = returnData.acctId + ':' + returnData.stkName + ':' + orderType + ':' + returnData.stkId + ':' + returnData.exchId
                trades[key] += trade

            elif returnData.exchId in WIndCodeType['stock']:
                orderType = returnData.orderType
                if orderType == '0B':
                    orderType = 'B'
                if orderType == '0S':
                    orderType = 'S'
                trade = np.array([returnData.knockQty, returnData.knockAmt, returnData.knockAmt], dtype=float)
                key = returnData.acctId + ':' + returnData.stkName + ':' + orderType + ':' + returnData.stkId + ':' + returnData.exchId
                # if returnData.tradingResultTypeDesc == u'买入成交' or returnData.tradingResultTypeDesc == u'卖出成交':
                trades[key] += trade

    def _get_orders_data(self, acctid, orders: dict, ):
        queryCond = QueryOrderCond()
        queryCond.acctId = acctid
        result = self.tradeServer.queryOrderList(queryCond, maxRowNum=10000, pageNum=1, syncFlag=True)
        if result:
            for returnData in result:
                # 将返回的字典转化为类对象
                try:
                    if returnData.validFlag != 0:
                        printObject(returnData, "委托不合法，信息如下：")
                        continue
                    contractTimes = 1
                    if returnData.exchId in WIndCodeType['future']:
                        wind_exch_id = rootNet['exchID2wind'].get(returnData.exchId)
                        wind_code = returnData.stkId + '.' + wind_exch_id
                        # contractTimes = self.getStkInfo(wind_code).contractTimes
                        orderType = returnData.bsFlag + '/' + returnData.f_offSetFlag
                    elif returnData.exchId in WIndCodeType['stock']:
                        orderType = returnData.orderType
                        if orderType == '0B':
                            orderType = 'B'
                        if orderType == '0S':
                            orderType = 'S'
                    else:
                        print('不支持的exchId:{},data:{}'.format(returnData.exchId,obj2dic(returnData)))
                        Logger.error('不支持的exchId:{},data:{}'.format(returnData.exchId,obj2dic(returnData)))
                        continue
                    key = returnData.acctId + '.' + orderType + '.' + returnData.stkId + '.' + returnData.exchId
                    orders[key] += (returnData.orderQty - returnData.withdrawQty)
                except:
                    Logger.error("解析委托信息失败：\n {}".format(obj2dic(returnData)))
                    Logger.error(traceback.format_exc())




# 将字典变为类
def obj_dic(d):
    top = type('new', (object,), d)
    seqs = tuple, list, set, frozenset
    for i, j in d.items():
        if isinstance(j, dict):
            setattr(top, i, obj_dic(j))
        elif isinstance(j, seqs):
            setattr(top, i,
                    type(j)(obj_dic(sj) if isinstance(sj, dict) else sj for sj in j))
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

import numpy as np
import pandas as pd
np.set_printoptions(suppress=True)

def _where_windcodes(where):
    windcode = None
    if isinstance(where, dict):
        windcode = where.get("windcode")
    return windcode

def BuildPositionsDF(positions_list, account_titles, where, ignore_type = True):
    """
    :param positions_list: list
        [[账户(多级)], 万得代码, 证券名称, 持仓数量, 保证金占用, 合约金额, 合约方向]
    :param account_titles: list
        账户各级的列名
    :param where: dict
        过滤条件。如果是dict类型并且存在key为windcode, 则结果集根据windcode过滤
    :return: pandas.DataFrame
        columns=[account_titles + ["WIND_CODE", "SECURITY_NAME", "POSITION", "AMOUNT", "NOTIONAL", "LS"]]
    """
    # 下面把List转换为Pandas.DataFrame对象
    columns = account_titles + ["WIND_CODE", "SECURITY_NAME", "POSITION", "AMOUNT", "NOTIONAL", "LS"]
    if not positions_list:
        return pd.DataFrame(columns=columns)
    np_position = np.array(positions_list, dtype=object)
    df = pd.DataFrame(np_position[:, 3:],
                      columns=["POSITION", "AMOUNT", "NOTIONAL", "LS"],
                      dtype=float)
    # 拆ACCOUNT
    acct_array = np.array(np_position[:, 0].tolist())
    for i in range(0, len(account_titles)):
        df[account_titles[i]] = acct_array[:, i]
    df["WIND_CODE"] = np_position[:, 1]
    df["SECURITY_NAME"] = np_position[:, 2]
    # 按照where中的万得代码过滤
    filter_windcode = _where_windcodes(where)
    if filter_windcode:
        condition = df["WIND_CODE"] == ""
        for windcode in filter_windcode:
            condition |= df["WIND_CODE"] == windcode
        df = df[condition]
    df = df.sort_index(ascending=True)
    df = df[columns]
    return df

def BuildTradesDF(trades_list, account_titles,  where):
    '''
                        [account,windcode,name,tradeType,volume,amount,price
    :param trades_list: [[账户(多级)], 万得代码, 证券名称, 交易类型 ,VOLUME, AMOUNT, PRICE]
    :param account_titles: 账户各级的列名
    :param where: 过滤条件。如果是dict类型并且存在key为windcode, 则结果集根据windcode过滤
    :return: pandas.DataFrame
    columns=[account_titles+["WIND_CODE","SECURITY_NAME", "TRADE_TYPE", "TRADE_VOLUME", "TRADE_AMOUNT", "TRADE_PRICE"]]
    '''

    np_trades = np.array(trades_list, dtype=object)
    if not np_trades.any():
        return pd.DataFrame(columns=account_titles+ ["WIND_CODE", "SECURITY_NAME", "TRADE_TYPE", "TRADE_VOLUME", "TRADE_AMOUNT", "TRADE_PRICE"])
    df = pd.DataFrame(np_trades[:, 4:],
                      columns=["TRADE_VOLUME", "TRADE_AMOUNT", "TRADE_PRICE"],
                      dtype=float)
    # 拆ACCOUNT
    acct_array = np.array(np_trades[:, 0].tolist())
    for i in range(0, len(account_titles)):
        df[account_titles[i]] = acct_array[:, i]
    df["WIND_CODE"] = np_trades[:, 1]
    df["SECURITY_NAME"] = np_trades[:, 2]
    df["TRADE_TYPE"] = np_trades[:, 3]
    # 按照where中的万得代码过滤
    filter_windcode = _where_windcodes(where)
    if filter_windcode:
        condition = df["WIND_CODE"] == ""
        for windcode in filter_windcode:
            condition |= df["WIND_CODE"] == windcode
        df = df[condition]
    # 规整列
    df = df[account_titles+
        ["WIND_CODE", "SECURITY_NAME", "TRADE_TYPE", "TRADE_VOLUME", "TRADE_AMOUNT", "TRADE_PRICE"]]
    return df


def BuildOrdersDF(order_list, account_titles, where):
    '''
    :param order_list: [[账户(多级)], 万得代码, 交易类型, VOLUME]
    :param account_titles: 账户各级的列名
    :param where: 过滤条件。如果是dict类型并且存在key为windcode, 则结果集根据windcode过滤
    :return: pandas.DataFrame
        columns=[account_titles + ["WIND_CODE", 'TRADE_TYPE', "ORDER_VOLUME"]]
    '''

    np_orders = np.array(order_list, dtype= object)
    if not np_orders.any():
        return pd.DataFrame(columns=account_titles + ["WIND_CODE", 'TRADE_TYPE', "ORDER_VOLUME"])
    df = pd.DataFrame(np_orders[:, 3],
                      columns=["ORDER_VOLUME"],
                      dtype=float)
    # 拆ACCOUNT
    acct_array = np.array(np_orders[:, 0].tolist())
    for i in range(0, len(account_titles)):
        df[account_titles[i]] = acct_array[:, i]
    df["WIND_CODE"] = np_orders[:, 1]
    df["TRADE_TYPE"] = np_orders[:, 2]
    # 按照where中的万得代码过滤
    filter_windcode = _where_windcodes(where)
    if filter_windcode:
        condition = df["WIND_CODE"] == ""
        for windcode in filter_windcode:
            condition |= df["WIND_CODE"] == windcode
        df = df[condition]
    #规整列
    df = df[account_titles + ["WIND_CODE", 'TRADE_TYPE', "ORDER_VOLUME"]]
    df = df[df.WIND_CODE != 'NONE']
    return df

def BuildOriginalOrdersDF(original_order_list, account_titles, where):
    '''
    :param original_order_list: [[账户(多级)], 万得代码, 交易类型, 证券代码, 市场类型, 委托量, 已成交量, 委托金额, 是否可撤(Y/N/F), 撤销状态(F/T),撤销KEY,委托时间,委托状态]
    :param account_titles: 账户各级的列名
    :param where: 过滤条件。如果是dict类型并且存在key为windcode, 则结果集根据windcode过滤
    :return: pandas.DataFrame
        columns=[account_titles + ["SECURITY_CODE", "MARKET_TYPE", 'TRADE_TYPE', "ORDER_VOLUME", "FILLED_VOLUME",
                              "ORDER_PRICE", "CANCELABLE", "CANCEL_KEY"]]
    '''
    if (not original_order_list):
        original_order_list.append([list(account_titles), 'windcode', 'B/S', 'security_code', 'mkt_type', 0, 0, 0.0, "Y/N/F", "cancel_key",'',''])
    np_orders = np.array(original_order_list)
    df = pd.DataFrame(np_orders[:, 5:8],
                      columns=["ORDER_VOLUME", "FILLED_VOLUME", "ORDER_PRICE"],
                      dtype=float)
    # 拆ACCOUNT
    acct_array = np.array(np_orders[:, 0].tolist())
    for i in range(0, len(account_titles)):
        df[account_titles[i]] = acct_array[:, i]

    df["WIND_CODE"] = np_orders[:, 1]
    df["TRADE_TYPE"] = np_orders[:, 2]
    df["SECURITY_CODE"] = np_orders[:, 3]
    df["MARKET_TYPE"] = np_orders[:, 4]
    df["CANCELABLE"] = np_orders[:, 8]
    df["CANCEL_KEY"] = np_orders[:, 9]
    df['INSTR_TIME'] = np_orders[:,10]
    df['ORDER_STATE'] = np_orders[:,11]




    # 按照where中的万得代码过滤
    filter_windcode = _where_windcodes(where)
    if filter_windcode:
        condition = df["WIND_CODE"] == ""
        for windcode in filter_windcode:
            condition |= df["WIND_CODE"] == windcode
        df = df[condition]

    # df = df[df['WIND_CODE'].isin(filter_windcode)]

    #规整列
    df = df[account_titles + ["WIND_CODE","SECURITY_CODE", "MARKET_TYPE", 'TRADE_TYPE', "ORDER_VOLUME", "FILLED_VOLUME",
                              "ORDER_PRICE", "CANCELABLE", "CANCEL_KEY","INSTR_TIME","ORDER_STATE"]]
    df = df[df.SECURITY_CODE != 'security_code']

    return df


def BuildOriginalOrdersDF_New(original_order_list, account_titles, where):
    '''
    :param original_order_list: [[账户(多级)], 万得代码, 交易类型, 证券代码, 市场类型, 委托量, 已成交量, 委托金额, 是否可撤(Y/N/F), 撤销状态(F/T),撤销KEY]
    :param account_titles: 账户各级的列名
    :param where: 过滤条件。如果是dict类型并且存在key为windcode, 则结果集根据windcode过滤
    :return: pandas.DataFrame
        columns=[account_titles + ["SECURITY_CODE", "MARKET_TYPE", 'TRADE_TYPE', "ORDER_VOLUME", "FILLED_VOLUME",
                              "ORDER_PRICE", "CANCELABLE", "CANCEL_KEY","remark"]]
    '''
    if (not original_order_list):
        original_order_list.append([list(account_titles), 'windcode', 'B/S', 'security_code', 'mkt_type', 0, 0, 0.0, "Y/N/F", "F/T","cancel_key","remark"])
    np_orders = np.array(original_order_list)
    df = pd.DataFrame(np_orders[:, 5:8],
                      columns=["ORDER_VOLUME", "FILLED_VOLUME", "ORDER_PRICE"],
                      dtype=float)
    # 拆ACCOUNT
    acct_array = np.array(np_orders[:, 0].tolist())
    for i in range(0, len(account_titles)):
        df[account_titles[i]] = acct_array[:, i]

    df["WIND_CODE"] = np_orders[:, 1]
    df["TRADE_TYPE"] = np_orders[:, 2]
    df["SECURITY_CODE"] = np_orders[:, 3]
    df["MARKET_TYPE"] = np_orders[:, 4]
    df["CANCELABLE"] = np_orders[:, 8]
    df['CANCEL_FLAG'] = np_orders[:,9]
    df["CANCEL_KEY"] = np_orders[:, 10]
    df["REMARK"] = np_orders[:, 11]


    # 按照where中的万得代码过滤
    filter_windcode = _where_windcodes(where)
    if filter_windcode:
        condition = df["WIND_CODE"] == ""
        for windcode in filter_windcode:
            condition |= df["WIND_CODE"] == windcode
        df = df[condition]

    # df = df[df['WIND_CODE'].isin(filter_windcode)]
    # 规整列
    df = df[account_titles + ["WIND_CODE","SECURITY_CODE", "MARKET_TYPE", 'TRADE_TYPE', "ORDER_VOLUME", "FILLED_VOLUME",
                              "ORDER_PRICE", "CANCELABLE","CANCEL_FLAG", "CANCEL_KEY","REMARK"]]
    df = df[df.SECURITY_CODE != 'security_code']
    return df
