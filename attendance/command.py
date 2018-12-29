from argparse import ArgumentParser
from .attendance_monitoring import sort_textwall_output


def main():
    parser = ArgumentParser(description='Sort textwall output')
    parser.add_argument('csv_file', metavar='csv_file', type=str, help='csv file to process')
    args = parser.parse_args()
    sort_textwall_output(args.csv_file)

if __name__ == "__main__":
    main()
