#pragma once

#include <string>
#include <map>
#include <vector>
#include "catssubscribedmessage.h"

#ifndef STDSTR
#define STDSTR std::string
#endif

/* �ͻ�����Ϣ  */
struct ClientLocationInfo {
	ClientLocationInfo() {};
	ClientLocationInfo(STDSTR ip, STDSTR macAddr, STDSTR hdSerial) :
		ip(ip), macAddr(macAddr), hdSerial(hdSerial) {};
	STDSTR ip;			// IP��ַ
	STDSTR macAddr;		// MAC��ַ
	STDSTR hdSerial;	// Ӳ�����к�

	STDSTR toString() const;
};

/* Cats�˻���Ϣ����½��.
����catsAcctLogin�����⣬�������󶼺��иýṹ�塣��Щ�������Ҫ������ȷ��cats�û�����token���������У�顣
*/
struct CatsAccountData {
	CatsAccountData() {};
	CatsAccountData(STDSTR catsAcct, STDSTR catsToken) : catsAcct(catsAcct), catsToken(catsToken) {};
	STDSTR catsAcct;	// cats�˻���
	STDSTR catsToken;	// cats�˻���½�ɹ���õ���token��

	STDSTR toString() const;
};

/************************************************************************/
/* �������Ӧ��Ϣ�Ļ���                                                 */
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
	STDSTR catsAcct;	// cats�˻���
	STDSTR password;	// cats����
	ClientLocationInfo clientInfo;	// �ͻ�����Ϣ
	
	virtual std::string toString() const;
};

struct CATSLoginSvcResponse : public CATSSvcResponseBase {
	STDSTR catsAcct;	// cats�˻���
	STDSTR catsToken;	// ��½�ɹ�ʱ����������ɵ�token�����û�����������
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
	STDSTR acctType;	// �ʽ��˻�����
	STDSTR acct;		// �ʽ��˻�
	STDSTR password;	// �ʽ��˻�����
	STDSTR loginParam;	// ��½����
	ClientLocationInfo clientInfo;	// �ͻ�����Ϣ
	virtual std::string toString() const;
};

struct CATSTradeAccountLoginSvcResponse : public CATSSvcResponseBase {
	STDSTR acctType;
	STDSTR acct;
	STDSTR branchName;	// ��֧��������
	STDSTR name;		// �ͻ�����
	STDSTR spcashStatus;
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: Submit Order                                                */
/************************************************************************/
#define ORDER_PARAM_EMPTY					""
#define ORDER_PARAM_FUTURE_SPECULATION		"1"	//Ͷ��
#define ORDER_PARAM_FUTURE_ARBITRAGE		"2"	//����
#define ORDER_PARAM_FUTURE_HEDGE			"3"	// �ױ�
#define ORDER_PARAM_HK_ENHANCED_LIMIT			"HKN,0"	//�۹ɶ����걨����ǿ�޼���
#define ORDER_PARAM_ODD_LOT_ENHANCED_LIMIT		"HKO,0"	//�۹�����걨����ǿ�޼���
#define ORDER_PARAM_HK_AUCTION_LIMIT			"HKN,1"	//�۹ɶ����걨�������޼���
#define ORDER_PARAM_HK_ODD_LOT_AUCTION_LIMIT	"HKO,1"	//�۹�����걨�������޼���
#define ORDER_PARAM_CREDIT_SPECIAL_CLASH		"spcash"	//ʹ��ר��ͷ����ȯ����

struct CATSOrderRequest {
	STDSTR acctType;	// �ʽ��˻�����
	STDSTR acct;		// �ʽ��˻�
	STDSTR symbol;		// ��Ĵ��룬�� 600030.SH
	STDSTR tradeSide;/*	��ͨ:
							1	���� �� ����Ʒ����
							2	���� �� ����Ʒ����
						ETF
							F	ETF�깺
							G	ETF���
						������ȯ:
							A	��������
							B	��ȯ����
							C	��ȯ��ȯ
							D	��ȯ����
							E	����ȯ��ȯ���󵣱�Ʒ����
						�ڻ�/��Ȩ:
							FA  ����֣��������룩
							FB  ���ղ֣�����������
							FC  ƽ�ղ֣�ƽ�����룩
							FD  ƽ��֣�ƽ��������
							*/
	STDSTR orderType; /* �Ϻ� ��Ʊ������
							0	�޼۵�
							U	�м۵��������嵵��ʱ�ɽ�ʣ�೷����
							R	�м۵��������嵵��ʱ�ɽ�ʣ��ת�޼ۣ�
						���� ��Ʊ������
							0	�޼۵�
							U	�м۵��������嵵��ʱ�ɽ�ʣ�೷����
							S	�м۵����������ż۸�
							T	�м۵�����ʱ�ɽ�ʣ�೷����
							Q	�м۵������ַ����ż۸�
							V	�м۵���ȫ��ɽ��򳷵���
							*/
	STDSTR priceValue;	// ί�м۸�
	int qty;			// ί����
	STDSTR orderParam;	// �ο������ORDER_PARAM_xxxϵ�к궨�塣һ��A�ɽ��׿ɴ�""
	virtual std::string toString() const;
};

struct CATSSubmitOrderSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;		
	CATSOrderRequest catsOrderRequest;	// �µ�����
	virtual std::string toString() const;
};

struct CATSSubmitOrderSvcResponse : public CATSSvcResponseBase {
	STDSTR orderNo;	// ����ID
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: Cancel Order                                                */
/************************************************************************/
struct CATSCancelOrderSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;	// ��½�����Ϣ
	STDSTR orderNo;		// ����ID
	STDSTR acctType;
	STDSTR acct;
	virtual std::string toString() const;
};

struct CATSCancelOrderSvcResponse : public CATSSvcResponseBase {
	STDSTR origOrderNo;	// ��������ԭʼ����ID
	STDSTR orderNo;		// ����ID
	virtual std::string toString() const;
};

/************************************************************************/
/* Service: Start Algo                                                */
/************************************************************************/
struct CATSStartAlgoSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	STDSTR algoId;			// �㷨����ID����"TWAP", "VWAP"�ȵ�
	STDSTR orderCorrData;	// �����ݻ����ӵ�orderUpdate��Я��
	long long algoData1;
	long long algoData2;
	std::map<std::string, std::string> algoParams; // �㷨����������μ�ÿ���㷨��˵��

	virtual std::string toString() const;
};

struct CATSStartAlgoSvcResponse : public CATSSvcResponseBase {
	STDSTR algoInstanceId;	// �㷨ʵ��ID
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
	STDSTR algoId;	// �㷨����ID����"TWAP", "VWAP"�ȵ�
	STDSTR algoInstanceId;	// ��Ҫֹͣ���㷨ʵ��ID

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
	int currentQty;		// ��ǰ����
	int enabledQty;		// ��������	
	float costPrice;	// �ɱ���

	/* �ڻ���� */
	STDSTR direction;	//�ֲֶ�շ���1-��;2-��ͷ;3-��ͷ  ��Ȩ�ֲ����,"0":Ȩ����|"1":����|"2":���ҷ�
	STDSTR hedgeFlag;	//Ͷ���ױ���־��1-Ͷ��;2-����;3-�ױ�
	STDSTR stockAcct;	//�ɶ�����
	std::string toString() const;
};

struct CATSPosition2QuerySvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	STDSTR acctType;
	STDSTR acct;
	int maxRowNum = 20;	// ÿҳ��������
	int pageNum = 0;	// ҳ��
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
	float beginBalance;		// �ڳ����
	float currentBalance;	// ��ǰ���
	float enabledBalance;	// �������
	float fetchBalance;		// ��ȡ���
	STDSTR moneyType;		// ��������
	STDSTR fundAcct;		// �ʽ��˻�

	/* �ڻ�����Ȩ��� */
	float currMargin;		// ��ǰ��֤���ܶ�
	float dynamicEquity;	// ��̬Ȩ��

	/* ������Ȩ */
	float enableBailBalance;	// ���ñ�֤��  --> ʵʱ��֤��
	float usedBailBalance;		// ���ñ�֤��
	float usedPurBalance;		// ����������
	float enablePurBalace;		// ����������
	STDSTR direction;			//�ֲֶ�շ���1-��;2-��ͷ;3-��ͷ  ��Ȩ�ֲ����,"0":Ȩ����|"1":����|"2":���ҷ�

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
	STDSTR acct; // ���ڶ���topic
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
	STDSTR orderCorrData;	// �����ݻ����ӵ�orderUpdate��Я��
	std::map<std::string, std::string> params;
	long long algoData1;
	long long algoData2;
};

struct CATSStartAlgoSvcResponseEx : public CATSStartAlgoSvcResponse {
	virtual std::string toString() const;
};

struct CATSStartAlgoBasketSvcRequest : public CATSSvcRequestBase {
	CatsAccountData catsAcctData;
	STDSTR algoId;			// �㷨����ID����"TWAP", "VWAP"�ȵ�	
	std::map<std::string, std::string> algoParams; // �㷨�����е�ͨ�ò���������μ�ÿ���㷨��˵��
	std::vector<CATSExtAlgoBusketItem> basket;	// ���Ӳ���������������ÿ���㷨ʵ���Ĳ�ͬ������corrData��

	virtual std::string toString() const;
};

// ��������ӵ����ɹ�����errCodeΪ0������Ϊ1
struct CATSStartAlgoBasketSvcResponse : public CATSSvcResponseBase {
	std::vector<CATSStartAlgoSvcResponseEx*> itemResponses; // ������ÿ���㷨������Ӧ���������е�basket˳����ͬ��
	int basketId;
	int updateIdx;	// ���θ��µ�������Ŀindex.(ÿ�λص�����ֻ�����1������)
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

// ��������ӵ����ɹ�����errCodeΪ0������Ϊ1
struct CATSStopAlgoBasketSvcResponse : public CATSSvcResponseBase {
	std::vector<CATSStopAlgoSvcResponseEx*> itemResponses; // ������ÿ���㷨������Ӧ���������е�basket˳����ͬ��
	int basketId;
	int updateIdx;	// ���θ��µ�������Ŀindex.(ÿ�λص�����ֻ�����1������)
	virtual std::string toString() const;
};


/***************************************************************/
/*  ����Դ����                                                 */
/***************************************************************/
enum CatsMarketDataSource {
	SZ,     //����
	SH,     //�Ϻ�(������Ȩ)
	SHOption,    // �Ϻ���Ȩ

	CFFEX,  //�н���
	CZCE,   //֣����
	SHFE,   //������
	INE,    //�Ϻ�������Դ
	DCE,    //����

	ES,     // ��ʢ,�����ڻ����顣

	HKSZ,   //���ͨ
	HKSH,   //����ͨ
	HKZ,    //��ת��
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
typedef void(*PFCatsSubAssetUpdateRespHandler)(const CATSSubAssetUpdateSvcResponse& resp, void* cbArg); // ����position��fund

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