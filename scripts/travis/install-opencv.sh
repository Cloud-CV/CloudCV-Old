#!/bin/bash
# This script must be run with sudo.

set -e

echo "############################################"
echo $HOME
echo "############################################"

# check to see if protobuf folder is empty
cd ~
if [ ! -d "opencv/release" ]; then
  # Install dependencies
  apt-get install -y gfortran git wget unzip build-essential

  # OpenCV dependencies
  apt-get install -y cmake libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
  apt-get install -y python-numpy libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libjasper-dev libdc1394-22-dev

  # Download Opencv source code
  wget -O OpenCV-2.4.11.zip http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.11/opencv-2.4.11.zip/download && unzip -qq OpenCV-2.4.11.zip && mv opencv-2.4.11 opencv && rm OpenCV-2.4.11.zip

  # OpenCV Installation
  cd opencv && \
      mkdir release && \
      cd release && \
      cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local .. && \
      make -j 4 && \
      make install
else
  echo 'Using cached directory for OpenCV Installation.';
fi
