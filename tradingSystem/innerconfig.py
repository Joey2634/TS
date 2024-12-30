# -*- coding:utf-8 -*-
from datetime import datetime

today = datetime.now().strftime('%Y-%m-%d')

exchID2name = dict(SH='上交所', SZ='深交所', DCE='大商所', CFE='中金所', SHF='上期所', CZC='郑商所')

# 交易系统信息
# rootNet = dict (serverHosts=dict (test='172.23.122.18', prod='172.22.137.194'),
rootNet = dict(serverHosts=dict(test='10.23.119.177', prod='172.22.137.194'),
               serverPorts=dict(test=9880, prod=9880),
               wind2ExchID=dict(SH='0', SZ='1', DCE='D', CFE='F', SHF='S', CZC='Z'),
               exchID2wind={'0': 'SH', '1': 'SZ', 'D': 'DCE', 'F': 'CFE', 'S': 'SHF', 'Z': 'CZC'},
               trade_types=['B', 'S'], )
WIndCodeType = {
    'future': ['D', 'F', 'S', 'Z'],

    'stock': ['0', '1']
}

CATS = dict(trading_server_hosts=dict(test='10.27.116.132', prod=''),
            trading_server_ports=dict(test=12000, prod=0),
            marketdata_server_hosts=dict(test='10.27.116.131', prod=''),
            marketdata_server_ports=dict(test=11000, prod=0),
            gateway_server=dict(ip='172.23.122.12', port=18000),
            gateway_server_backup=dict(ip='172.23.122.13', port=18000),
            trade_type=dict(tocats={'B': '1', 'S': '2'}, fromcats={'1': 'B', '2': 'S'})
            )
A6 = dict(serverHosts=dict(test='10.23.117.223', prod='172.22.135.31'),
          serverPorts=dict(test=21000, prod=21000),
          wind2ExchID=dict(SH='1', SZ='0', GG='8', CZC='Z', DCE='D', SHF='H', CFE='F', SG='G', TBZR='9', YHJ='A',
                           CW='W'),
          exchID2wind={'1': 'SH', '0': 'SZ', '8': 'GG', '9': 'TBZR', 'A': 'YHJ', 'Z': 'CZC', 'D': 'DCE', 'H': 'SHF',
                       'F': 'CFE', 'G': 'SG', 'W': 'CW'},
          trade_type=dict(toa6={'B': '0B', 'S': '0S', '0Q': '0Q', '0J': '0J'},
                          froma6={'0B': 'B', '0S': 'S', '0Q': 'B', '0J': '0J'}),
          # req=dict(test='req_kams', prod='req31'),
          # ans=dict(test='ans_kams', prod='ans31'),
          req=dict(test='req_kams', prod='req_ext'),
          ans=dict(test='ans_kams', prod='ans_ext'),
          hedgeflag='0',  # (0 投机 1 保值 2 套利)
          priceType='1',  # (1,绝对价格 , 2 平均价格 , 4 不限价 5 市价 6 固定价格)
          )

HS = dict(trading_server_hosts=dict(test='hsconfig_dev.ini', prod=''),
          wind2ExchID=dict(SH='1', SZ="2", ),
          exchID2wind={"1": "SH", "2": "SZ", 'G': "沪hk"},
          trading_funId=dict(login=331100, getcash=332255, getstkinfo=400, getposition=333104, getorders=333101,
                             gettrades=333102, sendorder=333002, cancelorder=333017),
          HSexchTy2wind={'1': "B", '2': 'S'},
          wind2HSexchTy={'B': '1', 'S': '2'}

          )

tradingSysInfo = dict(rootNet=rootNet, CATS=CATS, A6=A6, HS=HS)

# 交易所交易时间段信息
SH = dict(morning_open='8:30:00',
          morning_close='11:30:00',
          afternoon_open='13:00:00',
          afternoon_close='15:00:00')
SZ = dict(morning_open='8:30:00',
          morning_close='11:30:00',
          afternoon_open='13:00:00',
          afternoon_close='15:00:00')
CFE = dict(morning_open='9:00:00',
           morning_close='11:30:00',
           afternoon_open='13:00:00',
           afternoon_close='20:10:00')
DCE = dict(morning_open='9:00:00',
           morning_close='11:30:00',
           rest_start='10:15:00',
           rest_end='10:30:00',
           afternoon_open='13:00:00',
           afternoon_close='20:10:00')
SHF = dict(morning_open='9:00:00',
           rest_start='10:15:00',
           rest_end='10:30:00',
           morning_close='11:30:00',
           afternoon_open='13:00:00',
           afternoon_close='20:10:00')
CZC = dict(morning_open='9:00:00',
           rest_start='10:15:00',
           rest_end='10:30:00',
           morning_close='11:30:00',
           afternoon_open='13:00:00',
           afternoon_close='20:10:00')

exchange_info_map = dict(SH=SH, SZ=SZ, CFE=CFE, DCE=DCE, SHF=SHF, CZC=CZC)


def get_time_slot(exchangeCode, timeslotName):
    time_slot = exchange_info_map[exchangeCode][timeslotName]
    return datetime.strptime(today + ' ' + time_slot, '%Y-%m-%d %H:%M:%S')
