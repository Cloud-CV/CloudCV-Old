FROM ubuntu:14.04

MAINTAINER Deshraj

# We will install the bare minimum required to run the django server

# Basics

RUN apt-get update
RUN apt-get install -y build-essential g++ gcc gfortran wget python-dev git libjpeg-dev python-psycopg2 libpq-dev python-matplotlib
RUN wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py && rm get-pip.py

# Install dependencies for CloudCV Server

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
