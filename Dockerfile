FROM python:3.10-alpine as builder

WORKDIR /code

COPY requirements.txt /code/

RUN pip install -U pip
#RUN pip install --no-cache-dir -r /code/requirements.txt
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /code/wheels -r requirements.txt


FROM python:3.10-alpine

WORKDIR /code

# Copy folders

COPY manage.py /code/

COPY src/ /code/src
COPY alembic/ /code/alembic
COPY alembic.ini /code/

# Copy files

COPY --from=builder /code/wheels /wheels
COPY --from=builder /code/requirements.txt .

RUN pip install --no-cache /wheels/*

CMD alembic upgrade head;python3 manage.py --runserver
