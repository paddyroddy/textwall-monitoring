from argparse import ArgumentParser
from .attendance_monitoring import attendance_monitoring


def main():
    parser = ArgumentParser(description='Sort textwall output')
    parser.add_argument('csv_file', metavar='csv_file', type=str, help='csv file to process')
    args = parser.parse_args()
    output, errors = attendance_monitoring(args.csv_file)
    print(output)
    print(errors)

if __name__ == "__main__":
    main()
