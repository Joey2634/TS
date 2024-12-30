import numpy as np
import pandas as pd

asset = dict(columns=['strategy_id', 'trade_date', 'position_value', 'cash',
                      'total_asset', 'sod_total_asset', 'total_pnl', 'net_value', 'net_value_holder'])
# spot = dict(columns=['strategy_id', 'trade_date', 'spot_value'])


account = dict(columns=['strategy_id', 'trade_date', 'account_type', 'position_value', 'cash',
                        'total_asset', 'sod_total_asset'])

position = dict(columns=['strategy_id', 'trade_date', 'LS', 'windcode', 'account_type', 'amount',
                         'volume', 'notional', 'pre_close', 'close', 'pnl', 'avg_cost'])

trade = dict(columns=['strategy_id', 'trade_date', 'windcode', 'BS', 'LS', 'amount',
                      'volume', 'price', 'fee', 'notional', 'pnl'])

fee = dict(columns=['strategy_id', 'trade_date', 'commission_future', 'commission', 'management_fee_payable',
                    'custodian_fee_payable', 'incentive_fee_payable',
                    'management_fee_payable_cumulative', 'custodian_fee_payable_cumulative',
                    'incentive_fee_payable_cumulative',
                    'management_fee', 'custodian_fee', 'incentive_fee'])

target_position = dict(columns=['strategy_id', 'trade_date', 'windcode', 'LS', 'target_ratio'])

adjusted_target_position = dict(columns=['strategy_id', 'trade_date', 'LS', 'windcode', 'target_ratio'])

target_order = dict(columns=['strategy_id', 'trade_date', 'BS', 'LS', 'windcode', 'volume', 'price'])

performance = dict(columns=['strategy_id', 'benchmark_id', 'start_date', 'end_date', 'total_returns', 'annual_return',
                            'avg_year_return', 'sharpe_ratio', 'sortino_ratio', 'max_drawdown',
                            'longest_max_drawdown_duration',
                            'max_drawdown_5bd', 'max_drawdown_20bd', 'avg_daily_return', 'std_dev_daily_return',
                            'beta_300', 'beta_500',
                            'alpha_300', 'alpha_500', 'win_p'])
turnover = dict(columns=['strategy_id', 'account_type', 'value'])


def initPandasDataFrame(table_config, data=None):
    if isinstance(data, np.ndarray) and not data.any():
        df = pd.DataFrame(columns=table_config['columns'])
    elif data is None:
        df = pd.DataFrame(columns=table_config['columns'])
    else:
        df = pd.DataFrame(data=data, columns=table_config['columns'])
    if table_config.get('index'):
        df.set_index(table_config['index'], inplace=True)
    return df

