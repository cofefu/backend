# TODO implement the module
import argparse
import uvicorn

from src.config.settings import settings

# init parser
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--runserver', action='store_true')
parser.add_argument('--reload', action='store_true')
args = parser.parse_args()


def main():
    if args.runserver:
        uvicorn.run(
            'src.config.main:app',
            port=settings.server_port,
            log_level='info',
            workers=settings.workers,
            host=settings.server_host,
            reload=args.reload
        )


if __name__ == '__main__':
    main()
