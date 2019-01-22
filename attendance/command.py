import datetime as dt
from argparse import ArgumentParser
from .attendance_monitoring import process


def main():
    parser = ArgumentParser(description='Sort textwall output')
    parser.add_argument('csv_textwall', metavar='csv_textwall', type=str, help='textwall output')
    parser.add_argument('csv_student', metavar='csv_student', type=str, help='students by year group')
    parser.add_argument('csv_module', metavar='csv_module', type=str, help='module codes')
    parser.add_argument('starting_monday', metavar='starting_monday', type=valid_date, nargs='?', default='2018-08-27', help='starting monday of the year - format YYYY-MM-DD (defaults to 2018-08-27)')
    args = parser.parse_args()
    process(args.csv_textwall, args.csv_student, args.csv_module, args.starting_monday)


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

if __name__ == "__main__":
    main()
