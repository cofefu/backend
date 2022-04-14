# TODO implement the module
import argparse
import uvicorn

from backend.settings import SERVER_PORT

# init parser
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--runserver', action='store_true')
args = parser.parse_args()


def main():
    if args.runserver:
        uvicorn.run(
            'main:app',
            port=SERVER_PORT,
            log_level='info',
            workers=1,
        )


if __name__ == '__main__':
    main()
