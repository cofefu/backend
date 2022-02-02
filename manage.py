# TODO implement the module
import sys
import uvicorn

from backend.settings import SERVER_HOST, SERVER_PORT


def main():
    if 'runserver' in sys.argv:
        uvicorn.run(
            'server:app',
            host=SERVER_HOST,
            port=SERVER_PORT,
            log_level='info'
        )


if __name__ == '__main__':
    main()
