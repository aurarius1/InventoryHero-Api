FROM python:3.11-alpine
LABEL authors="lukas"

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY /app/* /app

CMD ["python", "./app.py"]