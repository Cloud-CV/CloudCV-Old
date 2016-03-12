#!/bin/bash
# This script must be run with sudo.

set -e

# Install dependencies
apt-get install -y gfortran git wget unzip build-essential

# OpenCV dependencies
apt-get install -y cmake libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
apt-get install -y python-numpy libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libjasper-dev libdc1394-22-dev

# Caffe dependencies
# This ppa is for gflags and glog
add-apt-repository -y ppa:tuleu/precise-backports
apt-get -y update
apt-get install \
    wget git \
    python-dev python-numpy python3-dev\
    libleveldb-dev libsnappy-dev libopencv-dev \
    libprotobuf-dev protobuf-compiler \
    libatlas-dev libatlas-base-dev \
    libhdf5-serial-dev libgflags-dev libgoogle-glog-dev \
    bc


# Install the Python runtime dependencies via miniconda (this is much faster
# than using pip for everything).
export PATH=$CONDA_DIR/bin:$PATH
# clear any cached conda
rm -rf $CONDA_DIR
if [ ! -d $CONDA_DIR ]; then
	wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh
	chmod +x miniconda.sh
	./miniconda.sh -b -p $CONDA_DIR
	
	conda update --yes conda
	conda install --yes numpy scipy matplotlib scikit-image pip
	# Let conda install boost (so that boost_python matches)
	conda install --yes -c https://conda.binstar.org/menpo boost=1.56.0
fi
