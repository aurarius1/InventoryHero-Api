FROM python:3.11-alpine
LABEL authors="codewizards"

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

ENV PUID 1000
ENV PGID 1000

COPY /docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
COPY /app /app

EXPOSE 5000
RUN chmod +x /entrypoint.sh