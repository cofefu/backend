# TODO implement the module
import sys
import uvicorn


def main():
    if 'runserver' in sys.argv:
        uvicorn.run(
            'server:app',
            port=8001,
            # ssl_certfile=WEBHOOK_SSL_CERT,
            # ssl_keyfile=WEBHOOK_SSL_PRIV,
            log_level='info'
        )


if __name__ == '__main__':
    main()
