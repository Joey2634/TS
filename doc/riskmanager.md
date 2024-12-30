##                                                风控逻辑文档
####                  提供通过止损，最大回撤，集中度等来控制仓位或个股占比的功能
##  注：目前支持品种类型（股票，ETF）
一，回测

    1,止损
    根据策略当前净值来判断是否达到风控设定的止损阀值，达到就将仓位降到风控配置的仓位值
    2,最大回撤
    可以配置 通过指定的某个策略或者自己n天内最大回撤或或者n天内配置的基准标的（一般为指数）的最大回撤来控制仓位
         检查持仓是否有在禁卖池中的。如果有 在前面空仓逻辑后的仓位基础上减去这部分
    当上述风控配置有多个时，最终仓位将会取每个风控类型的目标仓位中的最小值
    3,个股集中度
    可以在风控里配置个股最大占比，超过这个占比的股票将被砍到配置值，多余的部分用默认替代标的(defaultReplacement)替代.
        超过集中度的部分，替代方式目前有以下几种：
        1> CASH： 超出部分直接砍掉，留作现金
        2> SELF： 超出部分盘中超量，盘尾砍到集中度。多做部分的量的计算
                  ext_ratio = min(targetRatio-集中度, 底仓(position), 集中度)
                  shares = (total_asset * ext_ratio)/price
                  向上取整并不大于持仓量
                  volume = min(ceil(shares/100)*100, position)
        3> 510300.SH： 超出部分买510300.SH
                 
         
   4,新增期货对冲逻辑
        1> 在处理完最大回撤后判断是否需要对冲，如果需要修改类属性self.need_hedge对应的strategy_id为数据库配置的主力合约
        2> 在过完集中度后，如果需要对冲， 按多头目标仓位计算出空投期货占资比例
        
        

二，实盘
    昨日总资产获取来源不同，其他逻辑与回测相同


期货处理逻辑
定义变量及公式
        
        多空平衡公式：
        x:stockPositionRatio # 股票占比
        y:futurePositionRatio # 空头期货保证金占比
        z:cashRatio #
        r:marginRatio
        h:空头对冲多头的比例
        {x+y+z=1
         x*h=y/r
         z>=y/r*maxChange*1.1}  1.1的意思是  maxChange扣的钱+持仓亏损需要补的保证金
         解得:
            x <= 1/(1+h*r+h*maxChange*1.1)
         
        期货账户自平衡公式
        x = futureBond      # 期货持仓占用保证金占比
        y = cash            # 保证不爆仓的现金
        r = marginRatio     # 保证金比例
        z = cash_need_move  # 需挪走的现金占比
        x + y +z = 1
        y >= x /r*maxChange + x*maxChange
        解得： x <= 1-z/(1+maxChange/r+maxChange)
         
         
回测第一天，根据上述公式计算出股票多头，空投保证金，和现金各自比例，通过修改account信息，直接完成划拨资金动作

进入风控环节：

1> 首先判断是否为reset日
        判断条件： 是否为期货移仓换约日。
        reset：
            (重新计算多空比例，并根据现有根据当前总资产，多头总资产，空投总资产，计算出需要划拨的现金：cashNeedMove)
             如果cashNeedMove >0,代表如果从股票多头划拨资金到期货空头，cashNeedMove <0，从期货空头向股票多头划拨 
             
             根据多空平衡公式计算出今日多/空头占总资产比例 stockPositionRatio,futurePositionRatio
             计算出期货账户自平衡 futurePositionRationByItself
             最终  期货持仓目标占当前期货账户(preFutureAccount)比例： futureRatio = min(futurePositionRatio * totalAsset / preFutureAccount,
                                                                                        futurePositionRationByItself,
                                                                                        1)
                   多头股票目标占当前多头账户(preStockAccount)比例： stockRatio = min(stockPositionRatio * totalAsset / preStockAccount,
                                                                                        1)
        非reset：
             根据needMoveCash ,计算出今日多头及空投划拨资金之后应该剩余资产占各自账户的比例 ，
                   如果 needMoveCash > 0 :  stockRatio = (preStockAccount - needMoveCash)/preStockAccount
                   如果 needMoveCash <0 : 需通过空头自平衡公式计算出 今日空投持仓应占比例 futureRatio 
            
2> 经过集中度处理之后， 多头可能会减仓，为保证空头对应市值不大于多头，需重新计算多头实际目标市值 stockTargetPositionValue。
       并结合当前对应合约的保证金占比 计算出实际期货市值占比。 而这个占比不能超过自平衡占比 。
3> 添加期货对应AdjustTargetPosition 信息
4> 清算之后，根据个系统现金状态及计划划拨现金 进行资金划拨动作
    
注： adjustTargetPosition 中targetRatio占比含义更改，为 占各自对应账户总资产的比例

           
生成order部分修改。 由原来通过totalAsset计算 变成了通过 各自账户的总资产计算

    
    