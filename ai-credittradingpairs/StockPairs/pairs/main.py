from pairs.PairAnalys import Gen_total_df

if __name__ == '__main__':


    df = Gen_total_df('2017-11-15', '2017-11-30', switch=True)
    print(df)
    df.to_csv('total_115_35%_tot1.csv')
