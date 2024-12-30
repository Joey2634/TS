import numpy as np
import pandas as pd

data = pd.DataFrame(np.arange(16).reshape(4,4),index=list('abcd'),columns=list('ABCD'))
print(data)
print(data.loc['a'])
print(data.iloc[0])
print(data.loc[:,['A']]*2)
print(data)
