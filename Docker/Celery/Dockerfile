FROM cloudcv/base:latest

MAINTAINER Prashant Jalan

COPY ./bvlc_reference_caffenet.caffemodel /opt/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel

ENV C_FORCE_ROOT TRUE

WORKDIR /CloudCV_Server
CMD ["celery","app.celery.celery.celery","worker","--loglevel=info"]