

prod = [
    {"host": "172.23.122.16", "port": 7000},
    {"host": "172.23.122.16", "port": 7001},
    {"host": "172.23.122.12", "port": 7000},
    {"host": "172.23.122.12", "port": 7001},
    {"host": "172.23.122.19", "port": 7000},
    {"host": "172.23.122.19", "port": 7001},
]

dev = [
    {"host": "10.24.206.24", "port": 7000},
    {"host": "10.24.206.24", "port": 7001},
    {"host": "10.24.206.220", "port": 7000},
    {"host": "10.24.206.220", "port": 7001},
    {"host": "10.24.206.211", "port": 7000},
    {"host": "10.24.206.211", "port": 7001},

]

redis_client_dict = {'dev': dev, 'prod': prod}

# selection redis key
StrategyRedisKey = 'ai-investment-manager|security_pool'
ConditionRedisKey = 'ai-investment-manager|single_factor'

liveMarketRedisConfig = {"host": "172.23.122.17", "db": 4, "port": 6379, "password": ""}
