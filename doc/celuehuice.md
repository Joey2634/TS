# 五、策略回测
## （一）概述
**策略回测**是包含选股、资产配置、风控、生产订单、交易执行、清算和绩效评估全流程的模块，回测模块通过利用redis和内存进行数据存储提高数据使用效率，通过矩阵思维同时处理多个策略优化计算效率，通过进程、线程提高资源利用效率，最终优化回测速度。
## （二）回测使用案例
### 1、挂载本地数据
##### （1）第一次挂载：
进入ai-investment-manager包所在目录，运行以下命令

```shell
$  sh ai-investment-manager/nfs_start.sh
```

##### （2）非第一次挂载或199服务器重启：
进入ai-investment-manager包所在目录，运行以下命令

```shell
$  sudo umount /share_data
$  sudo mount –t nfs 10.24.206.199:/share_data /share_data
```

### 2、运行回测
进入ai-investment-manager包所在目录，运行以下命令

```shell
$  python3 ai-investment-manager/main/backtest/runBacktest.py
```

### 3、回测类Backtest使用说明如下：
* 初始化回测类
* def \_\_init__(self, strategy_ids, start_date, end_date, env=’dev’)

| 名称           | 类型   |     | 说明                                     |
|--------------|------|-----|----------------------------------------|
| strategy_ids | list | 输入  | 策略id的list，如[‘turing_1-3’,’turing_1-4’] |
| start_date   | str  | 输入  | %Y%m%d格式，如’20210112’                   |
| end _date    | str  | 输入  | %Y%m%d格式，如’20210112’                   |
| env          | str  | 输入  | 回测默认在dev环境                             |
| 返回值          | 无    | 返回值 | 无                                      |

* 初始化asset数据
* def _setAsset (self)

| 名称  | 类型        |     | 说明              |
|-----|-----------|-----|-----------------|
| 返回值 | dataframe | 返回值 | 策略配置首日asset数据 |

* 初始化account数据
* def _setAccount (self)

| 名称  | 类型        |     | 说明              |
|-----|-----------|-----|-----------------|
| 返回值 | dataframe | 返回值 | 策略配置首日account数据 |

* 初始化股票池
* def _setSecurityPool (self)

| 名称  | 类型 |     | 说明 |
|-----|----|-----|----|
| 返回值 | 无  | 返回值 | 无  |

* 初始化目标持仓占比
* def _setTargetPosition (self)

| 名称  | 类型 |     | 说明 |
|-----|----|-----|----|
| 返回值 | 无  | 返回值 | 无  |

* 初始化策略配置参数
* def _getStrategyConfig(self)

| 名称  | 类型         |     | 说明                                                                                                        |
|-----|------------|-----|-----------------------------------------------------------------------------------------------------------|
| 返回值 | List(dict) | 返回值 | 返回策略配置字典列表，如 [{‘strategy_id’:’turing’,’selection_id’:’1’}, {‘strategy_id’:’turing-1’,’selection_id’:’2’}] |

* 初始化策略选股、配置、风控、绩效等参数
* def _getConfig(self, table, key)

| 名称    | 类型         |     | 说明                                                                       |
|-------|------------|-----|--------------------------------------------------------------------------|
| table | str        | 输入  | 策略配置表名，如’risk_config’,’allocation_config’                                |
| key   | str        | 输入  | 相应配置id,如风险配置为’risk_id’，选股配置为’selection_id’                               |
| 返回值   | dict(dict) | 返回值 | 返回字典套字典，如 {’turing’:{selection_id’:’1’},{’turing-1:{’selection_id’:’2’}} |

* 初始化wind数据
* def _getConfig(self)

| 名称  | 类型 |     | 说明 |
|-----|----|-----|----|
| 返回值 | 无  | 返回值 | 无  |

* 回测结果存入数据库
* def saveResult2DB(self, tables ,condition)

| 名称         | 类型   |     | 说明                                                                  |
|------------|------|-----|---------------------------------------------------------------------|
| tables     | list | 输入  | 要存入数据库的表名，不写则全存                                                     |
| conditions | str  | 输入  | sql语句，是依据绩效指标判断是否存数据库的条件，如’total_returns>1000’，指只有策略的总收益大于1000%才存数据 |
| 返回值        | 无    | 返回值 | 无                                                                   |

* 回测主程序
* def run(self)

| 名称  | 类型 |     | 说明 |
|-----|----|-----|----|
| 返回值 | 无  | 返回值 | 无  |
