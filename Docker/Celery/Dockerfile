FROM tleyden5iwx/caffe-cpu-master:latest

MAINTAINER Prashant Jalan

RUN groupadd user && useradd --create-home --home-dir /home/user -g user user
WORKDIR /home/user

COPY ./requirements.txt /home/user/requirements.txt

#Install dependencies for CloudCV Server
RUN pip install -r /home/user/requirements.txt

#Install OpenCV for Python
RUN apt-get update
RUN apt-get -y install python-opencv

COPY ./bvlc_reference_caffenet.caffemodel /opt/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel

RUN usermod -a -G root user
USER user
WORKDIR /CloudCV_Server
CMD ["celery","-A","app.celery.celery.celery","worker","--loglevel=info"]
