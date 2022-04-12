# TODO implement the module
import sys
import uvicorn


def main():
    if 'runserver' in sys.argv:
        uvicorn.run(
            'main:app',
            port=8000,
            # ssl_certfile=WEBHOOK_SSL_CERT,
            # ssl_keyfile=WEBHOOK_SSL_PRIV,
            log_level='info',
            reload=True,
        )


if __name__ == '__main__':
    main()
