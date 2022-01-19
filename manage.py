# TODO implement the module
import argparse
import os
import subprocess

parser = argparse.ArgumentParser(description=None)
parser.add_argument('--runserver', action='store_true', help='run server')
args = parser.parse_args()


def main():
    if args.runserver:
        subprocess.run(['py', '../coffefu_webhook/start_bot_webhook.py'])
        os.system('uvicorn server:app --host 0.0.0.0 --reload')


if __name__ == '__main__':
    main()
