FROM tleyden5iwx/caffe-cpu-master:latest

MAINTAINER Prashant Jalan

COPY ./requirements.txt /requirements.txt

#Install dependencies for CloudCV Server
RUN pip install -r /requirements.txt

#Install OpenCV for Python
RUN apt-get update
RUN apt-get -y install python-opencv

EXPOSE 8000

RUN git clone https://github.com/batra-mlp-lab/CloudCV_Server.git --branch Docker
COPY ./bvlc_reference_caffenet.caffemodel /opt/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel
