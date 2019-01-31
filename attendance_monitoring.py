from __future__ import print_function, division
import os
import pandas as pd
import datetime as dt
import numpy as np
from argparse import ArgumentParser


class AttendanceMonitoring:
    def __init__(self, csv_textwall, csv_student, csv_module, starting_monday):
        self.csv_textwall = csv_textwall
        self.csv_student = csv_student
        self.csv_module = csv_module
        self.starting_monday = starting_monday
        self.output_folder = 'output'
        self.number_weeks = 52  # i.e. a year
        self.weeks = self.calculate_weeks()
        self.df_textwall = self.split_textwall_weeks()

    def sort_textwall_output(self):
        # read in csv
        # not using parse_dates because sometimes
        # the format of the data doesn't work
        df = pd.read_csv(self.csv_textwall, names=[
                         'string', 'n/a', 'date', 'time'])

        # remove email column
        df.drop('n/a', axis=1, inplace=True)

        # clean up date column
        df['date'] = df['date'].str.replace('=', '')
        df['date'] = df['date'].str.replace('"', '')

        # clean up time column
        df['time'] = df['time'].str.replace('=', '')
        df['time'] = df['time'].str.replace('"', '')

        # create datetime column and drop date and time columns
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        df = df.drop('date', axis=1)
        df = df.drop('time', axis=1)

        # set string all lowercase for ease
        df['string'] = df['string'].str.lower()

        # replace ? with ,
        df['string'] = df['string'].str.replace('?', ',')

        # replace . with ,
        df['string'] = df['string'].str.replace('.', ',')

        # remove =
        df['string'] = df['string'].str.replace('=', '')

        # remove "
        df['string'] = df['string'].str.replace('"', '')

        # remove double comma
        df['string'] = df['string'].str.replace(',,', ',')

        # remove leading _
        df['string'] = df['string'].str.lstrip('_')

        # remove leading :
        df['string'] = df['string'].str.lstrip(':')

        # remove leading ,
        df['string'] = df['string'].str.lstrip(',')

        # remove leading whitespace
        df['string'] = df['string'].str.lstrip()

        # remove pattern of 'a 12345678,' i.e. startin with a letter
        df['string'] = df['string'].str.replace(r'^\S\s+', '', regex=True)

        # remove obscure ending beginning with 'boundary'
        df['string'] = df['string'].str.replace('boundary----', '')

        # remove obscure ending beginning with 'nextpart'
        df['string'] = df['string'].str.replace(
            r'_nextpart_\S+_\S+_\S+', '', regex=True)

        # remove obscure ending beginning with 'part
        df['string'] = df['string'].str.replace(
            r'_part_\d+_\d+,\d+', '', regex=True)

        # remove erroneous 'phas' or 'spce' from string
        df['string'] = df['string'].str.replace('phas|pha|phs|pgas|spce', '')

        # correct_format = df['string'].str.match(
        correct_format = df['string'].str.match(
            r'^\d{8}(\s*,\s*|\s+)\d+(\s*,\s*|\s+)[\w\d\$\!\+\@\-\*\&\'\/\,]{3,}\s*$')
        false_df = df[~correct_format].copy()
        correct_df = df[correct_format].copy()

        # replace comma with space
        false_df['string'] = false_df['string'].str.replace(',', ' ')
        correct_df['string'] = correct_df['string'].str.replace(',', ' ')

        # split first column into three
        correct_df = pd.concat(
            [correct_df['datetime'], correct_df['string'].str.split(expand=True)], axis=1)
        false_df = pd.concat(
            [false_df['datetime'], false_df['string'].str.split(expand=True)], axis=1)

        # check if there is a largely None column (based on input csv)
        if len(correct_df.columns) == 5:
            # test if final column is not None
            indices = correct_df.iloc[:, -1].isnull()
            failures = correct_df[~indices]
            # add failures to false_df
            false_df = pd.concat([false_df, failures], sort=False)
            # remove failures from correct_df
            correct_df = correct_df[indices]
            # drop redundant column
            correct_df = correct_df[correct_df.columns[:-1]]

        # set names of columns
        col_names = ['datetime', 'student', 'module', 'phrase']
        correct_df.columns = col_names
        columns = {i: col_names[i + 1] for i in range(len(col_names) - 1)}
        false_df.rename(index=str, columns=columns, inplace=True)

        # make modules an int into a new column
        correct_df['int_module'] = pd.to_numeric(
            correct_df['module'], downcast='integer')

        # read in csv_module - list of modules
        df_module = pd.read_csv(self.csv_module, dtype=int)

        # only keep valid module codes
        cols_to_use = correct_df.columns.difference(df_module.columns)
        df_merged = df_module.merge(
            correct_df, how='outer', left_on='module', right_on='int_module', indicator=True)

        # adjust names of columns
        df_merged.drop('module_x', axis=1, inplace=True)
        df_merged.rename(index=str, columns={
                         'module_y': 'module'}, inplace=True)

        # add invalid module codes to false_df
        invalid_modules = df_merged.query('_merge == "right_only"').copy()
        invalid_modules.drop(['int_module', '_merge'], axis=1, inplace=True)
        false_df = pd.concat([false_df, invalid_modules], sort=False)

        # remove invalid modules and reformat columns
        df_valid_modules = df_merged.query('_merge == "both"').copy()
        df_valid_modules.drop(['module', '_merge'], axis=1, inplace=True)
        df_valid_modules.rename(
            index=str, columns={'int_module': 'module'}, inplace=True)

        # find difference between first textwall and current
        difference = df_valid_modules['datetime'] - \
            df_valid_modules.groupby(['module', 'phrase'])[
            'datetime'].transform('min')

        # create easy to read collumns of difference
        df_valid_modules['delta_hour'] = difference.dt.seconds / 3600

        # sort by module/phrase/datetime
        df_valid_modules.sort_values(
            by=['module', 'phrase', 'datetime'], inplace=True)

        # save outputs and errors
        self.save_csv(df_valid_modules, 'output',
                      'Full valid cleaned textwall output')
        self.save_csv(false_df, 'errors', 'Failed textwall entries')

        return df_valid_modules, false_df

    def calculate_weeks(self):
        # starting_monday in format of '26-12-2018'
        monday = pd.Timestamp(self.starting_monday)
        week = dt.timedelta(days=7)
        mondays = [monday + x * week for x in range(self.number_weeks + 1)]
        weeks = {k + 1: [mondays[k], mondays[k + 1]]
                 for k, v in enumerate(mondays[:-1])}
        return weeks

    def week_number(self, rec):
        for num, dates in self.weeks.items():
            if dates[0] <= rec['datetime'] and dates[1] > rec['datetime']:
                return num

    def split_textwall_weeks(self):
        # starting_monday in format of '2018-08-27'
        df, _ = self.sort_textwall_output()
        df['week'] = df.apply(lambda row: self.week_number(row), axis=1)
        return df

    def create_yeargroup_table(self):
        # get all valid output from textwall
        df = self.df_textwall

        # create copy column with different name for grouping
        df['delta_hour_copy'] = df['delta_hour']

        # calculate count and mean grouped by student number and week
        df_textwall_grouped = df.groupby(['student', 'week']).agg({'delta_hour': 'size', 'delta_hour_copy': 'mean'}).rename(
            columns={'delta_hour': 'count', 'delta_hour_copy': 'mean'}).reset_index()

        # populate df_output with values frpom df_textwall_year_group https://stackoverflow.com/questions/53961242/how-to-merge-two-pandas-dataframes-based-on-a-value-in-one-row-and-with-differen
        # pivot df2 to format it like df1
        s = df_textwall_grouped.pivot(
            index='student', columns='week', values=['count', 'mean'])
        # modify the column names
        s.columns = s.columns.map('week{0[1]}_{0[0]}'.format)

        # column names
        col_names = [('week' + str(i + 1) + '_count', 'week' +
                      str(i + 1) + '_mean') for i in range(self.number_weeks)]
        cols = [e for l in col_names for e in l]

        # read in csv_student and get headings
        df_student = pd.read_csv(self.csv_student, dtype=str)
        csv_headings = df_student.columns.values

        # loop through each heading
        for year_group in csv_headings:
            # get respective year group and remove trailing entries
            student_numbers = df_student[year_group].dropna()

            # create table
            self.year_group_table(year_group, cols, s, student_numbers)

        # find all students not in df_student but in s
        all_csv_values = df_student.values.flatten()
        student_array = all_csv_values[~pd.isnull(all_csv_values)]
        df_contained = pd.DataFrame(student_array, columns=['student'])

        # only keep missing students
        df_merged = df_contained.merge(
            df_textwall_grouped, how='outer', indicator=True)
        df_missing = df_merged.query('_merge == "right_only"').copy()
        df_missing.drop(['_merge'], axis=1, inplace=True)
        missing_students = df_missing['student'].unique()

        # save missing students in table
        self.year_group_table('missing_students', cols, s, missing_students)

    def year_group_table(self, heading, column_names, s, student_numbers):
        # num of rows in output
        num_rows = len(student_numbers)

        # initialise df of zeros
        df_output = pd.DataFrame(0, index=np.arange(
            num_rows), columns=['student'] + column_names)

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
        self.save_csv(df_output, heading, 'Sorted by year group')

    def create_module_table(self):
        # get all valid output from textwall
        df = self.df_textwall

        # read in csv_module - list of modules
        df_module = pd.read_csv(self.csv_module, dtype=int)
        module_codes = df_module['module']

        # calculate count and mean grouped by student number and week
        df_textwall_grouped = df.groupby(['module', 'week']).agg(
            {'delta_hour': 'size'}).rename(columns={'delta_hour': 'count'}).reset_index()

        # populate df_output with values frpom df_textwall_year_group https://stackoverflow.com/questions/53961242/how-to-merge-two-pandas-dataframes-based-on-a-value-in-one-row-and-with-differen
        # pivot df2 to format it like df1
        s = df_textwall_grouped.pivot(
            index='module', columns='week', values='count')
        # modify the column names
        s.columns = s.columns.map('week{0}_count'.format)

        # num of rows in output
        num_rows = len(module_codes)

        # column names
        cols = ['week' + str(i + 1) +
                '_count' for i in range(self.number_weeks)]

        # initialise df of zeros
        df_output = pd.DataFrame(0, index=np.arange(
            num_rows), columns=['module'] + cols)

        # set first column as module codes
        df_output['module'] = module_codes

        # perform update
        df_output = df_output.set_index('module')
        df_output.update(s)

        # save each year group to a csv
        self.save_csv(df_output, 'modules', 'Sorted by module codes')

    def save_csv(self, dataframe, ending, print_message):
        filename_no_folder = os.path.basename(self.csv_textwall)
        filename_no_extension = os.path.splitext(filename_no_folder)[0]
        filename = filename_no_extension + '_' + ending + '.csv'
        __location__ = os.path.realpath(os.path.join(
            os.getcwd(), os.path.dirname(__file__)))
        path = os.path.join(__location__, self.output_folder, filename)
        dataframe.to_csv(path)
        print(print_message + ': {0}'.format(path))


def process(csv_textwall, csv_student, csv_module, starting_monday):
    am = AttendanceMonitoring(
        csv_textwall, csv_student, csv_module, starting_monday)
    am.create_yeargroup_table()
    am.create_module_table()


def valid_date(s):
    try:
        date = dt.datetime.strptime(s, '%Y-%m-%d')
        # test if Monday
        if date.weekday() == 0:
            return date
        else:
            raise ValueError('Date not a Monday')
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


if __name__ == '__main__':
    parser = ArgumentParser(description='Sort textwall output')
    parser.add_argument('csv_textwall', metavar='csv_textwall',
                        type=str, help='textwall output')
    parser.add_argument('csv_student', metavar='csv_student',
                        type=str, help='students by year group')
    parser.add_argument('csv_module', metavar='csv_module',
                        type=str, help='module codes')
    parser.add_argument('starting_monday', metavar='starting_monday', type=valid_date, nargs='?',
                        default='2018-08-27', help='starting monday of the year - format YYYY-MM-DD (defaults to 2018-08-27)')
    args = parser.parse_args()
    process(args.csv_textwall, args.csv_student,
            args.csv_module, args.starting_monday)
