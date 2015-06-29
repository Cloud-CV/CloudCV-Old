FROM cloudcv/base:latest

MAINTAINER Prashant Jalan

COPY ./bvlc_reference_caffenet.caffemodel /opt/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel

RUN groupadd user && useradd --create-home --home-dir /home/user -g user user
USER user
