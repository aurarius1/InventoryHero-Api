FROM python:3.11-alpine
LABEL authors="codewizards"
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN apk add --no-cache --virtual build-deps gcc musl-dev pkgconf mariadb-dev && \
    apk add --no-cache mariadb-connector-c-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del build-deps

ENV PUID 1000
ENV PGID 1000

COPY /docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
COPY /app /app

EXPOSE 5000
RUN chmod +x /entrypoint.sh