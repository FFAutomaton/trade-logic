import pandas

df = pandas.read_csv('./data/sonuclar.csv', delimiter='\t', header=None)
# df[['A', 'B']] = df['AB'].str.split(' ', 1, expand=True)
df = df.sort_values(by=[0])
df['run'] = df[0].str.split('/t', expand=True)[0]
print(df.columns)
# df["run"] = df.apply(lambda x: x["info"].split('-')[0], axis=1)

sonuc = df.groupby('run').mean().sort_values(by=[21], ascending=False)
print('jj')