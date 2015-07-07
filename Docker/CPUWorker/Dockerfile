FROM ubuntu:14.04

MAINTAINER Prashant Jalan

# We will install opencv, graphlab and caffe in this container
# This container will run the CPU worker which handles the image classification,
# decaf, POI, image stitching and training a new model.

RUN apt-get update

# graphlab installation

RUN apt-get install -y gcc g++ build-essential libopenmpi-dev default-jdk cmake zlib1g-dev git
RUN git clone https://github.com/batra-mlp-lab/mlp-graphlab.git
RUN mv mlp-graphlab graphlab
RUN cd /graphlab && ./configure
RUN cd /graphlab/release/toolkits/computer_vision && make


#COPY ./bvlc_reference_caffenet.caffemodel /opt/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel

#ENV C_FORCE_ROOT TRUE

#WORKDIR /CloudCV_Server
#CMD ["celery","-A","celeryTasks","worker","--loglevel=info"]
