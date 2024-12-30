"""
@author:ai
@file:CATSServer.py
@time:2020/05/19
"""
import time
import os, sys
path = os.getcwd()
sys.path.append(path)
from ctypes import *
from tradingSystem.CATS.catsserverapi.include.catsserverapi_cwrapper import *
from tradingSystem.CATS.catsserverapi.models.Account import Account, LocalOsInfo
from tradingSystem.CATS.catsserverapi.catsConfig import mqBasePort, MQ_SERVER_IP
from threading import Event

#################################### global variable ###########################################
# 需要增加引用计数的函数的存放位置
global_func_ref = set()

#################################### global variable ###########################################

def CALLBACK_ONCE(a_func: callable):
    def wrap_func(*args, **kwargs):
        a_func(*args, **kwargs)
        global global_func_ref
        global_func_ref.remove(wrap_func)

    global global_func_ref
    global_func_ref.add(wrap_func)
    return wrap_func


def CALLBACK_PERSIST(a_func: callable):
    '''
    the a_func will be hold forever
    '''

    def wrap_func_p(*args, **kwargs):
        a_func(*args, **kwargs)

    global global_func_ref
    global_func_ref.add(wrap_func_p)
    return wrap_func_p


class CATSServer():
    """
        catsserverapi python版
    """

    def __init__(self, env='test', so_path='libs', acct_info=None, local_info=None, logger=None):
        self.env = env
        self.Logger = logger
        self.reqThreadCount = 1
        self.subThreadCount = 1
        # 超时时长设定 单位ms
        self.serverTimeoutMs = 10000
        # 账户信息
        self.acctInfo = acct_info
        # 本机信息(ip,mac,硬盘序列号
        self.localInfo = local_info
        ctypes.CDLL('libzmq.so', ctypes.RTLD_GLOBAL)
        ctypes.CDLL('libtbb.so', ctypes.RTLD_GLOBAL)
        ctypes.CDLL('libuuid.so', ctypes.RTLD_GLOBAL)
        self.catslib = ctypes.cdll.LoadLibrary(so_path + '/libcats_serverapi.so')
        self.void_p = ctypes.c_void_p(None)
        # cats 账户登录锁
        self.catsLogined = Event()
        # cats 账户是否登录成功
        self.catsLoginedSucessed = False
        # 交易账户登录锁
        self.catsTradeLogined = Event()
        # 交易账户登录是否成功
        self.catsTradeLoginedSucessed = False
        # 获取资金函数锁
        self.queryFundLock = Event()
        # 获取持仓函数锁
        self.queryPositionLock = Event()
        # 启动一个算法实例函数锁
        self.startAlgoLock = Event()
        # 停止一个算法实例函数锁
        self.stopAlgoLock = Event()
        # 直接发单函数锁
        self.submitOrderLock = Event()
        # 登录后从cats服务器获取的token,大部分交互都需要此值
        self.catsToken = ''
        # 持仓
        self.Positions = dict()
        # 账户信息
        self.catsFundsInfo = None
        # 成交信息
        self.trades = []
        # 增加引用计数,防止垃圾回收把回调函数回收掉
        self.ref_pool = []
        self.startedInstanceIds = []

    def initService(self):
        """
        初始化
        :return:
        """
        api_param = CCATS_CatsAPIParam()
        api_param.pcMqIp = MQ_SERVER_IP[self.env].encode()
        api_param.mqBasePort = mqBasePort[self.env]
        api_param.reqThreadCount = self.reqThreadCount
        api_param.subThreadCount = self.subThreadCount
        api_param.serverTimeoutMs = self.serverTimeoutMs
        api_param.autoSubAlgoInstanceUpdate = ctypes.c_bool(False)
        api_param.autoSubAlgoInstanceExecStat = ctypes.c_bool(False)
        self.catslib.CCATS_InitService.argtypes = [CCATS_CatsAPIParam]
        self.catslib.CCATS_InitService(api_param)
        # self.catsLogined = False
        # self.catsTradeLogined = False
        print('catsService init ok')

    def catsLogin(self):
        """
        cats账户登录
        :return:
        """
        self.catsLogined.clear()
        self.catsLoginedSucessed = False
        self._catsLogin()
        # while not self.catsLogined:
        #     time.sleep(0.1)
        self.catsLogined.wait()

    def catsTradeAcctLogin(self):
        """
        cats资金账户登录
        :return:
        """
        self.catsTradeLogined.clear()
        self.catsTradeLoginedSucessed = False
        self._catsTradeAcctLogin()
        # flag = "."
        # while not self.catsTradeLogined:
        #     # print(flag)
        #     # flag+="."
        #     time.sleep(0.1)

        self.catsTradeLogined.wait()

    def catsGetFundInfo(self):
        """
        获取资金信息
        :return:
        """
        self._catsFundInfo()
        self.queryFundLock.clear()
        self.queryFundLock.wait()

    def catsGetPosition(self):
        """
        获取持仓信息
        :return:
        """
        self._catsPositionQuery()
        self.queryPositionLock.clear()
        self.queryPositionLock.wait()

    def catsStartAlgo(self, algoId='AITWAP3', startParams=''):
        """
        启动算法
        :param algoId:
        :param startParams:
        :return:
        """
        self.startAlgoLock.clear()
        self._catsStartAlgo(algoId=algoId, startParams=startParams)
        self.startAlgoLock.wait()

    def catsStopAlgo(self, algoType="AITWAP3", algoInstanceId=""):
        """
        停止算法
        :param algoType:
        :param algoInstanceId:
        :return:
        """
        self.stopAlgoLock.clear()
        self._catsStopAlgo(algoId=algoType, algoInstanceId=algoInstanceId)
        self.stopAlgoLock.wait()

    def catsSubmitOrders(self,order):
        """
        直接下单(dma)
        :return:
        """
        self.submitOrderLock.clear()
        self._submitOrder()
        self.submitOrderLock.wait()

    # ------------------------------------subscribed --------------------------------------

    def subOrderUpdate(self):
        self._subOrderUpdate()
        pass

    # --------------------------------private -------------------------------------------------

    def _catsLogin(self):
        """
        登录cats账号
        :return:
        """
        loginLocalInfo = CCATS_CATSLoginSvcRequest()
        loginLocalInfo.catsAcct = self.acctInfo.catsAcct.encode()
        loginLocalInfo.password = self.acctInfo.catsAcctPwd.encode()
        loginLocalInfo.ip = self.localInfo.localIp.encode()
        loginLocalInfo.macAddr = self.localInfo.macAddr.encode()
        loginLocalInfo.hdSerial = self.localInfo.hdSerial.encode()
        return self.catslib.CCATS_CatsLogin(loginLocalInfo, self.onCatsLoginResponse(), self.void_p)

    def _catsTradeAcctLogin(self):
        """
        资金账号登录
        :return:
        """
        tradeAcctInfo = CCATS_CATSTradeAccountLoginSvcRequest()
        tradeAcctInfo.catsAcct = self.acctInfo.catsAcct.encode()
        tradeAcctInfo.catsToken = self.catsToken.encode()
        tradeAcctInfo.acctType = self.acctInfo.tradeAcctType.encode()
        tradeAcctInfo.acct = self.acctInfo.tradeAcct.encode()
        tradeAcctInfo.password = self.acctInfo.tradeAcctPwd.encode()
        tradeAcctInfo.loginParam = ''.encode()
        tradeAcctInfo.ip = self.localInfo.localIp.encode()
        tradeAcctInfo.macAddr = self.localInfo.macAddr.encode()
        tradeAcctInfo.hdSerial = self.localInfo.hdSerial.encode()
        return self.catslib.CCATS_TradeAcctLogin(tradeAcctInfo, self.onTradeLoginResponse(), self.void_p)

    def _catsStartAlgo(self, algoId='AITWAP3', startParams=''):
        """
        启动算法
        :param algoId:
        :param startParams:
        :return:
        """
        startAlgoReq = CCATS_CATSStartAlgoSvcRequest()
        startAlgoReq.catsAcct = self.acctInfo.catsAcct.encode()
        startAlgoReq.catsToken = self.catsToken.encode()
        startAlgoReq.algoId = algoId.encode()
        startAlgoReq.algoParams = startParams.encode()
        print("send algo {}:{}".format(algoId, startAlgoReq.algoParams))
        return self.catslib.CCATS_StartAlgo(startAlgoReq, self.onStartAlgo(), self.void_p)

    def _catsStopAlgo(self, algoId='AITWAP3', algoInstanceId=""):
        """
        停止算法
        :param algoId:
        :param algoInstanceId:
        :return:
        """
        stopAlgoReq = CCATS_CATSStopAlgoSvcRequest()
        stopAlgoReq.catsAcct = self.acctInfo.catsAcct.encode()
        stopAlgoReq.catsToken = self.catsToken.encode()
        stopAlgoReq.algoId = algoId.encode()
        stopAlgoReq.algoInstanceId = algoInstanceId.encode()
        print("stop algo {}:{}".format(algoId, algoInstanceId))
        return self.catslib.CCATS_StopAlgo(stopAlgoReq, self.onStopAlgo(), self.void_p)

    def _catsFundInfo(self):
        """
        cats 资金账户资金信息查询
        :return:
        """
        catsFundReq = CCATS_CATSFund2QuerySvcRequest()
        catsFundReq.catsAcct = self.acctInfo.catsAcct.encode()
        catsFundReq.catsToken = self.catsToken.encode()
        catsFundReq.acctType = self.acctInfo.tradeAcctType.encode()
        catsFundReq.acct = self.acctInfo.tradeAcct.encode()
        return self.catslib.CCATS_Fund2Query(catsFundReq, self.onCatsFundQuery(), self.void_p)

    def _catsPositionQuery(self, maxRowNum=10000, pageNum=0):
        """
        查询持仓
        :return:
        """
        queryPositionRequest = CCATS_CATSPosition2QuerySvcRequest()
        queryPositionRequest.catsAcct = self.acctInfo.catsAcct.encode()
        queryPositionRequest.catsToken = self.catsToken.encode()
        queryPositionRequest.acctType = self.acctInfo.tradeAcctType.encode()
        queryPositionRequest.acct = self.acctInfo.tradeAcct.encode()
        queryPositionRequest.maxRowNum = maxRowNum
        queryPositionRequest.pageNum = pageNum
        return self.catslib.CCATS_Position2Query(queryPositionRequest, self.onCatsPositionQuery(), self.void_p)

    def _submitOrder(self):
        """
        直接下单
        :return:
        """
        submitOrderRequest = CCATS_CATSSubmitOrderSvcRequest()


    def _subOrderUpdate(self):
        flag = self._setOrderUpdateCallBack()
        if flag == 0:
            orderUpdateRequest = CCATS_CATSSubOrderUpdateSvcRequest()
            orderUpdateRequest.catsAcct = self.acctInfo.catsAcct.encode()
            orderUpdateRequest.catsToken = self.catsToken.encode()
            orderUpdateRequest.acctType = self.acctInfo.tradeAcctType.encode()
            orderUpdateRequest.acct = self.acctInfo.tradeAcct.encode()
            orderUpdateRequest.notPubHist = c_bool(False)
            return self.catslib.CCATS_SubOrderUpdate(orderUpdateRequest, self.onOrderUpdateSubscribed(), self.void_p)
        else:
            print("set orderUpdateCallback failed!")

    def _setOrderUpdateCallBack(self):
        return self.catslib.CCATS_SetOrderUpdateHandler(self.onSetUpdateCallback(), self.void_p)

    def _formatPosition(self, positionLen, positions):
        """
        const char* symbol;
        int currentQty;		// 当前数量
        int enabledQty;		// 可用数量
        float costPrice;	// 成本价
                            /* 期货相关 */
        const char* direction;	//持仓多空方向：1-净;2-多头;3-空头  期权持仓类别,"0":权利方|"1":义务方|"2":备兑方
        const char* hedgeFlag;	//投机套保标志：1-投机;2-套利;3-套保
        const char* stockAcct;	//股东代码
        :param positions:
        :return:
        """
        result = {}
        if positions:
            for i in range(positionLen):
                result[positions[i].symbol.decode('gb2312')] = {
                    'currentQty': positions[i].currentQty,
                    'enabledQty': positions[i].enabledQty,
                    'costPrice': positions[i].costPrice,
                    'direction': positions[i].direction.decode('gb2312'),
                    'hedgeFlag': positions[i].hedgeFlag.decode('gb2312'),
                    'stockAcct': positions[i].stockAcct.decode('gb2312')
                }
        return result

    def _formatTrades(self, trade):
        print('trade info:{}'.format(trade))
        return trade

    #   ---------------------------callback----------------------------------------------
    def onCatsLoginResponse(self):
        """
        cats账号登录回调函数
        :return:
        """
        callbackfunc = CFUNCTYPE(None, CCATS_CATSLoginSvcResponse, c_void_p)

        @CALLBACK_ONCE
        def dealCatsLoginResponse(response, cbArg):
            print("cats login response:", response)
            if response.errCode == b'0':
                print("cats login sucessed!")
                print('catsToken:', response.catsToken.decode())
                catsToken = str(response.catsToken.decode())
                self.catsToken = catsToken
                self.catsLoginedSucessed = True
                self.catsLogined.set()
            else:
                print('cats login ERROR:{}:{}'.format(response.errCode,
                                                      response.errMsg.decode('gb2312')))
                self.catsLogined.set()
                raise Exception("cats login error!")

        return callbackfunc(dealCatsLoginResponse)

    def onTradeLoginResponse(self):
        """
        资金账号登录回调函数
        :return:
        """
        callbackfunc = CFUNCTYPE(None, CCATS_CATSTradeAccountLoginSvcResponse, c_void_p)

        @CALLBACK_ONCE
        def dealTradeLoginResponse(tradeAcctLoginResp, cbArg):
            print('cats tradeAccount login response', tradeAcctLoginResp)
            if tradeAcctLoginResp.errCode == b'0':
                print('cats tradeAccount login sucessed!')
                self.catsTradeLoginedSucessed = True
                self.catsTradeLogined.set()
            else:
                print('cats tradeAccount login ERROR:{}:{}'.format(tradeAcctLoginResp.errCode,
                                                                   tradeAcctLoginResp.errMsg.decode(
                                                                       'gb2312')))
                # sys.exit(1)
                self.catsTradeLogined.set()
                raise Exception("cats tradeAccount login error!")

        return callbackfunc(dealTradeLoginResponse)

    def onStartAlgo(self):
        """
        启动算法回调函数
        :return:
        """
        callbackfunc = CFUNCTYPE(None, CCATS_CATSStartAlgoSvcResponse, c_void_p)

        @CALLBACK_ONCE
        def dealStartResponse(response, cbArg):
            print('cats startAlgo response', response)
            if response.errCode == b'0':
                print('start algo instance sucessed!,instanceid:{}'.format(response.algoInstanceId.decode()))
                self.startedInstanceIds.append(response.algoInstanceId.decode())
            else:
                self.startAlgoLock.set()
                raise Exception('start algo instance error:{}:{}'.format(response.errCode,
                                                                         response.errMsg.decode('gb2312')))
            self.startAlgoLock.set()

        return callbackfunc(dealStartResponse)

    def onStopAlgo(self):
        """
        停止算法实例的回调函数
        :return:
        """
        callbackfunc = CFUNCTYPE(None, CCATS_CATSStopAlgoSvcResponse, c_void_p)

        @CALLBACK_ONCE
        def dealStopAlgoResponse(response, cbArg):
            print("cats stopAlgo response {}".format(response))
            if response.errCode == b'0':
                print('stop AlgoInstance sucessed')

            else:
                self.stopAlgoLock.set()
                print('stop AlgoInstance error:{}:{}'.format(response.errCode,
                                                                       response.errMsg.decode('gb2312')))
            self.stopAlgoLock.set()

        return callbackfunc(dealStopAlgoResponse)

    def onCatsFundQuery(self):
        """
        查询资金账户资金信息的回调函数
        :return:
        """
        callbackfunc = CFUNCTYPE(None, CCATS_CATSFund2QuerySvcResponse, c_void_p)

        @CALLBACK_ONCE
        def dealFundQueryResponse(response, cbArg):
            print('cats fundQuery response', response)
            if response.errCode == b'0':
                print('get fund info sucessed')
                self.catsFundsInfo = response
                pass

            else:
                self.queryFundLock.set()
                raise Exception('query fundInfo error:{}:{}'.format(response.errCode,
                                                                    response.errMsg.decode('gb2312')))
            self.queryFundLock.set()

        return callbackfunc(dealFundQueryResponse)

    def onCatsPositionQuery(self):
        """
        查询持仓信息回调函数
        :return:
        """
        callbackfunc = CFUNCTYPE(None, CCATS_CATSPosition2QuerySvcResponse, c_void_p)

        @CALLBACK_ONCE
        def dealPositionQueryResponse(response, cbArg):
            print("cats PositionQuery response", response)
            if response.errCode == b'0':
                print('get positions sucessed')
                self.Positions = self._formatPosition(response.positionsLen, response.positions)
            else:
                self.queryPositionLock.set()
                raise Exception('query Position error:{},{}'.format(response.errCode,
                                                                    response.errMsg.decode('gb2312')))
            self.queryPositionLock.set()

        return callbackfunc(dealPositionQueryResponse)

    def onSetUpdateCallback(self):
        """
        设置回调函数的回调函数
        :return:
        """
        callbackfunc = CFUNCTYPE(None, CCATS_CatsOrderUpdateData, c_void_p)

        @CALLBACK_PERSIST
        def dealOrderUpdateData(response, cbArg):
            print("cats orderUpdateDate response", response)
            print('get OrderUpdateData sucessed')
            self.trades.append(self._formatTrades(response))
        func = callbackfunc(dealOrderUpdateData)
        self.ref_pool.append(func)
        return func

    def onOrderUpdateSubscribed(self):
        """
        订阅成交的回调函数
        :return:
        """
        callbackfunc = CFUNCTYPE(None, CCATS_CATSSubOrderUpdateSvcResponse, c_void_p)

        @CALLBACK_ONCE
        def dealOrderUpdateData(response, cbArg):
            print("cats orderUpdateSubs response", response)
            if response.errCode == b'0':
                print('get OrderUpdateSubs sucessed')
            else:
                raise Exception('query OrderUpdateSubs error:{},{}'.format(response.errCode,
                                                                           response.errMsg.decode('gb2312')))

        return callbackfunc(dealOrderUpdateData)


if __name__ == '__main__':
    account = Account()
    localInfo = LocalOsInfo()
    cs = CATSServer(acct_info=account, local_info=localInfo)
    cs.initService()
    cs.catsLogin()
    cs.catsTradeAcctLogin()
    # cs.catsGetFundInfo()
    # # algoParams = AlgoParams(acctType=cs.acctInfo.tradeAcctType, account=cs.acctInfo.tradeAcct, symbol='300394.SZ',
    # #                         tradeSide='2', targetVol='475900', beginTime='95300', endTime='150000').getCatsParams()
    # # cs.catsStartAlgo(startParams=str(algoParams))
    # # algoParams = AlgoParams(acctType=cs.acctInfo.tradeAcctType, account=cs.acctInfo.tradeAcct, symbol='000002.SZ',
    # #                         tradeSide='1', targetVol='50000', beginTime='95300', endTime='150000').getCatsParams()
    # # cs.catsStartAlgo(startParams=str(algoParams))
    # cs.catsGetPosition()
    # pprint(cs.Positions)

    cs.subOrderUpdate()
    # cs.catsStopAlgo(algoInstanceId=cs.startedInstanceIds[0])

    time.sleep(50)
