#pragma once
#include <vector>

#ifndef _CATS_SUBSCRIBE_MESSAGE_DEFINITION_H
#define _CATS_SUBSCRIBE_MESSAGE_DEFINITION_H

#define int32	int
#define uint32	unsigned int
#define int64	long long

#pragma pack(push)

/* ��1�ֽڶ��� */
#pragma pack (1)

struct CatsRealMarketData {
	char symbol[32];			//��Ʒ���루ÿ�ζ�����
	int32 date;  				//YYYYMMDD
	int32 time;  				//HHMMSSmmm ����ʱ��
	
	unsigned char stopMark;  	//ͣ�Ʊ�־ (1 ͣ��)��ÿ�ζ�����
	int32 cjbs;  				//������� ����ɽ�����
	char futureCode[8]; 		//�ڻ����� �ڻ�����Ʒ�֣���AL IF CU...
	char stkName[16];  			//��Ʊ����

	uint32 lastPrice;  			//��ǰ�۸񣨡�10000��
	uint32 openPrice;  			//���̼ۣ���10000��
	uint32 highPrice;  			//��߼ۣ���10000��
	uint32 lowPrice;  			//��ͼۣ���10000��
	uint32 prevClosePrice;		//�������̣���10000��
	uint32 closePrice;  		//�������̣���10000��
	uint32 highLimited; 		//��ͣ��ۣ���10000��
	uint32 lowLimited; 			//��ͣ��ۣ���10000��
	uint32 settlement; 			//�ڻ����� �����ۣ���10000��
	uint32 prevSettlement; 		//�ڻ����� ǰ����ۣ���10000��

	uint32 bidPrice1;  			//�����1����10000��
	uint32 askPrice1;  			//������1����10000��
	uint32 bidPrice2;  			//�����2����10000��
	uint32 askPrice2;  			//������2����10000��
	uint32 bidPrice3;  			//�����3����10000��
	uint32 askPrice3;  			//������3����10000��
	uint32 bidPrice4;  			//�����4����10000��
	uint32 askPrice4;  			//������4����10000��
	uint32 bidPrice5;  			//�����5����10000��
	uint32 askPrice5;  			//������5����10000��
	uint32 bidPrice6;  			//�����6����10000��
	uint32 askPrice6;  			//������6����10000��
	uint32 bidPrice7;  			//�����7����10000��
	uint32 askPrice7;  			//������7����10000��
	uint32 bidPrice8;  			//�����8����10000��
	uint32 askPrice8;  			//������8����10000��
	uint32 bidPrice9;  			//�����9����10000��
	uint32 askPrice9;  			//������9����10000��
	uint32 bidPrice10;  		//�����10����10000��
	uint32 askPrice10;  		//������10����10000��

	int64 turnOver;  			//�ܳɽ����
	uint32 peRatio1;  			//������� ������ӯ��1����10000��
	uint32 peRatio2;  			//������� ������ӯ��2����10000��
	uint32 prevDelta;  			//�ڻ����� ����ʵ�ȣ���10000��
	uint32 curDelta;  			//�ڻ����� ����ʵ�ȣ���10000��
	uint32 openInterest; 		//�ڻ����� �ֲ���
	uint32 prevOpenInterest;	//�ڻ����� ǰ�ֲ���
	int64 volume;  				//�ܳɽ���

	uint32 bidVol1;  			//������1
	uint32 askVol1;  			//������1
	uint32 bidVol2;  			//������2
	uint32 askVol2;  			//������2
	uint32 bidVol3;  			//������3
	uint32 askVol3;  			//������3
	uint32 bidVol4;  			//������4
	uint32 askVol4;  			//������4
	uint32 bidVol5;  			//������5
	uint32 askVol5;  			//������5
	uint32 bidVol6;  			//������6
	uint32 askVol6;  			//������6
	uint32 bidVol7;  			//������7
	uint32 askVol7;  			//������7
	uint32 bidVol8;  			//������8
	uint32 askVol8;  			//������8
	uint32 bidVol9;  			//������9
	uint32 askVol9;  			//������9
	uint32 bidVol10;  			//������10
	uint32 askVol10;  			//������10

	uint32 curVol;				//����
	int32 IOPV;					//IOPVԤ����ֵ����10000��
	int32 yieldToMaturity;		//���������ʣ���10000��

	int32 accer; //����  (eg. 10000��ʾ1%)
	uint32 weightedAvgBidPrice; //��Ȩƽ��ί��۸�
	uint32 weightedAvgAskPrice; //��Ȩƽ��ί���۸�
	int status;     //״̬��������ο��ֵ��
	char  reserved[20]; //reserved for later

	std::string toString() const;
} ;

#pragma pack(pop)

struct CatsPositionUpdateData {
	std::string acctType;
	std::string acct;

	std::string symbol;
	long long currentQty;    // ��ǰ����
	long long enabledQty;    // ��������
	float incomeBalance;    // ӯ�����

								   /* ֤ȯ��� */
	float costPrice;        // �ɱ���  ��ȨΪ�ֲֳɱ����ۻ���+������-�ۻ���-��������
	float lastPrice;        // ���¼�
	float marketValue;        // �ο���ֵ
	std::string stockName;        // ֤ȯ���

	long long frozenQty;    //��������
	long long unfrozenQty;    //�ⶳ����

	long long beginQty;        //�ڳ�����
	long long realBuyQty;    //��������ɽ����� �ݲ�֧��
	long long realSellQty;    //���������ɽ����� �ݲ�֧��

								/* �ڻ���� */
	std::string direction;         //�ֲֶ�շ���1-��;2-��ͷ;3-��ͷ  ��Ȩ�ֲ����,"0":Ȩ����|"1":����|"2":���ҷ�
	std::string positionDate;    //�ֲ��������ͣ�1-���ճֲ�;2-��ʷ�ֲ�
	std::string hedgeFlag;       //Ͷ���ױ���־��1-Ͷ��;2-����;3-�ױ�
	long long ydPosition;     //���ճֲ�
	long long longFrozen;     //��ͷ����
	long long shortFrozen;    //��ͷ����
	float useMargin;        //ռ�õı�֤��
	float positionCost;     //�ֲֳɱ�
	float positionProfit;     //�ֲ�ӯ��
	float closeProfit;      //ƽ��ӯ��

	long long openVolume;     //��������
	float openAmount;       //���ֽ��
	long long closeVolume;    //ƽ������
	float closeAmount;      //ƽ�ֽ��
	long long todayPosition;  //���ճֲ�

	float closeProfitByDate; //���ն���ƽ��ӯ��
	float closeProfitByTrade;//��ʶԳ�ƽ��ӯ��

									/* ��Ȩ��� */
	float holdQty;        // ��������������ί��δ�ɽ����֣�
	float realOpenQty;        // �񿪲ֲֳ���
	float realDropQty;    // ��ƽ�ֲֳ���
	float entrustDropQty;    // ��ƽ��ί����
	float openAvgPrice;    // ���־���
	float buyAvgQty;        // �������
	float avgIncomeBalance;// ʵ��ӯ��
	float exerciseIncome;    // ��Ȩӯ�����
	float dutyUsedBail;    // �����ռ�ñ�֤��

	std::string toString() const;
};

struct CatsFundUpdateData {
	std::string acctType;
	std::string acct;

	float currentBalance;    // ��ǰ���ڻ�����׼����
	float enabledBalance;    // �������
	std::string moneyType;   // ��������

	/* ֤ȯ��� */
	std::string fundAcct;  // �ʽ��˻�

	float beginBalance;    //�ڳ����
	float fetchBalance;    //��ȡ���
	float frozenBalance;   //������
	float unfrozenBalace;  //�ⶳ���

	/* �ڻ�����Ȩ��� */
	float deposit;         //�����
	float withdraw;        //������
	float frozenMargin;    //���ᱣ֤��
	float frozenCash;      //������ʽ�
	float currMargin;      //��ǰ��֤���ܶ�
	float closeProfit;     //ƽ��ӯ��
	float positionProfit;  //�ֲ�ӯ��

	float preBalance;        //�ϴν���׼����
	float preMargin;        //�ϴ�ռ�õı�֤��
	float preDeposit;        //�ϴδ���
	float preCredit;        //�ϴ����ö��
	float preMortgage;        //�ϴ���Ѻ���
	float mortgage;        //��Ѻ���
	float credit;            //���ö��
	float frozenCommission;//����������
	float commission;        //������
	float dynamicEquity;    //��̬Ȩ��

	/* ��Ȩ��� */
	float optionCloseProfile;//��Ȩƽ��ӯ��

	//������Ȩ
	float enableBailBalance;    //���ñ�֤��  --> ʵʱ��֤��
	float usedBailBalance;     //���ñ�֤��
	float usedPurBalance;     //����������
	float enablePurBalace;     //����������

	float netBuyAmount;        //�������
	float withdrawnRate;        //������
	float filledRate;            //�ɽ���
	float rejectedRate;        //�ܵ���

	virtual std::string toString() const;
};

struct CatsOrderUpdateData {
	std::string acctType;// �˻�����
	std::string acct;    // �˻�����
	std::string catsAcct; // cats�˻�����
	std::string symbol;  // ��Լ����
	int orderQty; // ����������
	std::string orderPrice;  // �����۸�
	std::string tradeSide; // ��������
	std::string orderType;  // ��������
	std::string orderParam;  // ��������
	std::string orderNo;  // CATS�ڲ���ʾ�Ķ������

	std::string corrType; // corrType
	std::string corrID;   // �ڲ�ID; �㷨���ӵ��У�����AlgoInstanceId

	int filledQty;  // �ɽ�����
	std::string avgPrice;  // �ɽ�����
	int cancelQty; // ȡ������

	std::string lastTime; //������ʱ��  ��ʽΪ hhmmss

	/*status ����˵��
	0 �µ�(δ��)
	1 ���ֳɽ�(δ��)
	2 ȫ��(�ѽ�)
	3 ���ֳ���(�ѽ�)
	4 ȫ��(�ѽ�)
	5 �ܵ�(�ѽ�)
	*/
	int status;  // ����״̬

	std::string orderTime;  // ί��ʱ��  ��ʽΪhhmmss
	std::string orderDate;  // ί������  ��ʽyyyymmdd

	std::string orderCorrData;  // �㷨ĸ����startAlgo�����д���orderCorrData
	long long algoData1 = 0;
	long long algoData2 = 0;

	int basketId = 0;			 // ʹ��extStartAlgoBasket�����㷨���ӵ�����ID
	int basketItemIndex = 0;

	long long localTs;			// ����ʱ���(ms)�����ڳ�ʱ�ϻ�
	virtual std::string toString() const;
};


struct CatsAlgoInstanceUpdateData {
	virtual ~CatsAlgoInstanceUpdateData() {};
	std::string algoId; //����id
	std::string algoInstanceId;  //ʵ��id
	std::string catsAcct;  //cats�˺�
	bool stopped; //�Ƿ��Ѿ�ֹͣ��true��ʾ��ʵ���Ѿ�ֹͣ������δֹͣ
	std::string message;  //��Ϣ
	std::map<std::string, std::string> params;  //���Բ���
	int startTime;   //���Կ�ʼʱ�䣬��ʽΪ HHMMSSsss, eg:102433700
	int stopTime;    //���Խ���ʱ�䣬��ʽΪ HHMMSSsss, eg:102433700
	int date;       //���ڣ����һ�θ�������  ��ʽΪYYYYMMDD         eg:20190604
	int time;      //ʱ�䣬 ���һ�θ���ʱ�� ��ʽΪ HHMMSSsss, eg:102433700

	/* custom datas */
	std::string orderCorrData;
	long long algoData1 = 0;
	long long algoData2 = 0;

	/* ����ֻ�����㷨���ӻ��õ� */
	int basketId = 0;	// ʹ��extStartAlgoBasket�����㷨���ӵ�����ID
	int basketItemIndex = 0;

	long long localTs;			// ����ʱ���(ms)�����ڳ�ʱ�ϻ�
	virtual std::string toString() const;
};


struct CatsAlgoInstanceUpdateDataEx : public CatsAlgoInstanceUpdateData {
	virtual ~CatsAlgoInstanceUpdateDataEx() {};

	virtual std::string toString() const;

	void assignFromCatsAlgoInstanceUpdateData(const CatsAlgoInstanceUpdateData& o);
};


struct CatsBasketAlgoInstanceUpdateData {
	int basketId = 0;		// ����ID
	size_t basketSize = 0;	// ���Ӵ�С
	int updateIdx = 0;		// ���θ��µ�item����
	std::vector<CatsAlgoInstanceUpdateDataEx*> itemUpdateDatas; // ��Ӧ�������algoInstanceUpdate

	virtual std::string toString() const;
};

struct CatsAlgoInstanceExecStatData {
	std::string algoId;   //����id
	std::string algoInstanceId;  //����ʵ��id
	std::string acctType;  // �˻�����
	std::string acct;  // �˻�����
	std::string symbol;  // ��Լ����

	std::string tradeSide;  // ���׷���
	int targetQty;  // ����Ŀ����
	int orderQty;   // ����������
	std::string orderPrice;   // �µ��۸�
	int filledQty;   // �ɽ���

	std::string avgPrice;   // �ɽ�����
	int cancelQty;   // ȡ����
	int rejectQty;   // �ܾ���
	int pendingQty; // �ҵ���
	int orderCnt;   // �µ����� �������µ��ɹ�����ʧ��,ֻҪ�����µ��͵���1��

	int filledCnt; //�ɽ�����
	int cancelCnt; //��������
	int rejectCnt; //�ܵ�����
	std::string lastOrderNo; //���һ���������
									  /* lastOrderStatus ����˵��
									  0 �µ�(δ��)
									  1 ���ֳɽ�(δ��)
									  2 ȫ��(�ѽ�)
									  3 ���ֳ���(�ѽ�)
									  4 ȫ��(�ѽ�)
									  5 �ܵ�(�ѽ�)
									  6 ��̨�ܾ����µ���ʱ��ԭ�򣬻�����ԭ���µĴ���״̬�����糷��ʱ���صĶ����Ų���ԭ�ȵĵ��ţ�
									  999  ÿ���㷨ʵ��ִ��ͳ�Ƴ�ʼ����һ��ֵ����һ��ִ��ͳ�Ƶ����Ϳ���Ϊ��ֵ��
									  */
	int lastOrderStatus; //���һ������״̬

	std::string lastOrderType;  //���һ����������
	std::string lastOrderPrice;	//���һ�������۸�
	std::string lastError;		//��������Ϣ
	std::string remark;

	/* custom datas */
	std::string orderCorrData;
	long long algoData1 = 0;
	long long algoData2 = 0;

	int basketId = 0;				// ʹ��extStartAlgoBasket�����㷨���ӵ�����ID
	int basketItemIndex = 0;

	long long localTs;			// ����ʱ���(ms)�����ڳ�ʱ�ϻ�
	virtual std::string toString() const;
};

#endif /* _CATS_SUBSCRIBE_MESSAGE_DEFINITION_H */

