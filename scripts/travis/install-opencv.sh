#!/bin/bash
# This script must be run with sudo.

set -e

# Install dependencies
apt-get install -y gfortran git wget unzip build-essential

# OpenCV dependencies
apt-get install -y cmake libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
apt-get install -y python-numpy libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libjasper-dev libdc1394-22-dev

INSTALL_DIR=$(pwd)/dep
mkdir -p $INSTALL_DIR/opencv

# Install dependencies
cd $INSTALL_DIR

# Download Opencv source code
wget -O OpenCV-2.4.11.zip http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.11/opencv-2.4.11.zip/download && unzip -qq OpenCV-2.4.11.zip && mv opencv-2.4.11 opencv && rm OpenCV-2.4.11.zip

# OpenCV Installation
cd $INSTALL_DIR/opencv && \
    mkdir release && \
    cd release && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local .. && \
    make -j 4 && \
    make install

# In order to import caffe in python
export PYTHONPATH=$PYTHONPATH:$INSTALL_DIR/caffe/python

# Copying the required caffe model
mkdir -p $INSTALL_DIR/caffe/models/bvlc_reference_caffenet
wget -nc -P $INSTALL_DIR/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel http://dl.caffe.berkeleyvision.org/bvlc_reference_caffenet.caffemodel

export C_FORCE_ROOT=TRUE
# CMD ["celery","-A","celeryTasks","worker","--loglevel=debug", "--logfile=/CloudCV_Server/celery.log"]
