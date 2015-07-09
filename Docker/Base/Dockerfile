FROM python:2.7-slim

MAINTAINER Prashant Jalan

# Install django; code from official django library on hub.docker.com

RUN apt-get update && apt-get install -y \
        mysql-client libmysqlclient-dev \
        postgresql-client libpq-dev \
        sqlite3 \
        gcc \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

ENV DJANGO_VERSION 1.8.2

RUN pip install mysqlclient psycopg2 django=="$DJANGO_VERSION"

# Install other dependencies 

RUN apt-get update && apt-get install -y git

#Install dependencies for CloudCV Server
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt