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
  echo "Error Catch Point: 1"
  cd opencv
  echo "Error Catch Point: 2"
  mkdir release
  echo "Error Catch Point: 3"
  cd release
  echo "Error Catch Point: 4"
  cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local ..
  echo "Error Catch Point: 5"
  make -j 4
  echo "Error Catch Point: 6"
  make install
  echo "Error Catch Point: 7"
else
  echo 'Using cached directory for OpenCV Installation.';
fi
