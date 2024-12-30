收盘价算法

aitwap3 算法会把需要用收盘价算法(QMOC3)的单的信息存入数据库。 包括（windcode,tradeside,targetVol).
    该程序获取信息之后，对买单按一定资金分配逻辑分配资金之后，发到qmoc3算法
    
分配资金逻辑
    计算出该账户下所有买单按当前最新价计算出的所需资金的总和（cashNeedSum)
    查询到当前账户可用资金 nowCash
    按每个买单占总所需金额的比例分配当前资金 ，公式如下
    
        useableAmt = nowCash *(targetVol*newPrice/cashNeedSum)
        volume = round(useableAmt/newPrice//100) *100

   最终volume = min(volume,targetVol) ##不能超过原始下单量
   
