import pandas as pd
import os


def attendance_monitoring(csv):
    # read in csv
    df = pd.read_csv(csv, header=None, names=[
                     'string', 'n/a', 'date', 'time'], parse_dates={'datetime': ['date', 'time']})

    # remove email column
    df = df.drop('n/a', axis=1)

    # set string all lowercase for ease
    df['string'] = df['string'].str.lower()

    # replace ? with ,
    df['string'] = df['string'].str.replace('?', ',')

    # remove =
    df['string'] = df['string'].str.replace('=', '')

    # remove "
    df['string'] = df['string'].str.replace('"', '')

    # remove leading _
    df['string'] = df['string'].str.lstrip('_')

    # remove leading ,
    df['string'] = df['string'].str.lstrip(',')

    # remove leading whitespace
    df['string'] = df['string'].str.lstrip()

    # remove obscure ending beginning with 'boundary'
    df['string'] = df['string'].str.replace('boundary----', '')

    # remove obscure ending beginning with 'nextpart'
    df['string'] = df['string'].str.replace(
        r'_nextpart_[\d\w]{8}_[\d\w]{8}_[\d\w]{8}', '', regex=True)

    # remove obscure ending beginning with 'part
    df['string'] = df['string'].str.replace(
        r'_part_\d{8}_\d{10}.\d{13}', '', regex=True)

    # remove erroneous 'phas' or 'spce' from string
    df['string'] = df['string'].str.replace('phas|spce', '')

    correct_format = df['string'].str.match(
        r'\d{8}(\s*,\s*|\s+)\d{4}(\s*,\s*|\s+)[\w\d\$]{4,5}')
    false_df = df[~correct_format]
    df = df[correct_format]

    # replace comma with space
    false_df['string'] = false_df['string'].str.replace(',', ' ')
    df['string'] = df['string'].str.replace(',', ' ')

    # split first column into three
    df = pd.concat([df['string'].str.split(
        expand=True), df['datetime']], axis=1)
    false_df = pd.concat([false_df['string'].str.split(
        expand=True), false_df['datetime']], axis=1)

    # set names of columns
    df.columns = ['student', 'course', 'phrase', 'datetime']
    false_df.columns = ['student', 'course', 'phrase', 'datetime']

    # find difference between first textwall and current
    difference = df['datetime'] - \
        df.groupby(['course', 'phrase'])['datetime'].transform('min')

    # create easy to read collumns of difference
    df['delta_sec'] = difference.dt.seconds

    # sort by course/phrase/datetime
    df.sort_values(by=['course', 'phrase', 'datetime'], inplace=True)
    false_df.sort_values(by=['course', 'phrase', 'datetime'], inplace=True)

    filename_noext = os.path.splitext(csv)[0]
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output = os.path.join(output_dir, filename_noext + '_output.csv')
    df.to_csv(output)
    errors_dir = 'errors'
    if not os.path.exists(errors_dir):
        os.makedirs(errors_dir)
    errors = os.path.join(errors_dir, filename_noext + '_errors.csv')
    false_df.to_csv(errors)

    return output, errors
