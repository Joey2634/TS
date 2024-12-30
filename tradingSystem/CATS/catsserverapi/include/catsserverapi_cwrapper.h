#ifndef __CATS_SERVER_API_CWRAPPER_H__
#define __CATS_SERVER_API_CWRAPPER_H__


#if defined(__cplusplus) || defined(c_plusplus)
extern "C"
{
#endif

struct CCATS_CatsAPIParam {
	const char* pcMqIp = NULL;			// CATS��������ߵ�IP��ַ
	unsigned short mqBasePort = 45678;	// CATS��������ߵĻ����˿�
	int reqThreadCount = 1;				// ����������߳���
	int subThreadCount = 1;				// ��������Ϣ(Subscribed Data)���߳���
	int serverTimeoutMs = 10000;		// ����ʱ�ȴ�ʱ��(����)

	bool autoSubAlgoInstanceUpdate = true;	// �Ƿ��Զ������㷨ʵ�����¡���Ϊtrue����startAlgo�л��Զ�����subAlgoInstanceUpdate
	bool autoSubAlgoInstanceExecStat = true;  // �Ƿ��Զ������㷨ִ��ͳ�ơ���Ϊtrue���������㷨�ɹ�����Զ�����subAlgoInstanceExecStat
};


/************************************************************************/
/* Subscribed datas                                                     */
/************************************************************************/
struct CCATS_CatsOrderUpdateData {
	const char* acctType;// �˻�����
	const char* acct;    // �˻�����
	const char* catsAcct; // cats�˻�����
	const char* symbol;  // ��Լ����
	int orderQty; // ����������
	const char* orderPrice;  // �����۸�
	const char* tradeSide; // ��������
	const char* orderType;  // ��������
	const char* orderParam;  // ��������
	const char* orderNo;  // CATS�ڲ���ʾ�Ķ������

	const char* corrType; // corrType
	const char* corrID;   // �ڲ�ID; �㷨���ӵ��У�����AlgoInstanceId

	int filledQty;  // �ɽ�����
	const char* avgPrice;  // �ɽ�����
	int cancelQty; // ȡ������

	const char* lastTime; //������ʱ��  ��ʽΪ hhmmss

						  /*status ����˵��
						  0 �µ�(δ��)
						  1 ���ֳɽ�(δ��)
						  2 ȫ��(�ѽ�)
						  3 ���ֳ���(�ѽ�)
						  4 ȫ��(�ѽ�)
						  5 �ܵ�(�ѽ�)
						  */
	int status;  // ����״̬

	const char* orderTime;  // ί��ʱ��  ��ʽΪhhmmss
	const char* orderDate;  // ί������  ��ʽyyyymmdd
	const char* text;		// ��չ��Ϣ��Ŀǰ�����ܵ�ԭ��

	const char* orderCorrData;  // �㷨ĸ����startAlgo�����д���orderCorrData
	long long algoData1 = 0;
	long long algoData2 = 0;

	int basketId = 0;			 // ʹ��extStartAlgoBasket�����㷨���ӵ�����ID
	int basketItemIndex = 0;

	long long localTs;			// ����ʱ���(ms)�����ڳ�ʱ�ϻ�
};


/************************************************************************/
/* Request and Response parameter structures                            */
/************************************************************************/
struct CCATS_CATSLoginSvcRequest {
	const char* catsAcct;	// cats�˻���
	const char* password;	// cats����
	const char* ip;			// IP��ַ
	const char* macAddr;	// MAC��ַ
	const char* hdSerial;	// Ӳ�����к�
};

struct CCATS_CATSLoginSvcResponse {
	const char* errCode;
	const char* errMsg;
	const char* catsAcct;	// cats�˻���
	const char* catsToken;	// ��½�ɹ�ʱ����������ɵ�token�����û�����������
};


struct CCATS_CATSTradeAccountLoginSvcRequest {
	const char* catsAcct;	// cats�˻���
	const char* catsToken;	// cats�˻���½�ɹ���õ���token��
	const char* acctType;	// �ʽ��˻�����
	const char* acct;		// �ʽ��˻�
	const char* password;	// �ʽ��˻�����
	const char* loginParam;	// ��½����
	const char* ip;			// IP��ַ
	const char* macAddr;	// MAC��ַ
	const char* hdSerial;	// Ӳ�����к�
};

struct CCATS_CATSTradeAccountLoginSvcResponse {
	const char* errCode;
	const char* errMsg;
	const char* acctType;
	const char* acct;
	const char* branchName;	// ��֧��������
	const char* name;		// �ͻ�����
	const char* spcashStatus;
};

struct CCATS_CATSSubmitOrderSvcRequest {
	const char* catsAcct;	// cats�˻���
	const char* catsToken;	// cats�˻���½�ɹ���õ���token��
	const char* acctType;	// �ʽ��˻�����
	const char* acct;		// �ʽ��˻�
	const char* symbol;		// ��Ĵ��룬�� 600030.SH
	const char* tradeSide;/*	��ͨ:
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
	const char* orderType; /* �Ϻ� ��Ʊ������
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
	const char* priceValue;	// ί�м۸�
	int qty;			// ί����
	const char* orderParam;	// �ο������ORDER_PARAM_xxxϵ�к궨�塣һ��A�ɽ��׿ɴ�""
};

struct CCATS_CATSSubmitOrderSvcResponse {
	const char* errCode;
	const char* errMsg;
	const char* orderNo;	// ����ID
};


struct CCATS_CATSStartAlgoSvcRequest {
	const char* catsAcct;	// cats�˻���
	const char* catsToken;	// cats�˻���½�ɹ���õ���token��
	const char* algoId;		// �㷨����ID����"TWAP", "VWAP"�ȵ�
	const char* algoParams; // �㷨����������μ�ÿ���㷨��˵�����ַ���Ϊ<key>=<value>;��ʽ
};

struct CCATS_CATSStartAlgoSvcResponse {
	const char* errCode;
	const char* errMsg;
	const char* algoInstanceId;	// �㷨ʵ��ID
};

struct CCATS_CATSStopAlgoSvcRequest {
	const char* catsAcct;	// cats�˻���
	const char* catsToken;	// cats�˻���½�ɹ���õ���token��
	const char* algoId;	// �㷨����ID����"TWAP", "VWAP"�ȵ�
	const char* algoInstanceId;	// ��Ҫֹͣ���㷨ʵ��ID
};

struct CCATS_CATSStopAlgoSvcResponse {
	const char* errCode;
	const char* errMsg;
};

struct CCATS_CATSFund2QuerySvcRequest {
	const char* catsAcct;	// cats�˻���
	const char* catsToken;	// cats�˻���½�ɹ���õ���token��
	const char* acctType;
	const char* acct;
};

struct CCATS_CATSFund2QuerySvcResponse {
	const char* errCode;
	const char* errMsg;

	float beginBalance;		// �ڳ����
	float currentBalance;	// ��ǰ���
	float enabledBalance;	// �������
	float fetchBalance;		// ��ȡ���
	const char* moneyType;	// ��������
	const char* fundAcct;	// �ʽ��˻�

							/* �ڻ�����Ȩ��� */
	float currMargin;		// ��ǰ��֤���ܶ�
	float dynamicEquity;	// ��̬Ȩ��

								/* ������Ȩ */
	float enableBailBalance;	// ���ñ�֤��  --> ʵʱ��֤��
	float usedBailBalance;		// ���ñ�֤��
	float usedPurBalance;		// ����������
	float enablePurBalace;		// ����������
	const char* direction;		//�ֲֶ�շ���1-��;2-��ͷ;3-��ͷ  ��Ȩ�ֲ����,"0":Ȩ����|"1":����|"2":���ҷ�
};

struct CCATS_CATSPosition2Data {
	const char* symbol;
	int currentQty;		// ��ǰ����
	int enabledQty;		// ��������	
	float costPrice;	// �ɱ���

						/* �ڻ���� */
	const char* direction;	//�ֲֶ�շ���1-��;2-��ͷ;3-��ͷ  ��Ȩ�ֲ����,"0":Ȩ����|"1":����|"2":���ҷ�
	const char* hedgeFlag;	//Ͷ���ױ���־��1-Ͷ��;2-����;3-�ױ�
	const char* stockAcct;	//�ɶ�����
};

struct CCATS_CATSPosition2QuerySvcRequest {
	const char* catsAcct;	// cats�˻���
	const char* catsToken;	// cats�˻���½�ɹ���õ���token��
	const char* acctType;
	const char* acct;
	int maxRowNum;	// ÿҳ��������
	int pageNum;	// ҳ��
};

struct CCATS_CATSPosition2QuerySvcResponse {
	const char* errCode;
	const char* errMsg;
	int positionsLen; /* positions���鳤�� */
	CCATS_CATSPosition2Data* positions; /* �ֲ����������׵�ַ */
};


struct CCATS_CATSSubOrderUpdateSvcRequest {
	const char* catsAcct;	// cats�˻���
	const char* catsToken;	// cats�˻���½�ɹ���õ���token��
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
/* ��ʼ�� */
void CCATS_InitService(CCATS_CatsAPIParam catsParams);

/* CATS�˺ŵ�¼ */
int CCATS_CatsLogin(CCATS_CATSLoginSvcRequest c_req, CCATS_PFCatsLoginRespHandler c_respHandler, void* cbArg);

/* �ʽ��˺ŵ�¼ */
int CCATS_TradeAcctLogin(CCATS_CATSTradeAccountLoginSvcRequest c_req, CCATS_PFCatsTradeAccountLoginRespHandler c_respHandler, void* cbArg);

/* ֱ���µ� */
int CCATS_SubmitOrder(CCATS_CATSSubmitOrderSvcRequest c_req, CCATS_PFCatsSubmitOrderRespHandler c_respHandler, void* cbArg);

/* �����㷨�� */
int CCATS_StartAlgo(CCATS_CATSStartAlgoSvcRequest c_req, CCATS_PFCatsStartAlgoRespHandler c_respHandler, void* cbArg);

/* �����㷨�� */
int CCATS_StopAlgo(CCATS_CATSStopAlgoSvcRequest c_req, CCATS_PFCatsStopAlgoRespHandler c_respHandler, void* cbArg);

/* ��ѯ�˻��ʽ� */
int CCATS_Fund2Query(CCATS_CATSFund2QuerySvcRequest c_req, CCATS_PFCatsFund2QueryRespHandler c_respHandler, void* cbArg);

/* ��ѯ�ֲ��ʽ� */
int CCATS_Position2Query(CCATS_CATSPosition2QuerySvcRequest c_req, CCATS_PFCatsPosition2QueryRespHandler c_respHandler, void* cbArg);

/* ����OrderUpdate */
int CCATS_SubOrderUpdate(CCATS_CATSSubOrderUpdateSvcRequest c_req, CCATS_PFCatsSubOrderUpdateRespHandler c_respHandler, void* cbArg);


/* ����OrderUpdate��������fillCorrData������ʾ�Ƿ���Ҫ����StartAlgo�е�OrderCorrData */
int CCATS_SetOrderUpdateHandler(CCATS_PFCatsReceivedOrderUpdateHandler c_handler, void* cbArg, bool fillCorrData);



#if defined(__cplusplus) || defined(c_plusplus)
}
#endif



#endif // __CATS_SERVER_API_CWRAPPER_H__