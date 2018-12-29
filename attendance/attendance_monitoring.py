import os
import pandas as pd
import datetime as dt
import numpy as np


def sort_textwall_output(csv_textwall):
    # read in csv
    df = pd.read_csv(csv_textwall, header=None, names=[
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
    df.columns = ['student', 'module', 'phrase', 'datetime']
    false_df.columns = ['student', 'module', 'phrase', 'datetime']

    # find difference between first textwall and current
    difference = df['datetime'] - \
        df.groupby(['module', 'phrase'])['datetime'].transform('min')

    # create easy to read collumns of difference
    df['delta_sec'] = difference.dt.seconds

    # sort by module/phrase/datetime
    df.sort_values(by=['module', 'phrase', 'datetime'], inplace=True)
    false_df.sort_values(by=['module', 'phrase', 'datetime'], inplace=True)

    # save outputs and errors
    filename_noext = os.path.splitext(csv_textwall)[0]
    df.to_csv(filename_noext + '_output.csv')
    false_df.to_csv(filename_noext + '_errors.csv')

    return df, false_df


def calculate_weeks(starting_monday):
    # starting_monday in format of '26-12-2018'
    mon = [int(x) for x in starting_monday.split('-')]
    monday = pd.Timestamp(mon[2], mon[1], mon[0])
    week = dt.timedelta(days=7)
    mondays = [monday + x * week for x in range(12)]
    weeks = {k + 1: [mondays[k], mondays[k + 1]]
             for k, v in enumerate(mondays[:-1])}
    return weeks


def week_number(rec, starting_monday):
    weeks = calculate_weeks(starting_monday)
    for num, dates in weeks.items():
        if dates[0] <= rec['datetime'] and dates[1] > rec['datetime']:
            return num


def split_textwall_weeks(csv_textwall, starting_monday):
    # starting_monday in format of '26-12-2018'
    df, _ = sort_textwall_output(csv_textwall)
    weeks = calculate_weeks(starting_monday)
    df['week'] = df.apply(lambda row: week_number(
        row, starting_monday), axis=1)
    return df


def create_yeargroup_table(csv_student, csv_textwall, starting_monday):
    # get all valid output from textwall
    df_textwall = split_textwall_weeks(csv_textwall, starting_monday)

    # create copy column with different name for grouping
    df_textwall['delta_sec_copy'] = df_textwall['delta_sec']

    # read in csv_student and get headings
    df_student = pd.read_csv(csv_student, dtype=str)
    csv_headings = df_student.columns.values

    # number of weeks
    num_cols = 11

    # column names
    col_names = [('week' + str(i + 1) + '_count', 'week' +
                  str(i + 1) + '_mean') for i in range(num_cols)]
    cols = [e for l in col_names for e in l]

    # calculate count and mean grouped by student number and week
    df_textwall_grouped = df_textwall.groupby(['student', 'week']).agg({'delta_sec': 'size', 'delta_sec_copy': 'mean'}).rename(
        columns={'delta_sec': 'count', 'delta_sec_copy': 'mean'}).reset_index()

    # populate df_output with values frpom df_textwall_year_group https://stackoverflow.com/questions/53961242/how-to-merge-two-pandas-dataframes-based-on-a-value-in-one-row-and-with-differen
    # pivot df2 to format it like df1
    s = df_textwall_grouped.pivot(
        index='student', columns='week', values=['count', 'mean'])
    # modify the column names
    s.columns = s.columns.map('week{0[1]}_{0[0]}'.format)

    # loop through each heading
    for year_group in csv_headings:
        # get respective year group and remove trailing entries
        student_numbers = df_student[year_group].dropna()

        # num of rows in output
        num_rows = len(student_numbers)

        # initialise df of zeros
        df_output = pd.DataFrame(0, index=np.arange(
            num_rows), columns=['student'] + cols)

        # set first column as student numbers
        df_output['student'] = student_numbers

        # perform update
        df_output = df_output.set_index('student')
        df_output.update(s)

        # change all _count columns to int rather than float
        df_output[df_output.columns[::2]
                  ] = df_output[df_output.columns[::2]].astype(int)

        # round all _mean columns to an int
        df_output[df_output.columns[1::2]
                  ] = df_output[df_output.columns[1::2]].round(0).astype(int)

        # save each year group to a csv
        filename_noext = os.path.splitext(csv_textwall)[0]
        filename = filename_noext + '_' + year_group + '.csv'
        df_output.to_csv(filename)


def create_module_table(csv_module, csv_textwall, starting_monday):
    # get all valid output from textwall
    df_textwall = split_textwall_weeks(csv_textwall, starting_monday)

    # read in csv_module and get headings
    df_module = pd.read_csv(csv_module, dtype=str)

    # number of weeks
    num_cols = 11

    # column names
    cols = ['week' + str(i + 1) + '_count' for i in range(num_cols)]

    # calculate count and mean grouped by student number and week
    df_textwall_grouped = df_textwall.groupby(['module', 'week']).agg(
        {'delta_sec': 'size'}).rename(columns={'delta_sec': 'count'}).reset_index()

    # populate df_output with values frpom df_textwall_year_group https://stackoverflow.com/questions/53961242/how-to-merge-two-pandas-dataframes-based-on-a-value-in-one-row-and-with-differen
    # pivot df2 to format it like df1
    s = df_textwall_grouped.pivot(
        index='module', columns='week', values='count')
    # modify the column names
    s.columns = s.columns.map('week{0}_count'.format)

    # calculate the union of module codes
    df_merged = df_module.merge(df_textwall_grouped, how='outer', sort=True)
    module_codes = df_merged['module']

    # num of rows in output
    num_rows = len(module_codes)

    # initialise df of zeros
    df_output = pd.DataFrame(0, index=np.arange(
        num_rows), columns=['module'] + cols)

    # set first column as module codes
    df_output['module'] = module_codes

    # perform update
    df_output = df_output.set_index('module')
    df_output.update(s)

    # save each year group to a csv
    filename_noext = os.path.splitext(csv_textwall)[0]
    filename = filename_noext + '_modules.csv'
    df_output.to_csv(filename)


if __name__ == '__main__':
    create_yeargroup_table('student_numbers.csv',
                           'textwall_sample.csv', '01-10-2018')
    create_module_table('module_codes.csv',
                        'textwall_sample.csv', '01-10-2018')
