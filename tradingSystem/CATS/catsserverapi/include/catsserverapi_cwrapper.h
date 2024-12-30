#ifndef __CATS_SERVER_API_CWRAPPER_H__
#define __CATS_SERVER_API_CWRAPPER_H__


#if defined(__cplusplus) || defined(c_plusplus)
extern "C"
{
#endif

struct CCATS_CatsAPIParam {
	const char* pcMqIp = NULL;			// CATS服务端总线的IP地址
	unsigned short mqBasePort = 45678;	// CATS服务端总线的基础端口
	int reqThreadCount = 1;				// 处理请求的线程数
	int subThreadCount = 1;				// 处理订阅消息(Subscribed Data)的线程数
	int serverTimeoutMs = 10000;		// 请求超时等待时间(毫秒)

	bool autoSubAlgoInstanceUpdate = true;	// 是否自动订阅算法实例更新。若为true，则startAlgo中会自动调用subAlgoInstanceUpdate
	bool autoSubAlgoInstanceExecStat = true;  // 是否自动订阅算法执行统计。若为true，则启动算法成功后会自动调用subAlgoInstanceExecStat
};


/************************************************************************/
/* Subscribed datas                                                     */
/************************************************************************/
struct CCATS_CatsOrderUpdateData {
	const char* acctType;// 账户类型
	const char* acct;    // 账户名称
	const char* catsAcct; // cats账户名称
	const char* symbol;  // 合约代码
	int orderQty; // 报单总数量
	const char* orderPrice;  // 报单价格
	const char* tradeSide; // 报单方向
	const char* orderType;  // 报单类型
	const char* orderParam;  // 报单参数
	const char* orderNo;  // CATS内部显示的订单编号

	const char* corrType; // corrType
	const char* corrID;   // 内部ID; 算法单子单中，等于AlgoInstanceId

	int filledQty;  // 成交数量
	const char* avgPrice;  // 成交均价
	int cancelQty; // 取消数量

	const char* lastTime; //最后更新时间  格式为 hhmmss

						  /*status 参数说明
						  0 新单(未结)
						  1 部分成交(未结)
						  2 全成(已结)
						  3 部分撤单(已结)
						  4 全撤(已结)
						  5 拒单(已结)
						  */
	int status;  // 报单状态

	const char* orderTime;  // 委托时间  格式为hhmmss
	const char* orderDate;  // 委托日期  格式yyyymmdd
	const char* text;		// 扩展信息。目前包括拒单原因

	const char* orderCorrData;  // 算法母单的startAlgo请求中带的orderCorrData
	long long algoData1 = 0;
	long long algoData2 = 0;

	int basketId = 0;			 // 使用extStartAlgoBasket启动算法篮子的篮子ID
	int basketItemIndex = 0;

	long long localTs;			// 本地时间戳(ms)。用于超时老化
};


/************************************************************************/
/* Request and Response parameter structures                            */
/************************************************************************/
struct CCATS_CATSLoginSvcRequest {
	const char* catsAcct;	// cats账户名
	const char* password;	// cats密码
	const char* ip;			// IP地址
	const char* macAddr;	// MAC地址
	const char* hdSerial;	// 硬盘序列号
};

struct CCATS_CATSLoginSvcResponse {
	const char* errCode;
	const char* errMsg;
	const char* catsAcct;	// cats账户名
	const char* catsToken;	// 登陆成功时，服务端生成的token串。用户后续的请求
};


struct CCATS_CATSTradeAccountLoginSvcRequest {
	const char* catsAcct;	// cats账户名
	const char* catsToken;	// cats账户登陆成功后得到的token串
	const char* acctType;	// 资金账户类型
	const char* acct;		// 资金账户
	const char* password;	// 资金账户密码
	const char* loginParam;	// 登陆类型
	const char* ip;			// IP地址
	const char* macAddr;	// MAC地址
	const char* hdSerial;	// 硬盘序列号
};

struct CCATS_CATSTradeAccountLoginSvcResponse {
	const char* errCode;
	const char* errMsg;
	const char* acctType;
	const char* acct;
	const char* branchName;	// 分支机构名称
	const char* name;		// 客户名称
	const char* spcashStatus;
};

struct CCATS_CATSSubmitOrderSvcRequest {
	const char* catsAcct;	// cats账户名
	const char* catsToken;	// cats账户登陆成功后得到的token串
	const char* acctType;	// 资金账户类型
	const char* acct;		// 资金账户
	const char* symbol;		// 标的代码，如 600030.SH
	const char* tradeSide;/*	普通:
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
								 */
	const char* orderType; /* 上海 股票、信用
								  0	限价单
								  U	市价单（最优五档即时成交剩余撤销）
								  R	市价单（最优五档即时成交剩余转限价）
							  深圳 股票、信用
								  0	限价单
								  U	市价单（最优五档即时成交剩余撤销）
								  S	市价单（本方最优价格）
								  T	市价单（即时成交剩余撤销）
								  Q	市价单（对手方最优价格）
								  V	市价单（全额成交或撤单）
							  */
	const char* priceValue;	// 委托价格
	int qty;			// 委托量
	const char* orderParam;	// 参考上面的ORDER_PARAM_xxx系列宏定义。一般A股交易可传""
};

struct CCATS_CATSSubmitOrderSvcResponse {
	const char* errCode;
	const char* errMsg;
	const char* orderNo;	// 订单ID
};


struct CCATS_CATSStartAlgoSvcRequest {
	const char* catsAcct;	// cats账户名
	const char* catsToken;	// cats账户登陆成功后得到的token串
	const char* algoId;		// 算法类型ID，如"TWAP", "VWAP"等等
	const char* algoParams; // 算法参数。具体参加每个算法的说明。字符串为<key>=<value>;格式
};

struct CCATS_CATSStartAlgoSvcResponse {
	const char* errCode;
	const char* errMsg;
	const char* algoInstanceId;	// 算法实例ID
};

struct CCATS_CATSStopAlgoSvcRequest {
	const char* catsAcct;	// cats账户名
	const char* catsToken;	// cats账户登陆成功后得到的token串
	const char* algoId;	// 算法类型ID，如"TWAP", "VWAP"等等
	const char* algoInstanceId;	// 需要停止的算法实例ID
};

struct CCATS_CATSStopAlgoSvcResponse {
	const char* errCode;
	const char* errMsg;
};

struct CCATS_CATSFund2QuerySvcRequest {
	const char* catsAcct;	// cats账户名
	const char* catsToken;	// cats账户登陆成功后得到的token串
	const char* acctType;
	const char* acct;
};

struct CCATS_CATSFund2QuerySvcResponse {
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
	const char* direction;		//持仓多空方向：1-净;2-多头;3-空头  期权持仓类别,"0":权利方|"1":义务方|"2":备兑方
};

struct CCATS_CATSPosition2Data {
	const char* symbol;
	int currentQty;		// 当前数量
	int enabledQty;		// 可用数量	
	float costPrice;	// 成本价

						/* 期货相关 */
	const char* direction;	//持仓多空方向：1-净;2-多头;3-空头  期权持仓类别,"0":权利方|"1":义务方|"2":备兑方
	const char* hedgeFlag;	//投机套保标志：1-投机;2-套利;3-套保
	const char* stockAcct;	//股东代码
};

struct CCATS_CATSPosition2QuerySvcRequest {
	const char* catsAcct;	// cats账户名
	const char* catsToken;	// cats账户登陆成功后得到的token串
	const char* acctType;
	const char* acct;
	int maxRowNum;	// 每页数据条数
	int pageNum;	// 页码
};

struct CCATS_CATSPosition2QuerySvcResponse {
	const char* errCode;
	const char* errMsg;
	int positionsLen; /* positions数组长度 */
	CCATS_CATSPosition2Data* positions; /* 持仓数据数组首地址 */
};


struct CCATS_CATSSubOrderUpdateSvcRequest {
	const char* catsAcct;	// cats账户名
	const char* catsToken;	// cats账户登陆成功后得到的token串
	const char* acctType;
	const char* acct;
	bool notPubHist;
};

struct CCATS_CATSSubOrderUpdateSvcResponse {
	const char* errCode;
	const char* errMsg;
};


/************************************************************************/
/* Callbacks                                                            */
/************************************************************************/
typedef void(*CCATS_PFCatsLoginRespHandler)(CCATS_CATSLoginSvcResponse resp, void* cbArg);
typedef void(*CCATS_PFCatsTradeAccountLoginRespHandler)(CCATS_CATSTradeAccountLoginSvcResponse resp, void* cbArg);
typedef void(*CCATS_PFCatsSubmitOrderRespHandler)(CCATS_CATSSubmitOrderSvcResponse resp, void* cbArg);
typedef void(*CCATS_PFCatsStartAlgoRespHandler)(CCATS_CATSStartAlgoSvcResponse resp, void* cbArg);
typedef void(*CCATS_PFCatsStopAlgoRespHandler)(CCATS_CATSStopAlgoSvcResponse resp, void* cbArg);
typedef void(*CCATS_PFCatsFund2QueryRespHandler)(CCATS_CATSFund2QuerySvcResponse resp, void* cbArg);
typedef void(*CCATS_PFCatsPosition2QueryRespHandler)(CCATS_CATSPosition2QuerySvcResponse resp, void* cbArg);
typedef void(*CCATS_PFCatsSubOrderUpdateRespHandler)(CCATS_CATSSubOrderUpdateSvcResponse resp, void* cbArg);

/************************************************************************/
/* Handlers of subscribed data									        */
/************************************************************************/
typedef void(*CCATS_PFCatsReceivedOrderUpdateHandler)(CCATS_CatsOrderUpdateData orderUpdate, void* cbArg);

/************************************************************************/
/* Service Functions                                                    */
/************************************************************************/
/* 初始化 */
void CCATS_InitService(CCATS_CatsAPIParam catsParams);

/* CATS账号登录 */
int CCATS_CatsLogin(CCATS_CATSLoginSvcRequest c_req, CCATS_PFCatsLoginRespHandler c_respHandler, void* cbArg);

/* 资金账号登录 */
int CCATS_TradeAcctLogin(CCATS_CATSTradeAccountLoginSvcRequest c_req, CCATS_PFCatsTradeAccountLoginRespHandler c_respHandler, void* cbArg);

/* 直接下单 */
int CCATS_SubmitOrder(CCATS_CATSSubmitOrderSvcRequest c_req, CCATS_PFCatsSubmitOrderRespHandler c_respHandler, void* cbArg);

/* 启动算法单 */
int CCATS_StartAlgo(CCATS_CATSStartAlgoSvcRequest c_req, CCATS_PFCatsStartAlgoRespHandler c_respHandler, void* cbArg);

/* 启动算法单 */
int CCATS_StopAlgo(CCATS_CATSStopAlgoSvcRequest c_req, CCATS_PFCatsStopAlgoRespHandler c_respHandler, void* cbArg);

/* 查询账户资金 */
int CCATS_Fund2Query(CCATS_CATSFund2QuerySvcRequest c_req, CCATS_PFCatsFund2QueryRespHandler c_respHandler, void* cbArg);

/* 查询持仓资金 */
int CCATS_Position2Query(CCATS_CATSPosition2QuerySvcRequest c_req, CCATS_PFCatsPosition2QueryRespHandler c_respHandler, void* cbArg);

/* 订阅OrderUpdate */
int CCATS_SubOrderUpdate(CCATS_CATSSubOrderUpdateSvcRequest c_req, CCATS_PFCatsSubOrderUpdateRespHandler c_respHandler, void* cbArg);


/* 设置OrderUpdate处理函数。fillCorrData参数表示是否需要关联StartAlgo中的OrderCorrData */
int CCATS_SetOrderUpdateHandler(CCATS_PFCatsReceivedOrderUpdateHandler c_handler, void* cbArg, bool fillCorrData);



#if defined(__cplusplus) || defined(c_plusplus)
}
#endif



#endif // __CATS_SERVER_API_CWRAPPER_H__