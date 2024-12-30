#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file:catsserverapi_cwrapper.py
@time:2020/05/19
"""
import ctypes


class CCATS_CatsAPIParam(ctypes.Structure):
    _fields_ = [
        ('pcMqIp', ctypes.c_char_p),  # CATS服务端总线的IP地址
        ('mqBasePort', ctypes.c_ushort),  # CATS服务端总线的基础端口
        ('reqThreadCount', ctypes.c_int),  # 处理请求的线程数
        ('subThreadCount', ctypes.c_int),  # 处理订阅消息(Subscribed Data)的线程数
        ('serverTimeoutMs', ctypes.c_int),  # 请求超时等待时间(毫秒)
        ('autoSubAlgoInstanceUpdate', ctypes.c_bool),  # 是否自动订阅算法实例更新。若为true，则startAlgo中会自动调用subAlgoInstanceUpdate
        ('autoSubAlgoInstanceExecStat', ctypes.c_bool),  # 是否自动订阅算法执行统计。若为true，则启动算法成功后会自动调用subAlgoInstanceExecStat
    ]

    def __str__(self):
        return innerStr(self)


# /************************************************************************/
# /* Subscribed datas                                                     */
# /************************************************************************/

class CCATS_CatsOrderUpdateData(ctypes.Structure):
    _fields_ = [
        ('acctType', ctypes.c_char_p),  # 账户类型
        ('acct', ctypes.c_char_p),  # 账户名称
        ('catsAcct', ctypes.c_char_p),  # cats账户名称
        ('symbol', ctypes.c_char_p),  # 合约代码
        ('orderQty', ctypes.c_int),  # 报单总数量
        ('orderPrice', ctypes.c_char_p),  # 报单价格
        ('tradeSide', ctypes.c_char_p),  # 报单方向
        ('orderType', ctypes.c_char_p),  # 报单类型
        ('orderParam', ctypes.c_char_p),  # 报单参数
        ('orderNo', ctypes.c_char_p),  # CATS内部显示的订单编号
        ('corrType', ctypes.c_char_p),  # corrType
        ('corrID', ctypes.c_char_p),  # 内部ID; 算法单子单中，等于AlgoInstanceId
        ('filledQty', ctypes.c_int),  # 成交数量
        ('avgPrice', ctypes.c_char_p),  # 成交均价
        ('cancelQty', ctypes.c_int),  # 取消数量
        ('lastTime', ctypes.c_char_p),  # 最后更新时间  格式为 hhmmss
        ('status', ctypes.c_int),  # 报单状态 0 新单(未结)	1 部分成交(未结)	2 全成(已结)	3 部分撤单(已结)	4 全撤(已结)	5 拒单(已结)
        ('orderTime', ctypes.c_char_p),  # 委托时间  格式为hhmmss
        ('orderDate', ctypes.c_char_p),  # 委托日期  格式yyyymmdd
        ('orderCorrData', ctypes.c_char_p),  # reserved
        ('algoData1', ctypes.c_longlong),  # reserved
        ('algoData2', ctypes.c_longlong),  # reserved
        ('basketId', ctypes.c_int),  # reserved
        ('basketItemIndex', ctypes.c_int),  # reserved
        ('localTs', ctypes.c_longlong),  # 本地时间戳(ms)。用于超时老化
    ]

    def __str__(self):
        return innerStr(self)


# /************************************************************************/
# /* Request and Response parameter structures                            */
# /************************************************************************/

class CCATS_CATSLoginSvcRequest(ctypes.Structure):
    """
    const char* catsAcct;	// cats账户名
	const char* password;	// cats密码
	const char* ip;			// IP地址
	const char* macAddr;	// MAC地址
	const char* hdSerial;	// 硬盘序列号
    """
    _fields_ = [
        ('catsAcct', ctypes.c_char_p),
        ('password', ctypes.c_char_p),
        ('ip', ctypes.c_char_p),
        ('macAddr', ctypes.c_char_p),
        ('hdSerial', ctypes.c_char_p)
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSLoginSvcResponse(ctypes.Structure):
    """
    const char* errCode;
	const char* errMsg;
	const char* catsAcct;	// cats账户名
	const char* catsToken;	// 登陆成功时，服务端生成的token串。用户后续的请求
    """
    _fields_ = [
        ('errCode', ctypes.c_char_p),
        ('errMsg', ctypes.c_char_p),
        ('catsAcct', ctypes.c_char_p),
        ('catsToken', ctypes.c_char_p),
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSTradeAccountLoginSvcRequest(ctypes.Structure):
    """
    const char* catsAcct;	// cats账户名
	const char* catsToken;	// cats账户登陆成功后得到的token串
	const char* acctType;	// 资金账户类型
	const char* acct;		// 资金账户
	const char* password;	// 资金账户密码
	const char* loginParam;	// 登陆类型
	const char* ip;			// IP地址
	const char* macAddr;	// MAC地址
	const char* hdSerial;	// 硬盘序列号
    """
    _fields_ = [
        ('catsAcct', ctypes.c_char_p),
        ('catsToken', ctypes.c_char_p),
        ('acctType', ctypes.c_char_p),
        ('acct', ctypes.c_char_p),
        ('password', ctypes.c_char_p),
        ('loginParam', ctypes.c_char_p),
        ('ip', ctypes.c_char_p),
        ('macAddr', ctypes.c_char_p),
        ('hdSerial', ctypes.c_char_p),
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSTradeAccountLoginSvcResponse(ctypes.Structure):
    """
    const char* errCode;
	const char* errMsg;
	const char* acctType;
	const char* acct;
	const char* branchName;	// 分支机构名称
	const char* name;		// 客户名称
	const char* spcashStatus;
    """
    _fields_ = [
        ('errCode', ctypes.c_char_p),
        ('errMsg', ctypes.c_char_p),
        ('acctType', ctypes.c_char_p),
        ('acct', ctypes.c_char_p),
        ('branchName', ctypes.c_char_p),
        ('name', ctypes.c_char_p),
        ('spcashStatus', ctypes.c_char_p),
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSStartAlgoSvcRequest(ctypes.Structure):
    """
    	const char* catsAcct;	// cats账户名
	    const char* catsToken;	// cats账户登陆成功后得到的token串
	    const char* algoId;		// 算法类型ID，如"TWAP", "VWAP"等等
	    const char* algoParams; // 算法参数。具体参加每个算法的说明。字符串为<key>=<value>;格式
    """
    _fields_ = [
        ('catsAcct', ctypes.c_char_p),
        ('catsToken', ctypes.c_char_p),
        ('algoId', ctypes.c_char_p),
        ('algoParams', ctypes.c_char_p),
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSStartAlgoSvcResponse(ctypes.Structure):
    """
    const char* errCode;
	const char* errMsg;
	const char* algoInstanceId;	// 算法实例ID
    """
    _fields_ = [
        ('errCode', ctypes.c_char_p),
        ('errMsg', ctypes.c_char_p),
        ('algoInstanceId', ctypes.c_char_p),
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSStopAlgoSvcRequest(ctypes.Structure):
    # const char* catsAcct;	// cats账户名
    # const char* catsToken;	// cats账户登陆成功后得到的token串
    # const char* algoId;	// 算法类型ID，如"TWAP", "VWAP"等等
    # const char* algoInstanceId;	// 需要停止的算法实例ID
    _fields_ = [
        ('catsAcct', ctypes.c_char_p),
        ('catsToken', ctypes.c_char_p),
        ('algoId', ctypes.c_char_p),
        ('algoInstanceId', ctypes.c_char_p)
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSStopAlgoSvcResponse(ctypes.Structure):
    # const char* errCode;
    # const char* errMsg;

    _fields_ = [
        ('errCode', ctypes.c_char_p),
        ('errMsg', ctypes.c_char_p)
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSFund2QuerySvcRequest(ctypes.Structure):
    """struct CCATS_CATSFund2QuerySvcRequest {
        const char* catsAcct;	// cats账户名
        const char* catsToken;	// cats账户登陆成功后得到的token串
        const char* acctType;
        const char* acct;
    };"""
    _fields_ = [
        ("catsAcct", ctypes.c_char_p),
        ('catsToken', ctypes.c_char_p),
        ('acctType', ctypes.c_char_p),
        ('acct', ctypes.c_char_p)
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSFund2QuerySvcResponse(ctypes.Structure):
    """
    const char* errCode;
    const char* errMsg;
    float beginBalance;		// 期初余额
    float currentBalance;	// 当前余额
    float enabledBalance;	// 可用余额
    float fetchBalance;		// 可取金额
    const char* moneyType;	// 货币类型
    const char* fundAcct;	// 资金账户
    						/* 期货、期权相关 */
    float currMargin;		// 当前保证金总额
    float dynamicEquity;	// 动态权益
    							/* 个股期权 */
    float enableBailBalance;	// 可用保证金  --> 实时保证金
    float usedBailBalance;		// 已用保证金
    float usedPurBalance;		// 已用买入额度
    float enablePurBalace;		// 可用买入额度
    const char* direction;		//持仓多空方向：1-净;2-多头;3-空头
                                    期权持仓类别,"0":权利方|"1":义务方|"2":备兑方
    """
    _fields_ = [
        ('errCode', ctypes.c_char_p),
        ('errMsg', ctypes.c_char_p),
        ('beginBalance', ctypes.c_float),
        ('currentBalance', ctypes.c_float),
        ('enabledBalance', ctypes.c_float),
        ('fetchBalance', ctypes.c_float),
        ('moneyType', ctypes.c_char_p),
        ('fundAcct', ctypes.c_char_p),
        ('currMargin', ctypes.c_float),
        ('dynamicEquity', ctypes.c_float),
        ('enableBailBalance', ctypes.c_float),
        ('usedBailBalance', ctypes.c_float),
        ('usedPurBalance', ctypes.c_float),
        ('enablePurBalace', ctypes.c_float),
        ('direction', ctypes.c_char_p)
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSPosition2Data(ctypes.Structure):
    _fields_ = [
        ('symbol', ctypes.c_char_p),
        ('currentQty', ctypes.c_int),
        ('enabledQty', ctypes.c_int),
        ('costPrice', ctypes.c_float),
        ('direction', ctypes.c_char_p),
        ('hedgeFlag', ctypes.c_char_p),
        ('stockAcct', ctypes.c_char_p)
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSPosition2QuerySvcRequest(ctypes.Structure):
    # const char* catsAcct;	// cats账户名
    # const char* catsToken;	// cats账户登陆成功后得到的token串
    # const char* acctType;
    # const char* acct;
    # int maxRowNum;	// 每页数据条数
    # int pageNum;	// 页码

    _fields_ = [
        ('catsAcct', ctypes.c_char_p),
        ('catsToken', ctypes.c_char_p),
        ('acctType', ctypes.c_char_p),
        ('acct', ctypes.c_char_p),
        ('maxRowNum', ctypes.c_int),
        ('pageNum', ctypes.c_char_p)
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSSubmitOrderSvcRequest(ctypes.Structure):
    """
        tradeSide: 普通:
                     1	买入 或 担保品买入
                     2	卖出 或 担保品卖出
                    ETF
                     F	ETF申购
                     G	ETF赎回
                    融资融券:
                     A	融资买入
                     B	融券卖出
                     C	买券还券
                     D	卖券还款
                     E	先买券还券，后担保品买入
                    期货/期权:
                     FA  开多仓（开仓买入）
                     FB  开空仓（开仓卖出）
                     FC  平空仓（平仓买入）
                     FD  平多仓（平仓卖出）

        orderType : 0 代表限价

    """
    _fields_ = [
        ('catsAcct', ctypes.c_char_p),
        ('catsToken', ctypes.c_char_p),
        ('acctType', ctypes.c_char_p),
        ('acct', ctypes.c_char_p),
        ('symbol', ctypes.c_char_p),
        ('tradeSide', ctypes.c_char_p),
        ('orderType', ctypes.c_char_p),
        ('priceValue', ctypes.c_char_p),
        ('qty', ctypes.c_int),
        ('orderParam', ctypes.c_char_p),
    ]


class CCATS_CATSSubmitOrderSvcResponse(ctypes.Structure):
    _fields_ = [
        ('errCode', ctypes.c_char_p),
        ('errMsg', ctypes.c_char_p),
        ('orderNo', ctypes.c_char_p)
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSPosition2QuerySvcResponse(ctypes.Structure):
    _fields_ = [
        ('errCode', ctypes.c_char_p),
        ('errMsg', ctypes.c_char_p),
        ('positionsLen', ctypes.c_int),
        ('positions', ctypes.POINTER(CCATS_CATSPosition2Data))
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSSubOrderUpdateSvcRequest(ctypes.Structure):
    # const char* catsAcct;	// cats账户名
    # const char* catsToken;	// cats账户登陆成功后得到的token串
    # const char* acctType;
    # const char* acct;
    # bool notPubHist;

    _fields_ = [
        ('catsAcct', ctypes.c_char_p),
        ('catsToken', ctypes.c_char_p),
        ('acctType', ctypes.c_char_p),
        ('acct', ctypes.c_char_p),
        ('notPubHist', ctypes.c_bool)
    ]

    def __str__(self):
        return innerStr(self)


class CCATS_CATSSubOrderUpdateSvcResponse(ctypes.Structure):
    _fields_ = [
        ('errCode', ctypes.c_char_p),
        ('errMsg', ctypes.c_char_p)

    ]

    def __str__(self):
        return innerStr(self)


# ------------------------------------------utils-----------------------------------------------------

def innerStr(cls):
    s = ""
    for attrs in cls._fields_:
        if attrs[0] in ['errMsg', 'name']:
            value = getattr(cls, attrs[0]).decode('gb2312')
        elif attrs[0] == 'positions':
            # for i in range(self.positionsLen):
            #     print(self.positions[i])
            value = ''
        else:
            if isinstance(getattr(cls, attrs[0]), bytes):
                value = getattr(cls, attrs[0]).decode('gb2312')
            else:
                value = getattr(cls, attrs[0])
        s += attrs[0] + ":" + str(value) + ","
    return s
