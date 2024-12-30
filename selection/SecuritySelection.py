import threading
import numpy as np
from collections import defaultdict
from selection.selectionCondition import *
from selection.selectionCondition.TRADE_DATE_METHOD import *
from selection.selectionCondition.DROP_CODES_METHOD import *


class SecuritySelection:

    def __init__(self, security_selection_id, start_date, end_date, env, mode):
        # backtest回测 live实盘
        self.mode = mode
        self.env = env
        self.security_selection_id = security_selection_id
        self.start_date = start_date
        self.end_date = end_date
        self.name = StrategyRedisKey
        self.func_name = FuncName
        self.condition_name = ConditionRedisKey
        # 根据环境选择redis
        self.redisCli = RedisCluster(startup_nodes=redis_client_dict[self.env], password='citics')
        # 接收redis已存选股数据
        self.before_dict = {}
        self.getBeforeDict()
        # 不排除偏移日的所有交易日
        self.trade_dates_total = getTradeDates(self.start_date, self.end_date)
        # 线程锁
        self.lock = threading.Lock()
        # defaultdict
        self.res = defaultdict(list)
        # 接收ST 停牌股票
        self.drop_codes_method = ''
        self.ST = {}
        self.STOP = {}
        self.HKEND = {}
        self.HKSTOP = {}
        # 接收黑白名单
        self.black_list = {}
        self.white_list = {}
        self.black_list_id = ''
        self.white_list_id = ''
        # 接收索提诺率  天数 分位
        self.sortino_day = ''
        self.sortino_quantile = ''
        # 偏移日参数
        self.trade_date_condition = ''
        # 指标筛选的条件
        self.need_fix = []
        self.PCT_CHANGE = ''
        self.SECURITY_POOL = ''

    def setSecurityPool(self):
        """
        选股策略筛选函数
        """
        # 1.读取筛选条件
        print('读取筛选条件...')
        self.selection_conditions = self.loadStrategyConfig(self.security_selection_id)[self.security_selection_id]

        # 2.拆分有阈值要求的条件
        self.getFixCondition()

        # 3.根据筛选条件,返回筛选后的标的池 多线程
        print('筛选条件返回标的dict...')
        self.getConditionsRes()

        # 4.根据设定阈值，筛选后一日新增code
        self.res = self.getFixRes(self.res)

        # 5.res_codes(dict) 拿到筛选结果 + 黑白名单 偏移日填充 default
        res_codes = self.getResultDict()

        # 6.将策略标的池入库
        print('策略结果入库mysql...')
        self.strategyInsertMysql(self.security_selection_id, res_codes, self.start_date, self.end_date)  # 存mysql

        # 7.redis更新新的日期
        print('redis对应更新...')
        self.before_dict.update(res_codes)
        self.redisCli.hset(self.name, str(self.security_selection_id), str(self.before_dict))  # 存redis
        print(self.security_selection_id, '选股完成...')

    def getFixCondition(self):
        """
        拆分有阈值要求的条件
        """
        for i in self.selection_conditions:
            if i.endswith(']'):
                compare_data = eval(i.split(',')[-2] + ',' + i.split(',')[-1])
                self.selection_conditions.remove(i)
                self.need_fix.append(i)
                fix_conditon = i.split(',')[0] + ',' + i.split(',')[1] + ',' + str(compare_data[0])
                self.selection_conditions.append(fix_conditon)

    def getPctRate(self):
        pct_data_dict = {}
        for day in self.trade_dates:
            pct_data_dict[day] = {}
        oracle = Database(WIND_DB)
        for day in self.trade_dates:
            print('获取', day, 'pct数据...')
            sql = "select S_INFO_WINDCODE, S_DQ_PCTCHANGE FROM wind.AShareEODPrices where trade_dt='{}'".format(day)
            oracle.cursor.execute(sql)

            data = oracle.cursor.fetchall()
            # 返回的标的池list
            codes_res = list(data)
            for (code, rate) in codes_res:
                pct_data_dict[day][code] = rate
        oracle.cursor.close()
        oracle.conn.close()
        return pct_data_dict

    def getPctRes(self, res_dict):
        """
        获取相比前一天，新增的code,pct<0 去掉
        获取相比前一天，减少的code,pct>0 保留
        """
        # 相比前一天，变化的code
        add_code_dict = defaultdict(list)
        minus_code_dict = defaultdict(list)
        try:
            pct_data_dict = self.getPctRate()
            if self.trade_dates[0] == '20150105':
                start_index = 1
            else:
                start_index = 0
            for day in self.trade_dates[start_index:]:
                if self.trade_date_condition:
                    day_before = getTradeSectionDates(day, -6)[0]
                else:
                    day_before = getTradeSectionDates(day, -2)[0]
                for code in res_dict[day]:
                    if day_before not in self.trade_dates:
                        data_dict = self.before_dict
                    else:
                        data_dict = res_dict
                    if (code not in data_dict[day_before]) and (eval("'{}'<0".format(pct_data_dict[day][code]))):
                        # 留下来新增的、但是不要的code
                        add_code_dict[day].append(code)
                    if (code in data_dict[day_before]) and (code not in data_dict[day]) and (eval("'{}'>0".format(pct_data_dict[day][code]))):
                        minus_code_dict[day].append(code)
        except Exception as e:
            print(e, day)
            add_code_dict = {}
        for day in res_dict:
            res_dict[day] = [i for i in res_dict[day] if i not in add_code_dict.get(day, [])]
            res_dict[day] = res_dict[day] + minus_code_dict.get(day, [])
        return res_dict

    def getFixRes(self, res_dict):
        """
        条件阈值筛选
        """
        if self.PCT_CHANGE:
            res_dict = self.getPctRes(res_dict)
        # 配置的条件阈值
        for condition in self.need_fix:
            split_res = condition.split(',')
            condition_prefix, symbol, threshold_value = split_res[0], split_res[1], eval(split_res[-2]+','+split_res[-1])
            if type(threshold_value) == list:
                set_data, limit_data = threshold_value
                # 筛出来相比前一天新增的，但是阈值不符的、不要的code
                add_code_dict = self.getAddCode(res_dict, condition_prefix, symbol, limit_data)
                for day in add_code_dict:
                    res_dict[day] = [i for i in res_dict[day] if i not in add_code_dict.get(day, [])]
        return res_dict

    def getAddCode(self, res_dict, condition_prefix, symbol, limit_data):
        """
        获取相比前一天，新增的code
        """
        try:
            condition_data_dict = eval(self.redisCli.hget(ConditionRedisKey, str(condition_prefix)))
            # 相比前一天，不符合条件的code
            add_code_dict = defaultdict(list)
            if self.trade_dates[0] == '20150105':
                start_index = 1
            else:
                start_index = 0
            for day in self.trade_dates[start_index:]:
                if self.trade_date_condition:
                    day_before = getTradeSectionDates(day, -6)[0]
                else:
                    day_before = getTradeSectionDates(day, -2)[0]
                for code in res_dict[day]:
                    if day_before not in self.trade_dates:
                        data_dict = self.before_dict
                    else:
                        data_dict = res_dict
                    if (code not in data_dict[day_before]) and not (eval("'{}'{}'{}'".format(condition_data_dict[day][code], symbol, limit_data))):
                        # 留下来新增的、但是不要的code
                        add_code_dict[day].append(code)
        except Exception as e:
            print(e, day)
            add_code_dict = {}
        return add_code_dict

    def getResultDict(self):
        """
        黑白名单， 偏移日其他日期数据填充，default
        :return: dict
        """
        res_dict = self.res.copy()
        # 偏移日非交易日数据填充前一交易日数据
        res_dict = self.fillData(res_dict)
        # 黑白名单
        for i in self.black_list:
            res_dict[i] = [code for code in res_dict[i] if code not in self.black_list[i]]
        for i in self.white_list:
            res_dict[i] = res_dict[i] + self.white_list[i]
        if self.mode == 'live':
            # 只有实盘有禁买池
            res_dict = self.getForbidden(res_dict)
        # 在返回结果中剔除ST 停牌
        total_drop = self.getDropRes()
        for i in res_dict:
            res_dict[i] = list(set([code for code in res_dict[i] if code not in total_drop.get(i, [])]))
        # 根据索提诺率筛选
        if self.sortino_day and self.sortino_quantile:
            res_dict = self.getSortino(res_dict)
        return res_dict

    def getSortino(self, res_dict):
        """
        索提诺率(目前只有港股通100)
        """
        # 拿到所有的标的
        all_codes = []
        for i in res_dict:
            all_codes = list(set(all_codes + res_dict[i]))
        # 拿到标的所有日期的行情
        start_date = getTradeSectionDates(self.start_date, (-int(self.sortino_day) - 1))[0]
        end_date = getTradeSectionDates(self.end_date, 1)[0]
        if all_codes[0].endswith('HK'):
            code_eod_table = 'HKshareEODPrices_Original'
            benchmark_eod_table = 'AIndexWindIndustriesEOD'
            benchmark = self.SECURITY_POOL.split(',')
        else:
            code_eod_table = 'AShareEODPrices'
            benchmark_eod_table = 'AIndexEODPrices'
            benchmark = self.SECURITY_POOL.split(',')
        df = getWindData(code_eod_table, all_codes,
                         start_date=start_date, end_date=end_date, fields=['S_DQ_PRECLOSE', 'S_DQ_CLOSE'])

        # 拿到GGT100.WI所有日期的行情
        all_Y = getWindData(benchmark_eod_table, benchmark,
                         start_date=start_date, end_date=end_date, fields=['S_DQ_PCTCHANGE'])

        df['S_DQ_PCTCHANGE'] = (df['S_DQ_CLOSE'] - df['S_DQ_PRECLOSE'])*100 / df['S_DQ_PRECLOSE']
        df = df.pivot(index='TRADE_DT', columns='S_INFO_WINDCODE', values='S_DQ_PCTCHANGE')
        df_Y = all_Y.pivot(index='TRADE_DT', columns='S_INFO_WINDCODE', values='S_DQ_PCTCHANGE')
        for i in res_dict:
            print('计算{}索提诺率'.format(i))
            codes_list = res_dict[i]
            s_date = getTradeSectionDates(i, (-int(self.sortino_day) - 1))[0]
            e_date = getTradeSectionDates(i, -2)[0]
            # 拿到筛选后 对应日期、标的 的行情
            df_mid = df[(df.index >= s_date) & (df.index <= e_date)][codes_list]
            df_Y_mid = df_Y[(df_Y.index >= s_date) & (df_Y.index <= e_date)][benchmark]
            codes = df_mid.columns
            sortino = []
            Y = df_Y_mid.values
            for code in codes:
                below = [(df_mid[code][x] - np.nanmean(Y)) ** 2 for x in range(len(df_mid[code])) if df_mid[code][x] < np.nanmean(Y)]
                if below==[]:
                    sortino.append(0.0)
                else:
                    sortino.append(sum(below) / len(below))
            codes = codes[sortino >= np.percentile(sortino, int(self.sortino_quantile))]
            res_dict[i] = codes.tolist()
        return res_dict

    def getForbidden(self, res_dict):
        # 禁买池
        forbidden_dict = {}
        securityblackList = SecurityBlackList()
        tradetype = 'buy'
        data_forbidden = [i[0] for i in securityblackList.getBlackList(tradetype).values.tolist()]
        # 实盘禁买池与res交集-->black_list
        today = self.trade_dates_total[-1]
        forbidden_dict[today] = [code for code in res_dict[today] if code in data_forbidden]
        res_dict[today] = [code for code in res_dict[today] if code not in data_forbidden]
        # 将每天筛选结果与禁买池取交集，存入每日黑名单
        self.blacklistInsertMysql(self.security_selection_id, forbidden_dict)
        return res_dict

    def fillData(self, res_dict):
        # 偏移日非交易日数据填充前一交易日数据
        if self.trade_date_condition:
            for i in self.trade_dates_total:
                for j in range(len(self.trade_dates)-1):
                    if i not in self.trade_dates and i>self.trade_dates[j] and i <self.trade_dates[j+1]:
                        res_dict[i] = res_dict[self.trade_dates[j]]
                    elif i > self.trade_dates[-1]:
                        res_dict[i] = res_dict[self.trade_dates[-1]]
        return res_dict

    def getConditionsRes(self):
        """
        多线程计算每个条件返回的标的
        """
        with ThreadPoolExecutor(1) as executor:
            [executor.submit(self.getConditionRes, selection_condition, self.start_date, self.end_date) for selection_condition in self.selection_conditions]


    def getDropRes(self):
        """
        拿到ST 停牌 退市股票
        """
        print('剔除ST,停牌,退市股票...')
        if 'ST' in self.drop_codes_method.split(','):
            st_a = DROP_CODES_METHOD(self.start_date, self.end_date)
            self.ST = st_a.getST()
        if 'STOP' in self.drop_codes_method.split(','):
            stop_a = DROP_CODES_METHOD(self.start_date, self.end_date)
            self.STOP = stop_a.getStop()
        if 'HKSTOP' in self.drop_codes_method.split(','):
            stop_hk = DROP_CODES_METHOD(self.start_date, self.end_date)
            self.HKSTOP = stop_hk.getHKStop()
        if 'HKEND' in self.drop_codes_method.split(','):
            end_hk = DROP_CODES_METHOD(self.start_date, self.end_date)
            self.HKEND = end_hk.getHKEnd()
        total_drop = {}
        drop_list = [self.STOP, self.ST, self.HKSTOP, self.HKEND]
        for drop_dict in drop_list:
            if drop_dict:
                for date in drop_dict:
                    if total_drop.__contains__(date):
                        total_drop[date] = total_drop[date] + drop_dict[date]
                    else:
                        total_drop[date] = drop_dict[date]
        return total_drop

    def getWBListSqlRes(self, table):
        """
        黑白名单
        :return: dict
        """
        if table in ['black_list', 'black_list_his']:
            limit_list = [self.security_selection_id] + self.black_list_id.split(',')
        else:
            limit_list = [self.security_selection_id] + self.white_list_id.split(',')
        db = Database(AI_DB[self.env])
        if table in ['black_list', 'white_list']:
            sql = "select wind_code from {} where selection_id in {}"\
            .format(table, tuple(limit_list))
            db.cursor.execute(sql)
            data = db.cursor.fetchall()
            db.cursor.close()
            db.conn.close()
            date_dict = {}
            for date in self.trade_dates_total:
                date_dict[date] = [i[0] for i in data]
        else:
            # ['black_list_his', 'white_list_his']
            sql = "select trade_date, wind_code from {} where selection_id in {} and trade_date >= {} and trade_date <= {}"\
                .format(table, tuple(limit_list), self.start_date, self.end_date)
            db.cursor.execute(sql)
            data = db.cursor.fetchall()
            db.cursor.close()
            db.conn.close()
            date_dict = {}
            for (trade_date, windcode) in data:
                if date_dict.__contains__(trade_date):
                    date_dict[trade_date].append(windcode)
                else:
                    date_dict[trade_date] = [windcode]
        return date_dict

    def loadWBList(self):
        """
        选股结果 + 黑白名单
        默认所有日期都添加的黑白名单: black_list white_list
        只在对应日期添加黑白名单: black_list_his white_list_his
        """
        res_black = self.getWBListSqlRes('black_list')
        res_black_his = self.getWBListSqlRes('black_list_his')
        res_white = self.getWBListSqlRes('white_list')
        res_white_his = self.getWBListSqlRes('white_list_his')

        for date in self.trade_dates_total:
            self.black_list[date] = res_black.get(date, []) + res_black_his.get(date, [])
            self.white_list[date] = res_white.get(date, []) + res_white_his.get(date, [])

    def loadStrategyConfig(self, security_selection_id):
        """
        读取策略参数
        """
        config_dict = {}
        db = Database(AI_DB[self.env])
        sql_seg = "SELECT * FROM selection_config where selection_id='{}'".format(security_selection_id)
        db.cursor.execute(sql_seg)
        allres = db.cursor.fetchall()

        print('选股策略:', security_selection_id, '配置参数:', allres)
        res_list = []
        for res in allres:
            config_dict[res[0]] = res_list+[res[1]+':'+res[2]]
            res_list = config_dict[res[0]]
        config_dict = self.disposeConfig(config_dict, security_selection_id)

        # 加载黑白名单
        self.loadWBList()

        # 获取交易日期(偏移日...)
        if self.trade_date_condition:
            trade_dates_ob = TRADE_DATE_METHOD(self.start_date, self.end_date, self.trade_date_condition)
            self.trade_dates = trade_dates_ob.getTradeDates()
        else:
            self.trade_dates = getTradeDates(self.start_date, self.end_date)
        return config_dict

    def disposeConfig(self, config_dict, security_selection_id):
        """
        处理非逻辑条件
        """
        for i in config_dict[security_selection_id].copy():
            # 现金
            if i.startswith('CASH'):
                self.cash = i.split(':')[1]
                config_dict[security_selection_id].remove(i)
            # 交易日期 偏移日
            elif i.startswith('TRADE_DATE_METHOD'):
                self.trade_date_condition = i.split(':')[1]
                config_dict[security_selection_id].remove(i)
            # ST 停牌
            elif i.startswith('DROP_CODES_METHOD'):
                self.drop_codes_method = i.split(':')[1]
                config_dict[security_selection_id].remove(i)
            # 黑白名单id
            elif i.startswith('BLACK_LIST_ID'):
                self.black_list_id = i.split(':')[1]
                config_dict[security_selection_id].remove(i)
            elif i.startswith('WHITE_LIST_ID'):
                self.white_list_id = i.split(':')[1]
                config_dict[security_selection_id].remove(i)
            # 索提诺率
            elif i.startswith('SORTINO'):
                condition = i.split(':')[1]
                self.sortino_day = condition.split(',')[0]
                self.sortino_quantile = condition.split(',')[1]
                config_dict[security_selection_id].remove(i)
            elif i.startswith('SECURITY_POOL'):
                self.SECURITY_POOL = i.split(':')[1]
        return config_dict

    def getBeforeDict(self):
        """
        拿到redis已存选股策略数据
        """
        if self.redisCli.hexists(self.name, str(self.security_selection_id)) and \
                eval(self.redisCli.hget(self.name, str(self.security_selection_id))) != None:
                self.before_dict = eval(self.redisCli.hget(self.name, str(self.security_selection_id)))

    def strategyInsertMysql(self, security_selection_id, rescodes_dict, start_date, end_date):
        """
        策略标的池存mysql
        """
        db = Database(AI_DB[self.env])
        sql_del = """delete from security_pool where security_selection_id='{}' and trade_date>='{}' and trade_date<='{}'"""\
            .format(security_selection_id, start_date, end_date)
        db.cursor.execute(sql_del)
        date_list = rescodes_dict.keys()
        res_list = sum(list(map(lambda x: [[self.security_selection_id, x, code] for code in rescodes_dict[x]], date_list)), [])
        sql_ins = """insert into security_pool values (%s,%s,%s)"""
        db.cursor.executemany(sql_ins, res_list)
        db.conn.commit()
        db.cursor.close()
        db.conn.close()

    def blacklistInsertMysql(self, security_selection_id, rescodes_dict):
        """
        黑名单存mysql
        """
        # 黑名单溯源
        owner = 'swj'
        description = 'forbidden'

        db = Database(AI_DB[self.env])
        sql_del = """delete from black_list_his where selection_id='{}' and trade_date='{}'"""\
            .format(security_selection_id, self.trade_dates_total[-1])
        db.cursor.execute(sql_del)
        date_list = [self.trade_dates_total[-1]]
        res_list = sum(list(map(lambda x: [[self.security_selection_id, x, code, owner, description] for code in rescodes_dict[x]], date_list)), [])
        sql_ins = """insert into black_list_his values (%s,%s,%s,%s,%s)"""
        db.cursor.executemany(sql_ins, res_list)
        db.conn.commit()
        db.cursor.close()
        db.conn.close()

    def conditionPre(self, selection_condition):
        """
        条件参数整理,切片
        """
        # 'INVTURN:000906.SH,000852.SH:-1TD,<=,50'
        if not selection_condition.startswith('INVTURN'):
            selection_conditions_template, paras = selection_condition.split(':')
        else:
            selection_conditions_template, security_pool, paras = selection_condition.split(':')

        if selection_conditions_template == 'SECURITY_POOL':
            paramaters = [selection_condition]
        else:
            paramaters = paras.split(',')

        return selection_conditions_template, paramaters

    def getConditonResFromRedis(self,selection_condition, start_date, end_date):
        """
        从redis拿对应条件筛选结果，若无----> mysql
        """
        condition_redis = {}
        # 拿到redis条件已存 日期:标的池
        if self.redisCli.hexists(self.condition_name, str(selection_condition)):
            condition_redis = eval(self.redisCli.hget(self.condition_name, str(selection_condition)))
        # redis不存在，去mysql拿
        if not self.redisCli.hexists(self.condition_name, str(selection_condition)) or condition_redis == {}:
            print(selection_condition,'redis不存在数据，到mysql取...')
            codes_dict_f = {}
            codes_dict = self.getConditionResFromMysql(codes_dict_f, selection_condition, start_date, end_date)
        else:
            # redis存在，拿到redis已存的最大、最小日期，未存redis的去mysql拿
            codes_dict_f = condition_redis
            stored_max = max(condition_redis.keys())
            stored_min = min(condition_redis.keys())
            # 存的最后一天 < 回测设置最后一天 --->mysql --->func
            if stored_max < getTradeSectionDates(end_date, 1)[0]:
                start_date = str(datetime.datetime.strptime(stored_max, '%Y%m%d').date()+datetime.timedelta(days=1))
                start_date = datetime.datetime.strftime(datetime.datetime.strptime(start_date, '%Y-%m-%d'), '%Y%m%d')
                print(selection_condition, 'redis存在数据，但所存最大天数不满足， 到mysql取redis不存在日期的数据...')
                codes_dict = self.getConditionResFromMysql(codes_dict_f, selection_condition, start_date, end_date)

            elif stored_min > getTradeSectionDates(start_date, 1)[0]:
                end_date = str(datetime.datetime.strptime(stored_min, '%Y%m%d').date()+datetime.timedelta(days=-1))
                end_date = datetime.datetime.strftime(datetime.datetime.strptime(end_date, '%Y-%m-%d'), '%Y%m%d')
                print(selection_condition, 'redis存在数据，但所存最小天数不满足， 到mysql取redis不存在日期的数据...')
                codes_dict = self.getConditionResFromMysql(codes_dict_f, selection_condition, start_date, end_date)
            else:
                print(selection_condition, '拿到redis数据')
                codes_dict = codes_dict_f
        codes_res = {}
        # 因为redis存的是所有日期的条件标的，所以筛出所求日期范围的数据对应更新
        for i in self.trade_dates:
            codes_res[i] = codes_dict[i]
        return codes_res

    def getConditionResFromMysql(self, codes_dict, selection_condition, start_date, end_date):
        """
        从mysql拿对应条件筛选结果，若无----> 对应func
        """
        # mysql拿到条件对应code
        codes_mysql_dict = self.getCodesFromMysqlEach(selection_condition, start_date, end_date)
        start_date = getTradeSectionDates(start_date, 1)[0]

        # mysql没有 或 新条件， 调用对应筛选函数
        if codes_mysql_dict == {} or codes_mysql_dict == None or start_date < min(codes_mysql_dict.keys()) \
                or end_date > max(codes_mysql_dict.keys()):
            print(selection_condition, 'mysql数据不存在或不全，调用筛选函数...')
            func_dict = self.getConditionResFromFunc(selection_condition, start_date, end_date)
            codes_dict.update(func_dict)
        else:
            print(selection_condition, '拿到mysql数据...')
            codes_dict.update(codes_mysql_dict)
        self.redisCli.hset(self.condition_name, str(selection_condition), str(codes_dict))
        return codes_dict

    def getConditionResFromFunc(self,  selection_condition, start_date, end_date):
        """
        对应筛选函数-->codes_dict-->mysql
        """
        # 条件参数整理
        # str(条件名)，对应参数
        selection_conditions_template, paramaters = self.conditionPre(selection_condition)
        codes_ob = self.func_name[selection_conditions_template](paramaters, start_date, end_date, self.env, self.mode)

        codes_dict = codes_ob.getSecurityPool(selection_condition)
        codes_ob.setSecurityPool(codes_dict, selection_condition)

        print(selection_condition, '筛选函数已取到数据...')

        return codes_dict

    def getConditionRes(self, selection_condition, start_date, end_date):
        """
        多线程里面筛选条件函数
        :return: codes_dict
        """

        # 获取条件返回的codes_dict    redis-->mysql-->func
        print(selection_condition, '---', 'start')
        codes_dict = self.getConditonResFromRedis(selection_condition, start_date, end_date)
        days = codes_dict.keys()
        for day in sorted(days):
            self.lock.acquire()
            # 新日期第一个条件code全留，之后取交集
            if self.res.__contains__(day):
                # 估值条件特殊处理
                if selection_condition[:-2] in ['买入', '持有', '中性']:
                    self.res[day] = list(set(self.res[day] + codes_dict[day]))
                else:
                    self.res[day] = list(set(self.res[day]) & set(codes_dict[day]))
            else:
                self.res[day] = codes_dict[day]
            print(selection_condition, '条件筛选后', day, '日所剩标的数为：', len(self.res[day]))
            self.lock.release()
        print(selection_condition, '---', 'done')
        return codes_dict

    def getCodesFromMysqlEach(self, selection_condition, start_date, end_date):
        """
        从mysql取出条件筛选的codes
        :return:date_dict
        """
        condition_key, condition_value = selection_condition.split(':')
        db = Database(AI_DB[self.env])
        sql = """select trade_date, windcode from single_factor_security_pool where condition_key='{}' and condition_value='{}' and trade_date>='{}' and trade_date<='{}' """\
            .format(condition_key, condition_value, start_date, end_date)
        db.cursor.execute(sql)
        data = db.cursor.fetchall()
        db.cursor.close()
        db.conn.close()
        date_dict = {}
        for (trade_date, windcode) in data:
            if date_dict.__contains__(trade_date):
                date_dict[trade_date].append(windcode)
            else:
                date_dict[trade_date] = [windcode]
        return date_dict

    def getCodesFromMysqlStrategy(self):
        """
        从mysql取出策略筛选的codes
        :return:date_dict
        """
        db = Database(AI_DB[self.env])
        sql = """select trade_date, windcode from security_pool where security_selection_id='{}' and trade_date>='{}' and trade_date<='{}' """\
            .format(self.security_selection_id, self.start_date, self.end_date)
        db.cursor.execute(sql)
        data = db.cursor.fetchall()
        date_dict = {}
        for (trade_date, windcode) in data:
            if date_dict.__contains__(trade_date):
                date_dict[trade_date].append(windcode)
            else:
                date_dict[trade_date] = [windcode]
        return date_dict






