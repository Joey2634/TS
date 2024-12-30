#pragma once
#include <vector>

#ifndef _CATS_SUBSCRIBE_MESSAGE_DEFINITION_H
#define _CATS_SUBSCRIBE_MESSAGE_DEFINITION_H

#define int32	int
#define uint32	unsigned int
#define int64	long long

#pragma pack(push)

/* 按1字节对齐 */
#pragma pack (1)

struct CatsRealMarketData {
	char symbol[32];			//商品代码（每次都传）
	int32 date;  				//YYYYMMDD
	int32 time;  				//HHMMSSmmm 行情时间
	
	unsigned char stopMark;  	//停牌标志 (1 停牌)（每次都传）
	int32 cjbs;  				//深交所发布 行情成交笔数
	char futureCode[8]; 		//期货行情 期货交易品种，如AL IF CU...
	char stkName[16];  			//股票名称

	uint32 lastPrice;  			//当前价格（×10000）
	uint32 openPrice;  			//开盘价（×10000）
	uint32 highPrice;  			//最高价（×10000）
	uint32 lowPrice;  			//最低价（×10000）
	uint32 prevClosePrice;		//昨日收盘（×10000）
	uint32 closePrice;  		//今日收盘（×10000）
	uint32 highLimited; 		//涨停板价（×10000）
	uint32 lowLimited; 			//跌停板价（×10000）
	uint32 settlement; 			//期货行情 今结算价（×10000）
	uint32 prevSettlement; 		//期货行情 前结算价（×10000）

	uint32 bidPrice1;  			//申买价1（×10000）
	uint32 askPrice1;  			//申卖价1（×10000）
	uint32 bidPrice2;  			//申买价2（×10000）
	uint32 askPrice2;  			//申卖价2（×10000）
	uint32 bidPrice3;  			//申买价3（×10000）
	uint32 askPrice3;  			//申卖价3（×10000）
	uint32 bidPrice4;  			//申买价4（×10000）
	uint32 askPrice4;  			//申卖价4（×10000）
	uint32 bidPrice5;  			//申买价5（×10000）
	uint32 askPrice5;  			//申卖价5（×10000）
	uint32 bidPrice6;  			//申买价6（×10000）
	uint32 askPrice6;  			//申卖价6（×10000）
	uint32 bidPrice7;  			//申买价7（×10000）
	uint32 askPrice7;  			//申卖价7（×10000）
	uint32 bidPrice8;  			//申买价8（×10000）
	uint32 askPrice8;  			//申卖价8（×10000）
	uint32 bidPrice9;  			//申买价9（×10000）
	uint32 askPrice9;  			//申卖价9（×10000）
	uint32 bidPrice10;  		//申买价10（×10000）
	uint32 askPrice10;  		//申卖价10（×10000）

	int64 turnOver;  			//总成交金额
	uint32 peRatio1;  			//深交所发布 行情市盈率1（×10000）
	uint32 peRatio2;  			//深交所发布 行情市盈率2（×10000）
	uint32 prevDelta;  			//期货行情 昨虚实度（×10000）
	uint32 curDelta;  			//期货行情 今虚实度（×10000）
	uint32 openInterest; 		//期货行情 持仓量
	uint32 prevOpenInterest;	//期货行情 前持仓量
	int64 volume;  				//总成交量

	uint32 bidVol1;  			//申买量1
	uint32 askVol1;  			//申卖量1
	uint32 bidVol2;  			//申买量2
	uint32 askVol2;  			//申卖量2
	uint32 bidVol3;  			//申买量3
	uint32 askVol3;  			//申卖量3
	uint32 bidVol4;  			//申买量4
	uint32 askVol4;  			//申卖量4
	uint32 bidVol5;  			//申买量5
	uint32 askVol5;  			//申卖量5
	uint32 bidVol6;  			//申买量6
	uint32 askVol6;  			//申卖量6
	uint32 bidVol7;  			//申买量7
	uint32 askVol7;  			//申卖量7
	uint32 bidVol8;  			//申买量8
	uint32 askVol8;  			//申卖量8
	uint32 bidVol9;  			//申买量9
	uint32 askVol9;  			//申卖量9
	uint32 bidVol10;  			//申买量10
	uint32 askVol10;  			//申卖量10

	uint32 curVol;				//现量
	int32 IOPV;					//IOPV预估净值（×10000）
	int32 yieldToMaturity;		//到期收益率（×10000）

	int32 accer; //涨速  (eg. 10000表示1%)
	uint32 weightedAvgBidPrice; //加权平均委买价格
	uint32 weightedAvgAskPrice; //加权平均委卖价格
	int status;     //状态，具体请参考字典表
	char  reserved[20]; //reserved for later

	std::string toString() const;
} ;

#pragma pack(pop)

struct CatsPositionUpdateData {
	std::string acctType;
	std::string acct;

	std::string symbol;
	long long currentQty;    // 当前数量
	long long enabledQty;    // 可用数量
	float incomeBalance;    // 盈亏金额

								   /* 证券相关 */
	float costPrice;        // 成本价  期权为持仓成本（累积买+当日买-累积卖-当日卖）
	float lastPrice;        // 最新价
	float marketValue;        // 参考市值
	std::string stockName;        // 证券简称

	long long frozenQty;    //冻结数量
	long long unfrozenQty;    //解冻数量

	long long beginQty;        //期初数量
	long long realBuyQty;    //当天买入成交数量 暂不支持
	long long realSellQty;    //当天卖出成交数量 暂不支持

								/* 期货相关 */
	std::string direction;         //持仓多空方向：1-净;2-多头;3-空头  期权持仓类别,"0":权利方|"1":义务方|"2":备兑方
	std::string positionDate;    //持仓日期类型：1-今日持仓;2-历史持仓
	std::string hedgeFlag;       //投机套保标志：1-投机;2-套利;3-套保
	long long ydPosition;     //上日持仓
	long long longFrozen;     //多头冻结
	long long shortFrozen;    //空头冻结
	float useMargin;        //占用的保证金
	float positionCost;     //持仓成本
	float positionProfit;     //持仓盈亏
	float closeProfit;      //平仓盈亏

	long long openVolume;     //开仓数量
	float openAmount;       //开仓金额
	long long closeVolume;    //平仓数量
	float closeAmount;      //平仓金额
	long long todayPosition;  //今日持仓

	float closeProfitByDate; //逐日盯市平仓盈亏
	float closeProfitByTrade;//逐笔对冲平仓盈亏

									/* 期权相关 */
	float holdQty;        // 持有数量（包括委托未成交部分）
	float realOpenQty;        // 今开仓持仓量
	float realDropQty;    // 今平仓持仓量
	float entrustDropQty;    // 今平仓委托量
	float openAvgPrice;    // 开仓均价
	float buyAvgQty;        // 买入均价
	float avgIncomeBalance;// 实现盈亏
	float exerciseIncome;    // 行权盈亏金额
	float dutyUsedBail;    // 义务仓占用保证金

	std::string toString() const;
};

struct CatsFundUpdateData {
	std::string acctType;
	std::string acct;

	float currentBalance;    // 当前余额（期货结算准备金）
	float enabledBalance;    // 可用余额
	std::string moneyType;   // 货币类型

	/* 证券相关 */
	std::string fundAcct;  // 资金账户

	float beginBalance;    //期初余额
	float fetchBalance;    //可取金额
	float frozenBalance;   //冻结金额
	float unfrozenBalace;  //解冻金额

	/* 期货、期权相关 */
	float deposit;         //入金金额
	float withdraw;        //出金金额
	float frozenMargin;    //冻结保证金
	float frozenCash;      //冻结的资金
	float currMargin;      //当前保证金总额
	float closeProfit;     //平仓盈亏
	float positionProfit;  //持仓盈亏

	float preBalance;        //上次结算准备金
	float preMargin;        //上次占用的保证金
	float preDeposit;        //上次存款额
	float preCredit;        //上次信用额度
	float preMortgage;        //上次质押金额
	float mortgage;        //质押金额
	float credit;            //信用额度
	float frozenCommission;//冻结手续费
	float commission;        //手续费
	float dynamicEquity;    //动态权益

	/* 期权相关 */
	float optionCloseProfile;//期权平仓盈亏

	//个股期权
	float enableBailBalance;    //可用保证金  --> 实时保证金
	float usedBailBalance;     //已用保证金
	float usedPurBalance;     //已用买入额度
	float enablePurBalace;     //可用买入额度

	float netBuyAmount;        //净买入额
	float withdrawnRate;        //撤单率
	float filledRate;            //成交率
	float rejectedRate;        //拒单率

	virtual std::string toString() const;
};

struct CatsOrderUpdateData {
	std::string acctType;// 账户类型
	std::string acct;    // 账户名称
	std::string catsAcct; // cats账户名称
	std::string symbol;  // 合约代码
	int orderQty; // 报单总数量
	std::string orderPrice;  // 报单价格
	std::string tradeSide; // 报单方向
	std::string orderType;  // 报单类型
	std::string orderParam;  // 报单参数
	std::string orderNo;  // CATS内部显示的订单编号

	std::string corrType; // corrType
	std::string corrID;   // 内部ID; 算法单子单中，等于AlgoInstanceId

	int filledQty;  // 成交数量
	std::string avgPrice;  // 成交均价
	int cancelQty; // 取消数量

	std::string lastTime; //最后更新时间  格式为 hhmmss

	/*status 参数说明
	0 新单(未结)
	1 部分成交(未结)
	2 全成(已结)
	3 部分撤单(已结)
	4 全撤(已结)
	5 拒单(已结)
	*/
	int status;  // 报单状态

	std::string orderTime;  // 委托时间  格式为hhmmss
	std::string orderDate;  // 委托日期  格式yyyymmdd

	std::string orderCorrData;  // 算法母单的startAlgo请求中带的orderCorrData
	long long algoData1 = 0;
	long long algoData2 = 0;

	int basketId = 0;			 // 使用extStartAlgoBasket启动算法篮子的篮子ID
	int basketItemIndex = 0;

	long long localTs;			// 本地时间戳(ms)。用于超时老化
	virtual std::string toString() const;
};


struct CatsAlgoInstanceUpdateData {
	virtual ~CatsAlgoInstanceUpdateData() {};
	std::string algoId; //策略id
	std::string algoInstanceId;  //实例id
	std::string catsAcct;  //cats账号
	bool stopped; //是否已经停止，true表示该实例已经停止，否则未停止
	std::string message;  //消息
	std::map<std::string, std::string> params;  //策略参数
	int startTime;   //策略开始时间，格式为 HHMMSSsss, eg:102433700
	int stopTime;    //策略结束时间，格式为 HHMMSSsss, eg:102433700
	int date;       //日期，最后一次更新日期  格式为YYYYMMDD         eg:20190604
	int time;      //时间， 最后一次更新时间 格式为 HHMMSSsss, eg:102433700

	/* custom datas */
	std::string orderCorrData;
	long long algoData1 = 0;
	long long algoData2 = 0;

	/* 以下只有起算法篮子会用到 */
	int basketId = 0;	// 使用extStartAlgoBasket启动算法篮子的篮子ID
	int basketItemIndex = 0;

	long long localTs;			// 本地时间戳(ms)。用于超时老化
	virtual std::string toString() const;
};


struct CatsAlgoInstanceUpdateDataEx : public CatsAlgoInstanceUpdateData {
	virtual ~CatsAlgoInstanceUpdateDataEx() {};

	virtual std::string toString() const;

	void assignFromCatsAlgoInstanceUpdateData(const CatsAlgoInstanceUpdateData& o);
};


struct CatsBasketAlgoInstanceUpdateData {
	int basketId = 0;		// 篮子ID
	size_t basketSize = 0;	// 篮子大小
	int updateIdx = 0;		// 本次更新的item索引
	std::vector<CatsAlgoInstanceUpdateDataEx*> itemUpdateDatas; // 对应篮子里的algoInstanceUpdate

	virtual std::string toString() const;
};

struct CatsAlgoInstanceExecStatData {
	std::string algoId;   //策略id
	std::string algoInstanceId;  //策略实例id
	std::string acctType;  // 账户类型
	std::string acct;  // 账户名称
	std::string symbol;  // 合约代码

	std::string tradeSide;  // 交易方向
	int targetQty;  // 交易目标量
	int orderQty;   // 订单请求量
	std::string orderPrice;   // 下单价格
	int filledQty;   // 成交量

	std::string avgPrice;   // 成交均价
	int cancelQty;   // 取消量
	int rejectQty;   // 拒绝量
	int pendingQty; // 挂单量
	int orderCnt;   // 下单次数 ，无论下单成功还是失败,只要触发下单就递增1，

	int filledCnt; //成交次数
	int cancelCnt; //撤单次数
	int rejectCnt; //拒单次数
	std::string lastOrderNo; //最后一个订单编号
									  /* lastOrderStatus 参数说明
									  0 新单(未结)
									  1 部分成交(未结)
									  2 全成(已结)
									  3 部分撤单(已结)
									  4 全撤(已结)
									  5 拒单(已结)
									  6 柜台拒绝，下单后超时等原因，或其他原因导致的错误状态（比如撤单时返回的订单号不是原先的单号）
									  999  每个算法实例执行统计初始化的一个值，第一条执行统计的推送可能为该值。
									  */
	int lastOrderStatus; //最后一个订单状态

	std::string lastOrderType;  //最后一个订单类型
	std::string lastOrderPrice;	//最后一个订单价格
	std::string lastError;		//最后错误信息
	std::string remark;

	/* custom datas */
	std::string orderCorrData;
	long long algoData1 = 0;
	long long algoData2 = 0;

	int basketId = 0;				// 使用extStartAlgoBasket启动算法篮子的篮子ID
	int basketItemIndex = 0;

	long long localTs;			// 本地时间戳(ms)。用于超时老化
	virtual std::string toString() const;
};

#endif /* _CATS_SUBSCRIBE_MESSAGE_DEFINITION_H */

