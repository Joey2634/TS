#pragma once

#include <string>
#include <map>
#include <vector>
#include "catssubscribedmessage.h"

#ifndef STDSTR
#define STDSTR std::string
#endif

/* 客户端信息  */
struct ClientLocationInfo {
	ClientLocationInfo() {};
	ClientLocationInfo(STDSTR ip, STDSTR macAddr, STDSTR hdSerial) :
		ip(ip), macAddr(macAddr), hdSerial(hdSerial) {};
	STDSTR ip;			// IP地址
	STDSTR macAddr;		// MAC地址
	STDSTR hdSerial;	// 硬盘序列号

	STDSTR toString() const;
};

/* Cats账户信息（登陆后）.
除了catsAcctLogin请求外，其余请求都含有该结构体。这些请求均需要设置正确的cats用户名和token串用于身份校验。
*/
struct CatsAccountData {
	CatsAccountData() {};
	CatsAccountData(STDSTR catsAcct, STDSTR catsToken) : catsAcct(catsAcct), catsToken(catsToken) {};
	STDSTR catsAcct;	// cats账户名
	STDSTR catsToken;	// cats账户登陆成功后得到的token串

	STDSTR toString() const;
};

/************************************************************************/
/* 请求和响应消息的基类                                                 */
/************************************************************************/
struct CATSSvcRequestBase {
	virtual ~CATSSvcRequestBase() { };
	virtual STDSTR toString() { return "";  };
};

struct CATSSvcResponseBase {
	virtual ~CATSSvcResponseBase() { };
	STDSTR errCode;
	STDSTR errMsg;
	virtual STDSTR toString() { return "errCode=" + errCode + ",errMsg=" + errMsg;  };
};

/************************************************************************/
/* Service: CATS Login                                                  */
/************************************************************************/
struct CATSLoginSvcRequest : public CATSSvcRequestBase {
	CATSLoginSvcRequest() {};
	CATSLoginSvcRequest(STDSTR catsAcct, STDSTR password, ClientLocationInfo clientInfo) :
		catsAcct(catsAcct), password(password), clientInfo(clientInfo) {}
	STDSTR catsAcct;	// cats账户名
	STDSTR password;	// cats密码
	ClientLocationInfo clientInfo;	// 客户端信息
	
	virtual std::string toString() const;
};

struct CATSLoginSvcResponse : public CATSSvcResponseBase {
	STDSTR catsAcct;	// cats账户名
	STDSTR catsToken;	// 登陆成功时，服务端生成的token串。用户后续的请求
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: Trade Acct Login                                            */
/************************************************************************/
struct CATSTradeAccountLoginSvcRequest : public CATSSvcRequestBase {
	CATSTradeAccountLoginSvcRequest() {};
	CATSTradeAccountLoginSvcRequest(CatsAccountData catsAcctData, STDSTR acctType, STDSTR acct, STDSTR password, STDSTR loginParam, ClientLocationInfo clientInfo) :
		catsAcctData(catsAcctData), acctType(acctType), acct(acct), password(password), loginParam(loginParam), clientInfo(clientInfo) {};
	CatsAccountData catsAcctData;
	STDSTR acctType;	// 资金账户类型
	STDSTR acct;		// 资金账户
	STDSTR password;	// 资金账户密码
	STDSTR loginParam;	// 登陆类型
	ClientLocationInfo clientInfo;	// 客户端信息
	virtual std::string toString() const;
};

struct CATSTradeAccountLoginSvcResponse : public CATSSvcResponseBase {
	STDSTR acctType;
	STDSTR acct;
	STDSTR branchName;	// 分支机构名称
	STDSTR name;		// 客户名称
	STDSTR spcashStatus;
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: Submit Order                                                */
/************************************************************************/
#define ORDER_PARAM_EMPTY					""
#define ORDER_PARAM_FUTURE_SPECULATION		"1"	//投机
#define ORDER_PARAM_FUTURE_ARBITRAGE		"2"	//套利
#define ORDER_PARAM_FUTURE_HEDGE			"3"	// 套保
#define ORDER_PARAM_HK_ENHANCED_LIMIT			"HKN,0"	//港股订单申报，增强限价盘
#define ORDER_PARAM_ODD_LOT_ENHANCED_LIMIT		"HKO,0"	//港股零股申报，增强限价盘
#define ORDER_PARAM_HK_AUCTION_LIMIT			"HKN,1"	//港股订单申报，竞价限价盘
#define ORDER_PARAM_HK_ODD_LOT_AUCTION_LIMIT	"HKO,1"	//港股零股申报，竞价限价盘
#define ORDER_PARAM_CREDIT_SPECIAL_CLASH		"spcash"	//使用专项头寸融券卖出

struct CATSOrderRequest {
	STDSTR acctType;	// 资金账户类型
	STDSTR acct;		// 资金账户
	STDSTR symbol;		// 标的代码，如 600030.SH
	STDSTR tradeSide;/*	普通:
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
	STDSTR orderType; /* 上海 股票、信用
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
	STDSTR priceValue;	// 委托价格
	int qty;			// 委托量
	STDSTR orderParam;	// 参考上面的ORDER_PARAM_xxx系列宏定义。一般A股交易可传""
	virtual std::string toString() const;
};

struct CATSSubmitOrderSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;		
	CATSOrderRequest catsOrderRequest;	// 下单参数
	virtual std::string toString() const;
};

struct CATSSubmitOrderSvcResponse : public CATSSvcResponseBase {
	STDSTR orderNo;	// 订单ID
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: Cancel Order                                                */
/************************************************************************/
struct CATSCancelOrderSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;	// 登陆身份信息
	STDSTR orderNo;		// 订单ID
	STDSTR acctType;
	STDSTR acct;
	virtual std::string toString() const;
};

struct CATSCancelOrderSvcResponse : public CATSSvcResponseBase {
	STDSTR origOrderNo;	// 被撤销的原始订单ID
	STDSTR orderNo;		// 撤单ID
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: Start Algo                                                */
/************************************************************************/
struct CATSStartAlgoSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	STDSTR algoId;			// 算法类型ID，如"TWAP", "VWAP"等等
	STDSTR orderCorrData;	// 此数据会在子单orderUpdate中携带
	long long algoData1;
	long long algoData2;
	std::map<std::string, std::string> algoParams; // 算法参数。具体参加每个算法的说明

	virtual std::string toString() const;
};

struct CATSStartAlgoSvcResponse : public CATSSvcResponseBase {
	STDSTR algoInstanceId;	// 算法实例ID
	STDSTR orderCorrData;
	long long algoData1;
	long long algoData2;
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: Stop Algo */
/************************************************************************/
struct CATSStopAlgoSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	STDSTR algoId;	// 算法类型ID，如"TWAP", "VWAP"等等
	STDSTR algoInstanceId;	// 需要停止的算法实例ID

	virtual std::string toString() const;
};

struct CATSStopAlgoSvcResponse : public CATSSvcResponseBase {
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: Position2 Query */
/************************************************************************/
struct CATSPosition2Data {
	STDSTR symbol;
	int currentQty;		// 当前数量
	int enabledQty;		// 可用数量	
	float costPrice;	// 成本价

	/* 期货相关 */
	STDSTR direction;	//持仓多空方向：1-净;2-多头;3-空头  期权持仓类别,"0":权利方|"1":义务方|"2":备兑方
	STDSTR hedgeFlag;	//投机套保标志：1-投机;2-套利;3-套保
	STDSTR stockAcct;	//股东代码
	std::string toString() const;
};

struct CATSPosition2QuerySvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	STDSTR acctType;
	STDSTR acct;
	int maxRowNum = 20;	// 每页数据条数
	int pageNum = 0;	// 页码
	virtual std::string toString() const;
};

struct CATSPosition2QuerySvcResponse : public CATSSvcResponseBase {
	std::vector<CATSPosition2Data> positions;
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: Fund2 Query */
/************************************************************************/
struct CATSFund2Data {
	float beginBalance;		// 期初余额
	float currentBalance;	// 当前余额
	float enabledBalance;	// 可用余额
	float fetchBalance;		// 可取金额
	STDSTR moneyType;		// 货币类型
	STDSTR fundAcct;		// 资金账户

	/* 期货、期权相关 */
	float currMargin;		// 当前保证金总额
	float dynamicEquity;	// 动态权益

	/* 个股期权 */
	float enableBailBalance;	// 可用保证金  --> 实时保证金
	float usedBailBalance;		// 已用保证金
	float usedPurBalance;		// 已用买入额度
	float enablePurBalace;		// 可用买入额度
	STDSTR direction;			//持仓多空方向：1-净;2-多头;3-空头  期权持仓类别,"0":权利方|"1":义务方|"2":备兑方

	std::string toString() const;
};

struct CATSFund2QuerySvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	STDSTR acctType;
	STDSTR acct;

	virtual std::string toString() const;
};

struct CATSFund2QuerySvcResponse : public CATSSvcResponseBase {
	std::vector<CATSFund2Data> funds;
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: Sub AlgoInstanceUpdate                                      */
/************************************************************************/
struct CATSSubAlgoInstanceUpdateSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	STDSTR algoId;
	virtual std::string toString() const;
};

struct CATSSubAlgoInstanceUpdateSvcResponse : public CATSSvcResponseBase {
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: Sub AlgoInstanceExecStat                                    */
/************************************************************************/
struct CATSSubAlgoInstanceExecStatSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	STDSTR algoId;
	STDSTR algoInstanceId;
	STDSTR acct; // 用于订阅topic
	virtual std::string toString() const;
};

struct CATSSubAlgoInstanceExecStatSvcResponse : public CATSSvcResponseBase {
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: SubOrderUpdate                                               */
/************************************************************************/
struct CATSSubOrderUpdateSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	STDSTR acctType;
	STDSTR acct;
	bool notPubHist;
	virtual std::string toString() const;
};

struct CATSSubOrderUpdateSvcResponse : public CATSSvcResponseBase {
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: SubAssetUpdate                                              */
/************************************************************************/
struct CATSSubAssetUpdateSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	STDSTR acctType;
	STDSTR acct;
	virtual std::string toString() const;
};

struct CATSSubAssetUpdateSvcResponse : public CATSSvcResponseBase {
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: GetSafeKeyByAcct                                              */
/************************************************************************/
struct CATSGetSafeKeySvcRequest : public CATSSvcRequestBase {
	STDSTR acct;
	virtual std::string toString() const;
};

struct CATSGetSafeKeySvcResponse : public CATSSvcResponseBase {
	bool isEncrypted;
	STDSTR aesKey;
	virtual std::string toString() const;
};

/************************************************************************/
/* Extend Service: Start Algo Basket                                    */
/************************************************************************/
struct CATSExtAlgoBusketItem {
	STDSTR orderCorrData;	// 此数据会在子单orderUpdate中携带
	std::map<std::string, std::string> params;
	long long algoData1;
	long long algoData2;
};

struct CATSStartAlgoSvcResponseEx : public CATSStartAlgoSvcResponse {
	virtual std::string toString() const;
};

struct CATSStartAlgoBasketSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	STDSTR algoId;			// 算法类型ID，如"TWAP", "VWAP"等等	
	std::map<std::string, std::string> algoParams; // 算法篮子中的通用参数。具体参加每个算法的说明
	std::vector<CATSExtAlgoBusketItem> basket;	// 篮子参数，设置篮子中每个算法实例的不同参数、corrData等

	virtual std::string toString() const;
};

// 如果所有子单都成功，则errCode为0，否则为1
struct CATSStartAlgoBasketSvcResponse : public CATSSvcResponseBase {
	std::vector<CATSStartAlgoSvcResponseEx*> itemResponses; // 篮子中每个算法单的响应。与请求中的basket顺序相同。
	int basketId;
	int updateIdx;	// 本次更新的篮子条目index.(每次回调会且只会更新1条数据)
	virtual std::string toString() const;
};

/************************************************************************/
/* Extend Service: Stop Algo Basket                                     */
/************************************************************************/
struct CATSStopAlgoSvcResponseEx : public CATSStopAlgoSvcResponse {
	virtual std::string toString() const;
};

struct CATSStopAlgoBasketSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	int basketId;
	virtual std::string toString() const;
};

// 如果所有子单都成功，则errCode为0，否则为1
struct CATSStopAlgoBasketSvcResponse : public CATSSvcResponseBase {
	std::vector<CATSStopAlgoSvcResponseEx*> itemResponses; // 篮子中每个算法单的响应。与请求中的basket顺序相同。
	int basketId;
	int updateIdx;	// 本次更新的篮子条目index.(每次回调会且只会更新1条数据)
	virtual std::string toString() const;
};


/***************************************************************/
/*  行情源定义                                                 */
/***************************************************************/
enum CatsMarketDataSource {
	SZ,     //深圳
	SH,     //上海(不含期权)
	SHOption,    // 上海期权

	CFFEX,  //中金所
	CZCE,   //郑交所
	SHFE,   //上期所
	INE,    //上海国际能源
	DCE,    //大交所

	ES,     // 易盛,国际期货行情。

	HKSZ,   //深港通
	HKSH,   //沪港通
	HKZ,    //可转股
};


/************************************************************************/
/*  Handlers of responses                                               */
/************************************************************************/
typedef void(*PFCatsLoginRespHandler)(const CATSLoginSvcResponse& resp, void* cbArg);
typedef void(*PFCatsTradeAccountLoginRespHandler)(const CATSTradeAccountLoginSvcResponse& resp, void* cbArg);

typedef void(*PFCatsSubmitOrderRespHandler)(const CATSSubmitOrderSvcResponse& resp, void* cbArg);
typedef void(*PFCatsCancelOrderRespHandler)(const CATSCancelOrderSvcResponse& resp, void* cbArg);

typedef void(*PFCatsStartAlgoRespHandler)(const CATSStartAlgoSvcResponse& resp, void* cbArg);
typedef void(*PFCatsStopAlgoRespHandler)(const CATSStopAlgoSvcResponse& resp, void* cbArg);

typedef void(*PFCatsPosition2QueryRespHandler)(const CATSPosition2QuerySvcResponse& resp, void* cbArg);
typedef void(*PFCatsFund2QueryRespHandler)(const CATSFund2QuerySvcResponse& resp, void* cbArg);

typedef void(*PFCatsSubAlgoInstanceUpdateRespHandler)(const CATSSubAlgoInstanceUpdateSvcResponse& resp, void* cbArg);
typedef void(*PFCatsSubAlgoInstanceExecStatRespHandler)(const CATSSubAlgoInstanceExecStatSvcResponse& resp, void* cbArg);

typedef void(*PFCatsSubOrderUpdateRespHandler)(const CATSSubOrderUpdateSvcResponse& resp, void* cbArg); // order update
typedef void(*PFCatsSubAssetUpdateRespHandler)(const CATSSubAssetUpdateSvcResponse& resp, void* cbArg); // 包括position和fund

typedef void(*PFCatsGetSafeKeyRespHandler)(const CATSGetSafeKeySvcResponse& resp, void* cbArg);

typedef void(*PFCatsStartAlgoBasketRespHandler)(const CATSStartAlgoBasketSvcResponse& resp, void* cbArg);
typedef void(*PFCatsStopAlgoBasketRespHandler)(const CATSStopAlgoBasketSvcResponse& resp, void* cbArg);

/************************************************************************/
/* Handlers of subscribed data										     */
/************************************************************************/
typedef void(*PFCatsReceivedRealMarketDataHandler)(const CatsRealMarketData& md, void* cbArg);
typedef void(*PFCatsReceivedPositionUpdateHandler)(const CatsPositionUpdateData& md, void* cbArg);
typedef void(*PFCatsReceivedFundUpdateHandler)(const CatsFundUpdateData& md, void* cbArg);
typedef void(*PFCatsReceivedOrderUpdateHandler)(const CatsOrderUpdateData& md, void* cbArg);
typedef void(*PFCatsReceivedAlgoInstanceUpdateHandler)(const CatsAlgoInstanceUpdateData& md, void* cbArg);
typedef void(*PFCatsReceivedAlgoInstanceExecStatHandler)(const CatsAlgoInstanceExecStatData& md, void* cbArg);

typedef void(*PFCatsReceivedBasketAlgoInstanceUpdateHandler)(const CatsBasketAlgoInstanceUpdateData& md, void* cbArg);