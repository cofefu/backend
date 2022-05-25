FROM python:3.10

WORKDIR /code

# Copy folders

COPY app/ /code/app/
COPY bot/ /code/bot/
COPY db/ /code/db/
COPY static/ /code/static/
COPY fastapiProject/ /code/fastapiProject/
# COPY tests/ /code/tests/

# Copy files

COPY manage.py /code/
COPY requirements.txt /code/


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["python3", "manage.py", "--runserver"]