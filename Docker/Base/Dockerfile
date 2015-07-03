FROM cloudcv/caffe-cpu:latest

MAINTAINER Prashant Jalan

COPY ./requirements.txt /requirements.txt

#Install dependencies for CloudCV Server
RUN pip install -r /requirements.txt

#Install OpenCV for Python
RUN apt-get update
RUN apt-get -y install python-opencv
