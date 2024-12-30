#pragma once
#ifndef _CATS_SERVER_API_H__
#define _CATS_SERVER_API_H__

#include <string>
#include "catsmessage.h"

#define CATS_API_VERSION_MAJOR 0
#define CATS_API_VERSION_MINOR 9
#define CATS_API_VERSION_BUILD 20

#if defined(__cplusplus) || defined(c_plusplus)
extern "C" 
{
#endif

struct CatsAPIParam {
	std::string mqIp;					// CATS服务端总线的IP地址
	unsigned short mqBasePort = 45678;	// CATS服务端总线的基础端口
	int reqThreadCount = 1;				// 处理请求的线程数
	int subThreadCount = 1;				// 处理订阅消息(Subscribed Data)的线程数
	int serverTimeoutMs = 10000;		// 请求超时等待时间(毫秒)

	bool autoSubAlgoInstanceUpdate = true;	// 是否自动订阅算法实例更新。若为true，则startAlgo中会自动调用subAlgoInstanceUpdate
	bool autoSubAlgoInstanceExecStat = true;  // 是否自动订阅算法执行统计。若为true，则启动算法成功后会自动调用subAlgoInstanceExecStat
};


class CatsService {
private:
	CatsService(const CatsService&) ; // 禁止拷贝构造
	CatsService& operator=(const CatsService&) ; // 禁止对象赋值
public:
	CatsService(const CatsAPIParam& params);
	~CatsService();

	/* CATS账号登录 */
	int catsAcctLogin(const CATSLoginSvcRequest& req, PFCatsLoginRespHandler respHandler, void* cbArg);

	/* 资金账号登录 */
	int tradeAcctLogin(const CATSTradeAccountLoginSvcRequest& req, PFCatsTradeAccountLoginRespHandler respHandler, void* cbArg);

	/* 下单 */
	int submitOrder(const CATSSubmitOrderSvcRequest& req, PFCatsSubmitOrderRespHandler respHandler, void* cbArg);

	/* 撤单 */
	int cancelOrder(const CATSCancelOrderSvcRequest& req, PFCatsCancelOrderRespHandler respHandler, void* cbArg);

	/* 启动算法单 */
	int startAlgo(const CATSStartAlgoSvcRequest& req, PFCatsStartAlgoRespHandler respHandler, void* cbArg);

	/* 停止算法单 */
	int stopAlgo(const CATSStopAlgoSvcRequest& req, PFCatsStopAlgoRespHandler respHandler, void* cbArg);

	/* 查询持仓(注意：仅能用于'G30'类型的账户。若对其他类型的账户调用，会没有响应) */
	int position2Query(const CATSPosition2QuerySvcRequest& req, PFCatsPosition2QueryRespHandler respHandler, void* cbArg);

	/* 查询资金(注意：仅能用于'G30'类型的账户。若对其他类型的账户调用，会没有响应) */
	int fund2Query(const CATSFund2QuerySvcRequest& req, PFCatsFund2QueryRespHandler respHandler, void* cbArg);

	/************************************************************************/
	/* 以下为发送消息订阅请求。建议先设置订阅处理函数，再发送订阅请求。     */
	/************************************************************************/
	
	/* 订阅算法实例更新 */
	int subAlgoInstanceUpdate(const CATSSubAlgoInstanceUpdateSvcRequest& req, PFCatsSubAlgoInstanceUpdateRespHandler respHandler, void* cbArg);

	/* 订阅算法运行统计 */
	int subAlgoInstanceExecStat(const CATSSubAlgoInstanceExecStatSvcRequest& req, PFCatsSubAlgoInstanceExecStatRespHandler respHandler, void* cbArg);
	
	/* 订阅OrderUpdate */
	int subOrderUpdate(const CATSSubOrderUpdateSvcRequest& req, PFCatsSubOrderUpdateRespHandler respHandler, void* cbArg);

	/* 订阅资产更新（包括持仓(Positions)和资金(Funds)） */
	int subAssetUpdate(const CATSSubAssetUpdateSvcRequest& req, PFCatsSubAssetUpdateRespHandler respHandler, void* cbArg);

	/* 订阅快照行情 */
	int subRealMarketData(const CatsMarketDataSource& dataSource);

	/************************************************************************/
	/* 以下为设置各种订阅消息的处理函数。  */
	/************************************************************************/

	/* 设置OrderUpdate处理函数。fillCorrData参数表示是否需要关联StartAlgo中的OrderCorrData */
	int setOrderUpdateHandler(PFCatsReceivedOrderUpdateHandler handler, void* cbArg, bool fillCorrData = false);

	/* 设置算法实例更新处理函数 */
	int setAlgoInstanceUpdateHandler(PFCatsReceivedAlgoInstanceUpdateHandler handler, void* cbArg);

	/* 设置算法执行统计信息处理函数 */
	int setAlgoInstanceExecStatHandler(PFCatsReceivedAlgoInstanceExecStatHandler handler, void* cbArg);

	/* 设置行情处理函数 */
	int setRealMarketDataHandler(PFCatsReceivedRealMarketDataHandler handler, void* cbArg);

	/* 设置持仓(Position)更新处理函数 */
	int setPositionUpdateHandler(PFCatsReceivedPositionUpdateHandler handler, void* cbArg);

	/* 设置资金(Fund)更新处理函数 */
	int setFundUpdateDataHandler(PFCatsReceivedFundUpdateHandler handler, void* cbArg);


	/******************************************/
	/* 获取错误代码和错误消息                 */
	/******************************************/
	std::string getLastErrmsg();
	int getLastErrno();

	/**********************************************************/
	/* 扩展接口，是基于上面的基础接口封装，简化使用的功能接口 */
	/**********************************************************/
	/* 批量起算法单，并且订阅算法实例更新以及算法执行统计 */
	int startAlgoBasket(
		const CATSStartAlgoBasketSvcRequest& req, 
		PFCatsStartAlgoBasketRespHandler respHandler, 
		void* cbArg, 
		int& basketId	/* OUT: 返回篮子ID */
	);

	int stopAlgoBasket(
		const CATSStopAlgoBasketSvcRequest& req,
		PFCatsStopAlgoBasketRespHandler respHandler,
		void* cbArg
	);

	/* 设置算法实例更新处理函数 
	singleHandler: 接收单个算法实例更新的回调函数。
	basketHandler: 接收篮子汇总算法实例更新的回调函数。
	注意：算法篮子中的实例，会同时回调singleHandler和basketHandler。
	*/
	int setAlgoInstanceUpdateHandlerEx(
		PFCatsReceivedAlgoInstanceUpdateHandler singleHandler, void* cbArg,
		PFCatsReceivedBasketAlgoInstanceUpdateHandler basketHandler, void* basketCbArg
	);

private:
	void* impl;
};


/* 写日志接口 */
void CatsLogInfo(const char* fmt, ...);
void CatsLogWarn(const char* fmt, ...);
void CatsLogError(const char* fmt, ...);

#if defined(__cplusplus) || defined(c_plusplus)
}
#endif

#endif