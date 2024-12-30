import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from futureHedge.hedgeSignal import Future_Load_Signal

if __name__ == '__main__':
    arb = Future_Load_Signal('20120921', '20210508')
    monthlis = arb.delivery_df['month'].unique().tolist()
    target_position_lis = []
    arb.delete_target_position()
    pos_lis = []
    for mon in monthlis[1:]:
        print(f'[{mon}].....')
        if mon == monthlis[1]:
            lis, pos = arb._get_month_target_position(mon, 83, 70, 1.005, 0)
            target_position_lis.extend(lis)
            pos_lis.append(pos)
        else:
            lis, pos = arb._get_month_target_position(mon, 83, 70, 1.005, pos_lis[-1])
            target_position_lis.extend(lis)
            pos_lis.append(pos)
    arb.store_target_position('target_position_backtest', target_position_lis)

