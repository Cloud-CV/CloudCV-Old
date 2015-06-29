FROM tleyden5iwx/caffe-cpu-master:latest

MAINTAINER Prashant Jalan

COPY ./requirements.txt /requirements.txt

#Install dependencies for CloudCV Server
RUN pip install -r /requirements.txt

#Install OpenCV for Python
RUN apt-get update
RUN apt-get -y install python-opencv

RUN git clone https://github.com/batra-mlp-lab/CloudCV_Server.git --branch Docker