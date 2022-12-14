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

COPY db/ /code/db/
COPY static/ /code/static/
COPY fastapiProject/ /code/fastapiProject/
COPY app/ /code/app/
COPY bot/ /code/bot/
# COPY tests/ /code/tests/

# Copy files

COPY --from=builder /code/wheels /wheels
COPY --from=builder /code/requirements.txt .

RUN pip install --no-cache /wheels/*

CMD ["python3", "manage.py", "--runserver"]
