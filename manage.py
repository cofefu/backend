# TODO implement the module
import argparse
import os

parser = argparse.ArgumentParser(description=None)
parser.add_argument('--runserver', action='store_true', help='run server')
args = parser.parse_args()


def main():
    if args.runserver:
        os.system('uvicorn backend.server:app --host 0.0.0.0 --reload')


if __name__ == '__main__':
    main()
