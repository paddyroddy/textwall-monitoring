import pandas as pd

# read in csv
df = pd.read_csv('textwall_sample.csv', nrows=10, header=None, names=['string', 'n/a', 'date', 'time'], parse_dates={'datetime': ['date', 'time']})

# remove email column
df = df.drop('n/a', axis=1)

# clean data
df['string'] = df['string'].str.replace('?', ',')
df['string'] = df['string'].str.lstrip(',')

# split first column into three
df = pd.concat([df['string'].str.split('\,|\s', expand=True), df['datetime']], axis=1)

# set names of columns
df.columns = ['student', 'course', 'phrase', 'datetime']

# set phrase all lowercase
df['phrase'] = df['phrase'].str.lower()

print(df)
