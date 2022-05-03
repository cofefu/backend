# TODO implement the module
import argparse
import uvicorn

from fastapiProject.settings import SERVER_PORT, WORKERS

# init parser
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--runserver', action='store_true')
args = parser.parse_args()


def main():
    if args.runserver:
        uvicorn.run(
            'fastapiProject.main:app',
            port=SERVER_PORT,
            log_level='info',
            workers=WORKERS,
        )


if __name__ == '__main__':
    main()
