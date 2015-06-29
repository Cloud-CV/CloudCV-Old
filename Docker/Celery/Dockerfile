FROM cloudcv/base:latest

MAINTAINER Prashant Jalan

COPY ./bvlc_reference_caffenet.caffemodel /opt/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel
COPY ./conf /etc/default/celeryd
COPY ./generic-init.d /etc/init.d/celeryd

#Make the init.d script of celery executable
RUN chmod 755 /etc/init.d/celeryd

ENV C_FORCE_ROOT TRUE

CMD ["/etc/init.d/celeryd","start"]