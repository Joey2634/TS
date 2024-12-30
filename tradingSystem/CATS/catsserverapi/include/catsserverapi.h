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
	std::string mqIp;					// CATS��������ߵ�IP��ַ
	unsigned short mqBasePort = 45678;	// CATS��������ߵĻ����˿�
	int reqThreadCount = 1;				// ����������߳���
	int subThreadCount = 1;				// ��������Ϣ(Subscribed Data)���߳���
	int serverTimeoutMs = 10000;		// ����ʱ�ȴ�ʱ��(����)

	bool autoSubAlgoInstanceUpdate = true;	// �Ƿ��Զ������㷨ʵ�����¡���Ϊtrue����startAlgo�л��Զ�����subAlgoInstanceUpdate
	bool autoSubAlgoInstanceExecStat = true;  // �Ƿ��Զ������㷨ִ��ͳ�ơ���Ϊtrue���������㷨�ɹ�����Զ�����subAlgoInstanceExecStat
};


class CatsService {
private:
	CatsService(const CatsService&) ; // ��ֹ��������
	CatsService& operator=(const CatsService&) ; // ��ֹ����ֵ
public:
	CatsService(const CatsAPIParam& params);
	~CatsService();

	/* CATS�˺ŵ�¼ */
	int catsAcctLogin(const CATSLoginSvcRequest& req, PFCatsLoginRespHandler respHandler, void* cbArg);

	/* �ʽ��˺ŵ�¼ */
	int tradeAcctLogin(const CATSTradeAccountLoginSvcRequest& req, PFCatsTradeAccountLoginRespHandler respHandler, void* cbArg);

	/* �µ� */
	int submitOrder(const CATSSubmitOrderSvcRequest& req, PFCatsSubmitOrderRespHandler respHandler, void* cbArg);

	/* ���� */
	int cancelOrder(const CATSCancelOrderSvcRequest& req, PFCatsCancelOrderRespHandler respHandler, void* cbArg);

	/* �����㷨�� */
	int startAlgo(const CATSStartAlgoSvcRequest& req, PFCatsStartAlgoRespHandler respHandler, void* cbArg);

	/* ֹͣ�㷨�� */
	int stopAlgo(const CATSStopAlgoSvcRequest& req, PFCatsStopAlgoRespHandler respHandler, void* cbArg);

	/* ��ѯ�ֲ�(ע�⣺��������'G30'���͵��˻��������������͵��˻����ã���û����Ӧ) */
	int position2Query(const CATSPosition2QuerySvcRequest& req, PFCatsPosition2QueryRespHandler respHandler, void* cbArg);

	/* ��ѯ�ʽ�(ע�⣺��������'G30'���͵��˻��������������͵��˻����ã���û����Ӧ) */
	int fund2Query(const CATSFund2QuerySvcRequest& req, PFCatsFund2QueryRespHandler respHandler, void* cbArg);

	/************************************************************************/
	/* ����Ϊ������Ϣ�������󡣽��������ö��Ĵ��������ٷ��Ͷ�������     */
	/************************************************************************/
	
	/* �����㷨ʵ������ */
	int subAlgoInstanceUpdate(const CATSSubAlgoInstanceUpdateSvcRequest& req, PFCatsSubAlgoInstanceUpdateRespHandler respHandler, void* cbArg);

	/* �����㷨����ͳ�� */
	int subAlgoInstanceExecStat(const CATSSubAlgoInstanceExecStatSvcRequest& req, PFCatsSubAlgoInstanceExecStatRespHandler respHandler, void* cbArg);
	
	/* ����OrderUpdate */
	int subOrderUpdate(const CATSSubOrderUpdateSvcRequest& req, PFCatsSubOrderUpdateRespHandler respHandler, void* cbArg);

	/* �����ʲ����£������ֲ�(Positions)���ʽ�(Funds)�� */
	int subAssetUpdate(const CATSSubAssetUpdateSvcRequest& req, PFCatsSubAssetUpdateRespHandler respHandler, void* cbArg);

	/* ���Ŀ������� */
	int subRealMarketData(const CatsMarketDataSource& dataSource);

	/************************************************************************/
	/* ����Ϊ���ø��ֶ�����Ϣ�Ĵ�������  */
	/************************************************************************/

	/* ����OrderUpdate��������fillCorrData������ʾ�Ƿ���Ҫ����StartAlgo�е�OrderCorrData */
	int setOrderUpdateHandler(PFCatsReceivedOrderUpdateHandler handler, void* cbArg, bool fillCorrData = false);

	/* �����㷨ʵ�����´����� */
	int setAlgoInstanceUpdateHandler(PFCatsReceivedAlgoInstanceUpdateHandler handler, void* cbArg);

	/* �����㷨ִ��ͳ����Ϣ������ */
	int setAlgoInstanceExecStatHandler(PFCatsReceivedAlgoInstanceExecStatHandler handler, void* cbArg);

	/* �������鴦���� */
	int setRealMarketDataHandler(PFCatsReceivedRealMarketDataHandler handler, void* cbArg);

	/* ���óֲ�(Position)���´����� */
	int setPositionUpdateHandler(PFCatsReceivedPositionUpdateHandler handler, void* cbArg);

	/* �����ʽ�(Fund)���´����� */
	int setFundUpdateDataHandler(PFCatsReceivedFundUpdateHandler handler, void* cbArg);


	/******************************************/
	/* ��ȡ�������ʹ�����Ϣ                 */
	/******************************************/
	std::string getLastErrmsg();
	int getLastErrno();

	/**********************************************************/
	/* ��չ�ӿڣ��ǻ�������Ļ����ӿڷ�װ����ʹ�õĹ��ܽӿ� */
	/**********************************************************/
	/* �������㷨�������Ҷ����㷨ʵ�������Լ��㷨ִ��ͳ�� */
	int startAlgoBasket(
		const CATSStartAlgoBasketSvcRequest& req, 
		PFCatsStartAlgoBasketRespHandler respHandler, 
		void* cbArg, 
		int& basketId	/* OUT: ��������ID */
	);

	int stopAlgoBasket(
		const CATSStopAlgoBasketSvcRequest& req,
		PFCatsStopAlgoBasketRespHandler respHandler,
		void* cbArg
	);

	/* �����㷨ʵ�����´����� 
	singleHandler: ���յ����㷨ʵ�����µĻص�������
	basketHandler: �������ӻ����㷨ʵ�����µĻص�������
	ע�⣺�㷨�����е�ʵ������ͬʱ�ص�singleHandler��basketHandler��
	*/
	int setAlgoInstanceUpdateHandlerEx(
		PFCatsReceivedAlgoInstanceUpdateHandler singleHandler, void* cbArg,
		PFCatsReceivedBasketAlgoInstanceUpdateHandler basketHandler, void* basketCbArg
	);

private:
	void* impl;
};


/* д��־�ӿ� */
void CatsLogInfo(const char* fmt, ...);
void CatsLogWarn(const char* fmt, ...);
void CatsLogError(const char* fmt, ...);

#if defined(__cplusplus) || defined(c_plusplus)
}
#endif

#endif