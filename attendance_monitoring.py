import pandas as pd

# read in csv
df = pd.read_csv('textwall_sample.csv', header=None, names=[
                 'string', 'n/a', 'date', 'time'], parse_dates={'datetime': ['date', 'time']})

# remove email column
df = df.drop('n/a', axis=1)

# set string all lowercase for ease
df['string'] = df['string'].str.lower()

# replace ? with ,
df['string'] = df['string'].str.replace('?', ',')

# remove =
df['string'] = df['string'].str.replace('=', '')

# remove leading _
df['string'] = df['string'].str.lstrip('_')

# remove obscure ending beginning with 'boundary'
df['string'] = df['string'].str.replace(r'\s+boundary"----', '', regex=True)

# remove obscure ending beginning with 'nextpart'
df['string'] = df['string'].str.replace(
    r'_nextpart_[\d\w]{8}_[\d\w]{8}_[\d\w]{8}"', '', regex=True)

# remove obscure ending beginning with 'part
df['string'] = df['string'].str.replace(
    r'_part_\d{8}_\d{10}.\d{13}"', '', regex=True)

# remove any remaining "
df['string'] = df['string'].str.replace('"', '')

# remove erroneous 'phas' or 'spce' from string
df['string'] = df['string'].str.replace('phas|spce', '')

# insert missing delimeters
# i.e. 'student, coursephrase' -> 'student, course, phrase'
df['string'] = df['string'].str.replace(
    r'(\d{8}\s*,?\s*\d{4})(\w{4})', r'\1,\2', regex=True)
# i.e. 'studentcourse, phrase' -> 'student, course, phrase'
df['string'] = df['string'].str.replace(
    r'(\d{8})(\d{4}\s*,?\s*\w{4})', r'\1,\2', regex=True)
# i.e. 'studentcoursephrase' -> 'student, course, phrase'
df['string'] = df['string'].str.replace(
    r'(\d{8})(\d{4})(\w{4})', r'\1,\2,\3', regex=True)

# replace comma with space
df['string'] = df['string'].str.replace(',', ' ')

# switch order if input incorrectly
# i.e. 'student, phrase, course' -> 'student, course, phrase'
df['string'] = df['string'].str.replace(
    r'(\d{4,}\s+)(.{4}\s+)(\d{4})', r'\1 \3 \2', regex=True)

# if forgot the course code force phrase in correct column
# i.e. 'student, phrase' -> 'student, , phrase'
df['string'] = df['string'].str.replace(
    r'(\d{6,}\s+)(.{4})(?!.{4})', r'\1 -1 \2', regex=True)

# split first column into three
df = pd.concat([df['string'].str.split(expand=True), df['datetime']], axis=1)

# set names of columns
df.columns = ['student', 'course', 'phrase', 'datetime']

# if course is 4< characters remove first digit (usually zero)
df['course'] = df['course'].str.replace(r'(\d+)(\d{4})', r'\2', regex=True)

# remove course if not a number, set to -1
df['course'] = df['course'].str.replace(r'\D{4}', '-1', regex=True)

df.to_csv('textwall_sample_output.csv')
print(df)
