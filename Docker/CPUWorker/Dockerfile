FROM ubuntu:14.04

MAINTAINER Prashant Jalan

# We will install opencv, graphlab and caffe in this container
# This container will run the CPU worker which handles the image classification,
# decaf, POI, image stitching and training a new model.

# Basics

RUN apt-get update
RUN apt-get install -y gfortran git wget unzip python-dev build-essential
RUN wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py && rm get-pip.py

# Download source code

RUN wget https://github.com/BVLC/caffe/archive/rc2.zip && unzip rc2 && mv caffe-rc2 caffe && rm rc2.zip
RUN git clone https://github.com/graphlab-code/graphlab.git
RUN wget -O OpenCV-2.4.11.zip http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.11/opencv-2.4.11.zip/download && unzip OpenCV-2.4.11.zip && mv opencv-2.4.11 opencv && rm OpenCV-2.4.11.zip

# Graphlab installation

# Graphlab dependencies
RUN apt-get install -y gcc g++ build-essential libopenmpi-dev openmpi-bin default-jdk cmake zlib1g-dev gfortran openmpi-checkpoint openmpi-bin

RUN cd /graphlab && ./configure
RUN cd /graphlab/release/toolkits/computer_vision && make

# OpenCV Installation

# OpenCV dependencies
RUN apt-get install -y cmake git libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
RUN apt-get install -y python-dev python-numpy libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libjasper-dev libdc1394-22-dev

RUN cd /opencv && \
    mkdir release && \
    cd release && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local .. && \
    make -j 4 && \
    make install

# Caffe installation

# Caffe dependencies
RUN apt-get install -y libprotobuf-dev libleveldb-dev libsnappy-dev libopencv-dev libhdf5-serial-dev
RUN apt-get install -y --no-install-recommends libboost-all-dev
RUN apt-get install -y libatlas-base-dev
RUN apt-get install -y libgflags-dev libgoogle-glog-dev liblmdb-dev protobuf-compiler
RUN for req in $(cat /caffe/python/requirements.txt); do pip install $req; done

RUN cd /caffe && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j 4 all && \
    make runtest 

#COPY ./bvlc_reference_caffenet.caffemodel /opt/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel

#ENV C_FORCE_ROOT TRUE

#WORKDIR /CloudCV_Server
#CMD ["celery","-A","celeryTasks","worker","--loglevel=info"]
