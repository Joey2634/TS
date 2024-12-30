# WIND数据库表名 14
table_names = ['AindexDescription', 'AIndexEODPrices', 'AIndexIndustriesEODCITICS', 'AIndexMembers',
               'AIndexMembersWIND', 'AIndexWindIndustriesEOD', 'AShareBalanceSheet', 'AShareCalendar',
               'AShareCapitalization', 'AShareConseption', 'AShareDescription', 'AShareEODDerivativeIndicator',
               'AShareEODPrices', 'AShareFinancialIndicator', 'AShareFreeFloat', 'AShareIndustriesClass',
               'AShareIndustriesClassCITICS', 'AShareIndustriesCode', 'AShareIPO', 'AShareMoneyFlow',
               'AShareSECNIndustriesClass', 'AShareST', 'AShareSWIndustriesClass',
               'AShareTradingSuspension', 'ASWSIndexEOD', 'CBIndexEODPrices', 'CBIndexMembers', 'CBondEODPrices',
               'CBondFuturesEODPrices',
               'CBondIBRMBMonDMarQuotation', 'CCommodityFuturesEODPrices', 'CFutureIndexEODPrices', 'CFuturesContPro',
               'CfuturesContractMapping',
               'CFuturesDescription', 'CGoldSpotEODPrices', 'ChinaClosedFundEODPrice', 'ChinaMFPerformance',
               'ChinaMutualFundNAV',
               'ChinaMutualFundShare', 'ChinaOptionContpro', 'ChinaOptionDescription', 'ChinaOptionEODPrices',
               'CIndexFuturesEODPrices',
               'FXRMBMidRate', 'GlobalIndexEOD', 'HKIndexDescription', 'HKIndexEODPrices', 'HKshareEODPrices',
               'HKStockIndexCode',
               'HKStockIndexMembers', 'IBFXEODPrices', 'IndexContrastSector', 'ShiborPrices', 'WindCustomCode',
               'BRK_DAY_TXN_DATA_TO_AI', 'COMMODITIESKLINE', 'HKSTOCKHSINDEXWEIGHT', 'ASHAREEODINDUSTRIES',
               'ASarePlanTrade', 'AShareBlockTrade', 'AShareCashFlow', 'AShareCompRestricted', 'AShareDividend',
               'AShareIncome',
               'AShareMjrHolderTrade', 'AshareStockRepo', 'ChinaMutualFundBenchMark', 'ChinaMutualFundDescription',
               'HKEXCalendar',
               'HKShareDescription', 'HKShareIssuance', 'HKStockHSIndustriesMembers', 'HKStockWindIndustriesMembers',
               'HKTransactionStatus',
               'CMoneyMarketDailyFIncome', 'HKSCMembers', 'CFuturesmarginratio', 'AShareEnergyindexADJ',
               'AshareintensitytrendADJ',
               'AShareswingReversetrendADJ', 'security_industry_gics', 'foreign_sec_eod']

# 1.字段TRADE_DT
table_trade_dt = ['AIndexEODPrices', 'AIndexIndustriesEODCITICS', 'AIndexWindIndustriesEOD',
                  'AShareEODDerivativeIndicator', 'AShareEODPrices', 'AShareMoneyFlow',
                  'ASWSIndexEOD', 'CBIndexEODPrices', 'CBondEODPrices',
                  'CBondFuturesEODPrices', 'CBondIBRMBMonDMarQuotation', 'CCommodityFuturesEODPrices',
                  'CFutureIndexEODPrices', 'CGoldSpotEODPrices', 'ChinaClosedFundEODPrice', 'ChinaMFPerformance',
                  'ChinaOptionEODPrices', 'CIndexFuturesEODPrices',
                  'FXRMBMidRate', 'GlobalIndexEOD', 'HKIndexEODPrices', 'HKshareEODPrices',
                  'IBFXEODPrices', 'ShiborPrices', 'HKSTOCKHSINDEXWEIGHT', 'ASHAREEODINDUSTRIES',
                  'AShareBlockTrade', 'CFuturesmarginratio', 'AShareEnergyindexADJ',
                  'AshareintensitytrendADJ', 'AShareswingReversetrendADJ',
                  'ASharePlacementDetails', 'ASharePledgetrade', 'ChinaETFPchRedmMembers',
                  'AIndexValuation', 'SIndexPerformance', 'AIndexHS300FreeWeight', 'ASWSIndexCloseWeight',
                  'MSCICoreAPEODPrices', 'ChinaMutualFundBenchmarkEOD', 'ChinaMFPerformance', 'CMFFixedinvestmentRate',
                  'FIndexPerformance'
                  ]

# 2.S_CON_INDATE
table_members = ['AIndexMembers', 'AIndexMembersWIND', 'CBIndexMembers', 'HKStockIndexMembers']

# 3.ANN_DT
table_ann_dt = ['AShareBalanceSheet', 'AShareCapitalization', 'AShareFinancialIndicator', 'AShareFreeFloat'
    , 'AShareIPO', 'ChinaMutualFundNAV', 'AShareCashFlow', 'AShareIncome', 'AShareMjrHolderTrade'
    , 'AshareStockRepo', 'AShareFreeFloat', 'IPOInquiryDetails']

# 4.ENTRY_DT  REMOVE_DT
table_entry_dt = ['AShareConseption', 'AShareIndustriesClass', 'AShareIndustriesClassCITICS',
                  'AShareSECNIndustriesClass'
    , 'AShareST', 'AShareSWIndustriesClass', 'HKStockHSIndustriesMembers', 'HKStockWindIndustriesMembers'
    , 'HKSCMembers']

# 5.TRADE_DAYS
table_trade_days = ['AShareCalendar', 'HKEXCalendar']

# 6.TRADE_DATE
table_trade_date = ['COMMODITIESKLINE', 'security_industry_gics', 'foreign_sec_eod']

# 7.S_INFO_LISTDATE
table_listdate = ['AindexDescription', 'AShareDescription', 'CFuturesContPro', 'CFuturesDescription',
                  'HKIndexDescription'
    , 'AShareCompRestricted', 'HKShareDescription']

table_occurrence_date = ['AShareEventdateinformation']
table_report_period = ['AShareinstHolderDerData', 'CFundPortfoliochanges']
table_est_dt = ['AIndexConsensusData', 'AIndexConsensusRollingData', 'AShareConsensusData',
                'AShareConsensusRollingData']
table_f_est_date = ['ChinaMutualFundPosEstimation']
table_price_date = ['ChinaMutualFundNAV']
table_f_prt_enddate = ['ChinaMutualFundStockPortfolio']
table_rating_date = ['AShareStockRatingConsus']

daily_data = ['AIndexEODPrices', 'AShareEODPrices', 'ChinaClosedFundEODPrice', 'HKIndexEODPrices',
                 'HKshareEODPrices', 'AIndexWindIndustriesEOD', 'AIndexIndustriesEODCITICS', 'ASWSIndexEOD',
                 'ChinaOptionEODPrices', 'CBondFuturesEODPrices', 'CIndexFuturesEODPrices', 'CCommodityFuturesEODPrices',
                 'AShareEODDerivativeIndicator', 'AShareTechIndicators', 'AShareEnergyindexADJ', 'AshareintensitytrendADJ',
              'AShareL2Indicators', 'AShareswingReversetrendADJ', 'AShareTechIndicators', 'AShareYield',
              'PITFinancialFactor', 'RevenueTechnicalFactor', 'TurnoverTechnicalFactor', 'SIndexPerformance']

# 01 中国A股数据库
# 01-01 中国A股-基础信息
wind_0101 = ['AShareCNIIndustriesClass', 'AShareConseption', 'AShareDescription', 'AShareIndustriesClass',
             'AShareIntroduction', 'AShareIPOClass', 'AShareIPORoadshow', 'AShareNEIndustriesClass',
             'AShareOwnership', 'ASharePreviousENName', 'ASharePreviousName', 'AShareRegional',
             'AShareSECIndustriesClass', 'AShareSECNIndustriesClass', 'AShareSSEIndustriesClass', 'AShareSTIBConceptualPlate',
             'AShareSTIBEmergingIndustries', 'AShareSTIBInterest', 'CompanyPreviousName', 'SHSCMembers',
             'SHSCSELLMembers', 'SZSCMembers', 'SZSCSELLMembers']

# 01-02 中国A股-行情交易数据
wind_0102 = ['AShareAfterEODPrices', 'AShareBlockTrade', 'AShareCalendar', 'AShareEODPrices',
             'AShareEXRightDividendRecord', 'AShareMarketOverallindex', 'AShareStrangeTrade', 'AShareStrangeTradedetail',
             'AShareTradingSuspension']

# 01-03 中国A股-行情衍生数据  table/year/code
wind_0103 = ['AShareEnergyindex', 'AShareEnergyindexADJ', 'AShareEODDerivativeIndicator', 'Ashareintensitytrend',
             'AshareintensitytrendADJ', 'AShareL2Indicators', 'AShareMoneyFlow', 'AShareMonthlyYield',
             'AShareswingReversetrend', 'AShareswingReversetrendADJ', 'AShareTechIndicators', 'AShareWeeklyYield',
             'AShareYield']

# 01-04 中国A股-融资融券数据
wind_0104 = ['AShareMarginShortFeeRate', 'AShareMarginSubject', 'AShareMarginTrade', 'AShareMarginTradeSum']

# 01-05 中国A股-权益数据 , 'AShareCompRestricted'500w+ , 'AShareEventdateinformation'300w+, 'ASharePlacementDetails'500w+
# , 'IPOInquiryDetails'500w+
wind_0105 = ['AShareAdmPermitSchedule', 'AShareAgency', 'AShareCapitalization',
             'AShareDividend', 'AShareDivisionElimination', 'AShareEquityDivision',
             'AShareFreeFloat', 'AShareFreeFloatCalendar', 'AShareFundUsing', 'AShareIPO',
             'AShareIPOAmount', 'AShareIssueCommAudit', 'AShareLeadUnderwriter',
             'ASharePlacementInfo', 'AShareRightIssue', 'AShareSEO', 'AShareSTIBHolderVote',
             'AShareSTIBInvestmentIending', 'AshareStockRepo', 'AShareWinning', 'IECMemberList',
             'IPOCompRFA', 'IPODeclareDisclosureDate', 'AShareCompRestricted' , 'AShareEventdateinformation',
             'ASharePlacementDetails', 'IPOInquiryDetails']
# ['NOPUBLICSTOCKCompRFA']

# 01-06 中国A股-财务数据 'AShareBalanceSheet',字段多 , 'AShareCashFlow', 'AShareIncome'
wind_0106 = ['AShareAccountingChange', 'AShareANNFinancialIndicator', 'AShareAuditDescription', 'AShareAuditOpinion',
              'AShareBankIndicator', 'AShareFinancialderivative',
             'AShareFinancialIndicator', 'AShareFinSegmentinfo', 'AShareIBrokerIndicator',

             'AShareInsuranceIndicator', 'AShareIssuingDatePredict', 'AShareMonthlyReportsofBrokers', 'AShareProfitExpress',
             'AShareProfitNotice', 'AShareReportperiodindex', 'AShareTTMAndMRQ', 'AShareTTMHis',
             'BankLoan5LClassification', 'CBankDepositStructure', 'CBankLoanStructure',
             'AShareBalanceSheet', 'AShareCashFlow', 'AShareIncome']

# 01-07 中国A股-财务附注
wind_0107 = ['AshareAccountsReceivable', 'AShareAdvancePayment', 'AShareAdvanceReceipt', 'AshareAgingstructure',
             'AshareBuyRESaleFINAssets', 'AShareCapitalSurplus', 'AShareCashADepositsWithCB',
             'AShareCompensationPayable',
             'AShareDeferredTaxAssets', 'AShareDeferredTaxLiability', 'AShareDevaluationPreparation', 'AShareEMBValueASSESSResults',
             'AShareEMBValueChangeANAL', 'AShareEngineering', 'AShareFairValueChange', 'AShareFinancialEXP',
             'AShareFinancialExpense', 'AShareFinancialSecurities', 'AShareFixedAssets', 'AShareGoodwill',
             'AShareGoodwillDEValue', 'AShareGovernmentgrants', 'AShareGovernmentSubsidyDEFIN', 'AshareGuaranteestatistics',
             'AShareIMPAIRLossAssets', 'AShareIncomeTax', 'AShareIncomeTaxADJProc', 'AShareIntangibleAssets',
             'AShareInterestRateRisk', 'AShareInterestReceivable', 'AShareINTPayable', 'AShareINVEFallPriceRES',
             'AshareInventorydetails', 'AShareInvestmentIncome', 'AShareInvestmentRealEstate', 'AShareKindsOveLoansTerm',
             'AShareLiquidityRisk', 'AShareLoandetails', 'AShareLoansOTHBanks', 'AShareLTEQYInvest',
             'AShareLTLoan', 'AShareLTPayables', 'AShareLTPrepaidEXP', 'AshareMajorreceivables',
             'AShareManagementExpense', 'AshareMonetaryfundOfProj', 'AshareMonetaryfunds', 'AShareNonCurrentLiabilities1Y',
             'AShareNONOPEREXP', 'AShareNONOPERREV', 'Asharenonprofitloss', 'AShareNotesPayable',
             'AShareNotesReceivable', 'AShareOPERREVAndCOST', 'AshareOtherAccountsreceivable', 'AShareOtherCOMPREHIncome',
             'AShareOtherCurrentAssets', 'AShareOtherCurrentLiabilities', 'AShareOtherincome', 'AShareOtherNoncurrentAssets',
             'AShareOtherNoncurrentLIAB', 'AShareOtherPayables', 'AshareOtherreceivables', 'AshareProvisionbaddebts',
             'AShareRDexpenditure', 'AShareRDExpense', 'AShareRelatedclaimsdebts', 'AShareSaleExpense',
             'AShareSalesSegment', 'AShareSalesSegmentMapping', 'AShareSensitAnalysis', 'AShareSTLoan',
             'AShareSurplusReserve', 'AShareTaxesPay', 'AshareTaxespayable', 'AShareTaxrate',
             'AShareTaxSurcharge', 'AShareTotalInvest', 'AShareTrustinvestmentTOT', 'AShareUndistributedProfit',
             'FinNotesAccountsPayable', 'FinNotesDetail', 'Top5ByAccountsReceivable', 'Top5ByLongTermBorrowing',
             'Top5ByOperatingIncome']
# ['FinancialNoteCategory']

# 01-08 中国A股-公司治理
wind_0108 = ['AShareEsopDescription', 'AShareEsopTradingInfo', 'AShareIncDescription', 'AShareIncExecQtyPri',
             'AShareIncExercisePct', 'AShareIncQuantityDetails', 'AShareIncQuantityPrice', 'AShareManagement',
             'AShareManagementHoldReward', 'ASharePovertyAlleviationData', 'AShareStaff', 'AShareStaffStructure']

# 01-09 中国A股-股东数据 , 'AShareinstHolderDerData'400w+ , 'ASharePledgetrade'400w
wind_0109 = ['AEquFroPleInfoRepperend', 'ASarePlanTrade', 'AShareEquFroInfo', 'AShareEquityPledgeInfo',
             'AShareEquityRelationships', 'AShareFloatHolder', 'AShareHolderNumber', 'AShareInsideHolder',
             'AShareInsiderTrade', 'AShareMajorHolderPlanHold', 'AShareMjrHolderTrade',
             'ASharePledgeproportion'
    , 'AShareinstHolderDerData', 'ASharePledgetrade']

# 01-10 中国A股-重大事件, 'AShareMajorEvent'
wind_0110 = ['AShareCapitalOperation', 'AShareCOCapitaloperation', 'AShareCompanyHoldShares', 'AShareCorporateFinance',
             'AShareGuarantee', 'AShareholdersmeeting', 'AShareholdersmeetingVotes', 'AShareholdingoperate',
             'AShareIllegality', 'AShareInternetvoting', 'AshareOfferforoffer',
             'AShareOperationEvent', 'AShareProsecution', 'AShareRalatedTrade', 'AShareRegInv',
             'AshareRestructuringEvents', 'AShareST', 'AShareStockSwap'
    , 'AShareMajorEvent']

# 01-11 中国A股-并购重组
wind_0111 = ['CommitProfit', 'CommitProfitSummary', 'MergerAgency', 'MergerEvent',
             'MergerIntelligence', 'MergerParticipant']
# ['RelatedEvent']

# 01-12 中国A股-机构调研, 'AShareISQA'中文多
wind_0112 = ['AShareCompDisclosureResults', 'AshareISActivity', 'AShareISParticipant'
    , 'AShareISQA']

# 01-13 中国A股-优先股
wind_0113 = ['CPSAgency', 'CPSCapitalization', 'CPSDescription', 'CPSDividend',
             'CPSEODPrices', 'CPSIssuerRating', 'CPSPlacementDetails', 'CPSRating',
             'CPSSEO']

# 01-14 中国A股-股票风格
wind_0114 = ['AShareStyleCoefficient', 'ShareFundStyleThreshold']

# 01-15 中国A股-指数数据, 'ChinaETFPchRedmMembers'4000w
wind_0115 = ['AIndexDescription', 'AIndexEODPrices', 'AIndexMembers', 'AIndexMembersWIND',
             'AIndexWindIndustriesEOD', 'ChinaETFPchRedmList'
    , 'ChinaETFPchRedmMembers']

# 01-16 中国A股-指数衍生数据 后2 1500w
wind_0116 = ['AIndexFinancialderivative', 'AIndexValuation', 'SIndexPerformance']

# 01-17 中国A股-专题统计报表--- 灰
wind_0117 = ['IPOInformation', 'LiberateStageStatistics', 'MarginTradingScale', 'SEOInformation',
             'StockTradingScale', 'TransactionStatistics']

# 01-97 中国A股-CCRQM数据--- 灰
wind_0197 = ['TEJCreditRatingDescription', 'TEJCreditRatingMaster', 'TEJDailyNews', 'TEJRiskIndicator']

# 01-98 中国A股第三方数据
wind_0198 = ['AIndexAlternativeMembers', 'AIndexCSI1000Weight', 'AIndexCSI100Weight', 'AIndexCSI300DivdPitWeightPrice',
             'AIndexCSI500DivdPitWeightPrice', 'AIndexCSI500Weight', 'AIndexCSI700Weight', 'AIndexCSI800Weight',
             'AIndexHS300CloseWeight', 'AIndexHS300FreeWeight', 'AIndexHS300Weight', 'AIndexIndustriesEODCITICS',
             'AIndexMembersCITICS', 'AIndexMembersCITICS2', 'AIndexMembersCITICS3', 'AIndexSSE180Weight',
             'AIndexSSE50Weight', 'AMSCIIndexEOD', 'AShareCSIndustriesClass', 'AShareGICSIndustriesClass',
             'AShareIndustriesClassCITICS', 'AShareSWIndustriesClass', 'ASPCITICIndexEOD', 'ASWSIndexCloseWeight',
             'ASWSIndexEOD', 'CSIAggressiveStrategyIndexEOD', 'CSIConstantRiskStgyIndexEOD', 'CSIDividendIndexWeight',
             'CSIEquityandBondRiskIndexEOD', 'CSIInvestmentClockIndexEOD', 'CSIModerateStrategyIndexEOD',
             'CSIMultiAssetRiskIndexEOD',
             'CSIndusAnalysis', 'CSIOptionStrategyIndexEOD', 'CSIPA2025RetirementIndexEOD',
             'CSIPA2035RetirementIndexEOD',
             'CSIPA2045RetirementIndexEOD', 'CSISplementaryPensionIndexEOD', 'CSITargetDate2035IndexEOD',
             'CSITargetDate2045IndexEOD',
             'CSITargetDate2055IndexEOD', 'CSIYHGrowth3037IndexEOD', 'CSIYHGrowth7030IndexEOD',
             'CSIYHValue3070IndexEOD',
             'CSIYHValue7030IndexEOD', 'MSCICoreAPEODPrices', 'MSCIEODPrices', 'MSCIIndexWeight',
             'SSEEquityandBondRiskIndexEOD', 'SWIndexMembers', 'ThirdPartyStockIndexEOD']
# ['AIndexCSI1000CloseWeight', 'AIndexCSI500CloseWeight', 'AIndexCSI500WeightWeight', 'AIndexCSI800CloseWeight',
#     'AIndexCSI800GrowthWeight', 'AIndexCSI800ValueWeight', 'AIndexCSI800WeightWeight', 'AIndexCSIAllINDWeight',
#     'AIndexCSIEmergingCompWeight', 'AIndexCSIHealthCareWeight', 'AIndexCSISEDWeight', 'AIndexCSITECH100Weight',
#     'AIndexCSITECH50Weight', 'AIndexCSITMT150WeightWeight', 'AIndexDIVDLowVolWeight', 'AIndexSolarPowerWeightCITICS',
#     'AIndexSSE50DivdPitWeightPrice', 'AIndexSSEDividendWeight', 'AIndexSSESE100Weight', 'AshareMSCIMembers',
#     'ASPCITICIndexWeight', 'ChiNextLCIndexWeight', 'ChiNextPRICEIndexWeight', 'CITICSIndexMembers',
#     'CNIConsumer100IndexWeight', 'CSI300HighBetaIndexWeight', 'CSI300RealEstateEWIndexWeight', 'CSIAgricultureIndexWeight',
#     'CSIASConStaplesIndexWeight', 'CSIASConsumerIndexWeight', 'CSIASFinancialsIndexWeight', 'CSIASHealthCareIndexWeight',
#     'CSIASInvestmentBBIndexWeight', 'CSIASRealEstateIndexWeight', 'CSIASTransIndexWeight', 'CSIBanksIndexWeight',
#     'CSICoalEWIndexWeight', 'CSICommodityEquityIndexWeight', 'CSIComputerIndexWeight', 'CSIDividendLowWaveIndexWeight',
#     'CSIElectronicsIndexWeight', 'CSIEPIndustryIndexWeight', 'CSIFoodBeverageIndexWeight', 'CSIHealthCare100IndexWeight',
#     'CSIHighEndEMIndexWeight', 'CSILeisureENTIndexWeight', 'CSILiquorIndexWeight', 'CSIMobileInternetIndexWeight',
#     'CSIndexDivisor', 'CSIndexMembersCorpActions', 'CSIndexmembersforecast', 'CSINFTargetDate2025IndexEOD',
#     'CSINFTargetDate2035IndexEOD', 'CSINFTargetDate2045IndexEOD', 'CSISECandINSIndexWeight', 'MSCIAONSHOREHEALTHEODPrices',
#     'MSCICAInclusionRMBEODPrices', 'MSCICAInclusionRMBWeight', 'MSCICHINAAEODPrices', 'MSCICHINAAOFFSHOREPrices',
#     'MSCICHINAAWeight', 'MSCICompanyQualityIndexWeight', 'MSCICoQualityIndexEODPrices', 'MSCICoreAPWeight',
#     'MSCIESGUniversalEODWeight', 'MSCIHKConectSouthbdValuePrices', 'MSCIHKConectSouthbdValueWeight', 'MSCILowWaveIndexEODPrices',
#     'MSCILowWaveIndexWeight', 'MSCIRMBESGUniversalEODPrices', 'MSCIUSDESGUniversalEODPrices', 'SSEConsumer80IndexWeight']

# 01-99 FileSync配置表--- 灰
wind_0199 = ['FileSyncTimeSchedule']


# 02 中国A股一致预测
# 02-01 中国A股-万得一致预测  未存
wind_0201 = ['AIndexConsensusData', 'AIndexConsensusRollingData', 'AShareConsensusData', 'AShareConsensusindex',
             'AShareConsensusRollingData', 'AShareStockRatingConsus']

# 02-02 中国A股-盈利预测明细 'AShareEarningEst',
wind_0202 = ['AShareIndusRating', 'AShareIPOPricingForecast', 'AShareStockRating'
             ,'AShareEarningEst']


# 04 中国共同基金数据库
# 04-01 共同基金-基础信息
wind_0401 = ['CFundCompanyPreviousName', 'CFundFactionalStyle', 'CFundPchRedm', 'CFundPreviousName',
             'CFundStyleCoefficient', 'CFundStyleThreshold', 'ChinaFeederFund', 'ChinaGradingFund',
             'ChinaMutualFundBenchMark', 'ChinaMutualFundDescription', 'ChinaMutualFundManager', 'ChinaMutualFundSector',
             'ChinaMutualFundSuspendPchRedm', 'ChinaMutualFundTrackingIndex', 'CMFCodeAndSName', 'CMFConseption',
             'CMFDESCChange', 'CMFIndustryplate', 'CMFPreferentialFee', 'CMFProportionOfInveObj',
             'CMFRiskLevel', 'CMFSECClass', 'CMFSellingAgents', 'CMFSubredFee',
             'CMFThemeConcept', 'CMFundOperatePeriod', 'CMoneyMarketFSCarryOverm', 'CPFundDescription',
             'FinancialQualification', 'LOFDescription']
# ['ChinaMutualFundAgency']

# 04-02 基金公司-基本资料
wind_0402 = ['FundCompanyInsideHolder']
# ['CFundBankAccount', 'CFundIntroduction', 'CFundManagement', 'CFundPchRedmCMF',
#  'CFundTACode', 'FundCreditRecord']

# 04-03 共同基金-权益数据'ChinaFundMajorEvent',
wind_0403 = ['CFundAdmPermitSchedule', 'CFundEventdateinformation', 'Cfundholdersmeeting', 'CFundIllegality',
              'ChinaMFDividend', 'ChinaMutualFundIssue', 'ChinaMutualFundTransformation',
             'CMFHolder', 'CMFHolderStructure', 'CMFHoldingratioanomaly', 'CMFRatioSubscribe',
             'CMFundSplit',
             'ChinaFundMajorEvent']
# ['CMFLiquidation']

# 04-04 共同基金-市场表现 , 'ChinaMutualFundBenchmarkEOD' 'ChinaMutualFundNAV','ChinaMutualFundPosEstimation',
wind_0404 = ['Cfundratesensitive', 'ChinaClosedFundEODPrice', 'ChinaMutualFundFloatShare',
               'ChinaMutualFundRepNAVPer', 'ChinaMutualFundSeatTrading',
             'ChinaMutualFundShare', 'CMFIOPVNAV', 'CMFNAVOperationrecord', 'CMFTradingSuspension',
             'CMMQuarterlydata', 'CMoneyMarketDailyFIncome', 'CMoneyMarketFIncome'
    , 'ChinaMutualFundBenchmarkEOD', 'ChinaMutualFundNAV', 'ChinaMutualFundPosEstimation',]

# 04-05 共同基金-市场衍生数据  未落
wind_0405 = ['ChinaMFMPerformance', 'ChinaMFPerformance', 'CMFFixedinvestmentRate', 'FIndexPerformance']

# 04-06 共同基金-申购赎回
wind_0406 = ['ChinaMutualFundPchRedm', 'ClosedFundPchRedm', 'LOFPchRedm']
# ['ETFPchRedm']

# 04-07 共同基金-投资组合 未落
wind_0407 = ['CFundHoldRestrictedCirculation', 'CFundPortfoliochanges', 'ChinaMutualFundAssetPortfolio', 'ChinaMutualFundBondPortfolio',
             'ChinaMutualFundIndPortfolio', 'ChinaMutualFundStockPortfolio', 'CMFOtherPortfolio', 'CMFundThirdPartyIndPortfolio',
             'CMMFPortfolioPTM']

# 04-08 共同基金-评级
wind_0408 = ['CMFundWindRating', 'CompanyAward', 'FundBondportfolio']
# ['CMFundThirdPartyRating']

# 04-09 共同基金-财务数据
wind_0409 = ['CMFBalanceSheet', 'CMFfairvalueChangeProfit', 'CMFFinancialIndicator', 'CMFIncome',
             'CMFIssuingDatePredict', 'CMFNAVChange', 'CMFQuarterlyFinancialIndicator']

# 04-10 共同基金-公司财务数据--- 灰
wind_0410 = ['FundACashFlow', 'FundBalanceSheet', 'FundIncome']

# 04-11 共同基金-分级基金--- 灰
wind_0411 = ['SCFClause', 'SCFConvert', 'SCFReturnDistribution']

# 04-12 共同基金-估值
wind_0412 = ['SuspendSECValuation']
# ['SuspendSECValuationMethod']

# 04-13 中港互认基金-基本资料
wind_0413 = ['CHFundAgency', 'CHFundDescription', 'CHFundFee', 'CHFundList',
             'CHFundManager', 'CHFundSector']

# 04-14 中港互认基金-市场表现
wind_0414 = ['CHFundMFPerformance', 'CHFundNAV', 'CHFundShare']

# 04-15 中港互认基金-权益数据
wind_0415 = ['CHFundDividend']

# 04-16 QFII基金库
wind_0416 = ['QFIIDescription', 'QFIIQuotaChange']

# 04-17 QDII投资组合
wind_0417 = ['QDIIIndPortfolio', 'QDIIScopePortfolio', 'QDIISecuritiesPortfolio']

# 04-18 共同基金-指数数据
wind_0418 = ['CFundIndexMembers', 'CFundindextable', 'CFundWindIndexcomponent', 'CFundWindIndexMembers',
             'CMFIndexDescription', 'CMFIndexEOD']

# 04-19 中国共同基金-财务附注--- 灰
wind_0419 = ['CMFInterestRateRisk']

# 05-01 期货-基础信息
wind_0501 = ['CFuturesContPro', 'CFuturesDescription', 'CFuturesmarginratio']

# 05-02 期货-交易数据
# 05-03 期货-黄金现货
# 05-04 期货-商品现货
wind_0504 = ['CCommodityFuturesEODPrices']
# 05-05 期货-股指期货
wind_0505 = ['CIndexFuturesEODPrices']
# 05-06 期货-国债期货
wind_0506 = ['CBondFuturesEODPrices']
# 05-07 中国期权数据
wind_0507 = ['ChinaOptionEODPrices']
# 05-08 中国期权-交易统计
# 05-09 期货-中国期货指数
# 05-10 中国期货第三方数据

# 07-01 香港股票-基础信息
# 07-02 香港股票-发行数据
# 07-03 香港股票-行业数据
# 07-04 香港股票-行情交易数据
wind_0704 = ['HKshareEODPrices']
# 07-05 香港股票-行情衍生数据
# 07-06 香港股票-股本结构
# 07-07 香港股票-权益数据
wind_0707 = ['HKshareEvent']
# 07-08 香港股票-财务报表GSD
# 07-09 香港股票-财务附注
# 07-10 香港股票-重大事件
# 07-11 香港股票-公司治理
# 07-12 香港股票-盈利预测
# 07-13 香港股票-ETF
# 07-14 香港股票-指数数据
wind_0714 = ['HKIndexEODPrices']
# 07-15 香港期货
# 07-16 香港期权
# 07-17 香港衍生品
# 07-98 香港股票第三方数据

# 中国A股量化因子库
wind_16 = ['PITFinancialFactor', 'RevenueTechnicalFactor', 'TurnoverTechnicalFactor']


def getDirName(table):
    if table in wind_0101:
        dir_name = '中国A股-基础信息'
    elif table in wind_0102:
        dir_name = '中国A股-行情交易数据'
    elif table in wind_0103:
        dir_name = '中国A股-行情衍生数据'
    elif table in wind_0104:
        dir_name = '中国A股-融资融券数据'
    elif table in wind_0105:
        dir_name = '中国A股-权益数据'
    elif table in wind_0106:
        dir_name = '中国A股-财务数据'
    elif table in wind_0107:
        dir_name = '中国A股-财务附注'
    elif table in wind_0108:
        dir_name = '中国A股-公司治理'
    elif table in wind_0109:
        dir_name = '中国A股-股东数据'
    elif table in wind_0110:
        dir_name = '中国A股-重大事件'
    elif table in wind_0111:
        dir_name = '中国A股-并购重组'
    elif table in wind_0112:
        dir_name = '中国A股-机构调研'
    elif table in wind_0113:
        dir_name = '中国A股-优先股'
    elif table in wind_0114:
        dir_name = '中国A股-股票风格'
    elif table in wind_0115:
        dir_name = '中国A股-指数数据'
    elif table in wind_0116:
        dir_name = '中国A股-指数衍生数据'
    elif table in wind_0117:
        dir_name = '中国A股-专题统计报表'
    elif table in wind_0197:
        dir_name = '中国A股-CCRQM数据'
    elif table in wind_0198:
        dir_name = '中国A股第三方数据'
    elif table in wind_0199:
        dir_name = 'FileSync配置表'
    elif table in wind_0201:
        dir_name = '中国A股-万得一致预测'
    elif table in wind_0202:
        dir_name = '中国A股-盈利预测明细'
    elif table in wind_0401:
        dir_name = '共同基金-基础信息'
    elif table in wind_0402:
        dir_name = '基金公司-基本资料'
    elif table in wind_0403:
        dir_name = '共同基金-权益数据'
    elif table in wind_0404:
        dir_name = '共同基金-市场表现'
    elif table in wind_0405:
        dir_name = '共同基金-市场衍生数据'
    elif table in wind_0406:
        dir_name = '共同基金-申购赎回'
    elif table in wind_0407:
        dir_name = '共同基金-投资组合'
    elif table in wind_0408:
        dir_name = '共同基金-评级'
    elif table in wind_0409:
        dir_name = '共同基金-财务数据'
    elif table in wind_0410:
        dir_name = '共同基金-公司财务数据'
    elif table in wind_0411:
        dir_name = '共同基金-分级基金'
    elif table in wind_0412:
        dir_name = '共同基金-估值'
    elif table in wind_0413:
        dir_name = '中港互认基金-基本资料'
    elif table in wind_0414:
        dir_name = '中港互认基金-市场表现'
    elif table in wind_0415:
        dir_name = '中港互认基金-权益数据'
    elif table in wind_0416:
        dir_name = 'QFII基金库'
    elif table in wind_0417:
        dir_name = 'QDII投资组合'
    elif table in wind_0418:
        dir_name = '共同基金-指数数据'
    elif table in wind_0419:
        dir_name = '中国共同基金-财务附注'
    elif table in wind_0501:
        dir_name = '期货-基础信息'
    elif table in wind_0504:
        dir_name = '期货-商品现货'
    elif table in wind_0505:
        dir_name = '期货-股指期货'
    elif table in wind_0506:
        dir_name = '期货-国债期货'
    elif table in wind_0507:
        dir_name = '中国期权数据'
    elif table in wind_0704:
        dir_name = '香港股票-行情交易数据'
    elif table in wind_0707:
        dir_name = '香港股票-权益数据'
    elif table in wind_0714:
        dir_name = '香港股票-指数数据'
    elif table in wind_16:
        dir_name = '中国A股量化因子库'
    else:
        dir_name = '临时目录'
    return dir_name


f_info_windcode_table = ['ChinaMutualFundNAV', 'CMFFixedinvestmentRate']












