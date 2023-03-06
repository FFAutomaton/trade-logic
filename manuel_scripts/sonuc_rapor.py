import pandas


def sonuc_rapor(params):
    df = pandas.read_csv('../manuel_scripts/data/sonuclar.csv', delimiter='\t', header=None)
    df = df.sort_values(by=[0])
    df['run'] = df[0]

    sonuc = df.groupby('run').mean().sort_values(by=[len(df.columns)-2], ascending=False)
    p_list = list(params.keys())
    p_list.remove("mlp_layers")
    sonuc.columns = ['run'] + p_list + ['kar']
    print(sonuc.iloc[0])
