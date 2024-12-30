##                             调仓指令   
####功能描述：根据目标仓位，当前总资产和当前持仓信息，计算出今日的调仓指令，和成交详情 
## 注： 目前支持类型（股票，ETF）
一，回测
#####过程：
1. 根据策略配置中的撮合价格类型获取预成交价（price），并按此预成交价重新计算totalAsset
2. 结合各成分股目标仓位占比（targetratio）和总资产 计算出目标占资（targetNotional）
3. 用各股的 目标占资（targetNotiional） - 持仓市值 ，计算出需调仓金额（resultNotional），
    负值，需要卖出，正值，需要买入
4. 根据标的及策略配置的交易系统获取计算出响应的手续费，然后从totalasset中减去手续费,并重新计算买的需调仓金额（resultNotional）
5. 用 resultNotional/price 计算出基础调仓量。
6. 对基础调仓量根据买卖不同方式做整百处理，基本处理方式
                                        对于买，以该标的类型的最小下单量(min_order_volume)为基准做向下取整，
                                        对于卖，以该标的类型的最小下单量(min_order_volume)为基准向上取整 .
        具体公式 :
               
        shares = resultNotional/price
        basal = shares//min_order_volume            # 取整
        increment = math.ceil((shares % min_order_volume/min_order_volume)*((1-BS)/2)  #BS:买卖方向，卖为-1，买为1
        volume = (basal + increment)* min_order_volume
                        
                        
                        



二，实盘：
        与回测逻辑相同，不同之处在于 总资产（totalAsset） 和持仓（preposition）是通过交易接口实时获取的最新状态。
        price从交易系统获取最新价