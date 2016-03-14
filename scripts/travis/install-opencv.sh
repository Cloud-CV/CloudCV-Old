#!/bin/bash
# This script must be run with sudo.

set -e

# Install dependencies
sudo apt-get install build-essential cmake git pkg-config
sudo apt-get install libjpeg8-dev libtiff4-dev libjasper-dev libpng12-dev
sudo apt-get install libgtk2.0-dev
sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt-get install libatlas-base-dev gfortran
sudo apt-get install python2.7-dev

# clone source
cd ~
git clone https://github.com/Itseez/opencv.git
cd opencv
git checkout 3.0.0

# SIFT SURF are in opencv_contrib.git
cd ~
git clone https://github.com/Itseez/opencv_contrib.git
cd opencv_contrib
git checkout 3.0.0

cd ~/opencv
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=RELEASE \
 -DOPENCV_EXTRA_MODULES_PATH=~/github/opencv_contrib/modules \
 -DWITH_TBB=ON \
 -DBUILD_NEW_PYTHON_SUPPORT=ON \
 -DINSTALL_C_EXAMPLES=ON \
 -DINSTALL_PYTHON_EXAMPLES=ON \
 -DBUILD_EXAMPLES=ON \
 -DWITH_CUDA=OFF \
 -DBUILD_TIFF=ON \
 -DCMAKE_INSTALL_PREFIX=$(python -c "import sys; print(sys.prefix)") \
 -DPYTHON_EXECUTABLE=$(which python) \
 -DPYTHON_INCLUDE_DIR=$(python -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
 -DPYTHON_PACKAGES_PATH=$(python3 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
 <strong><span style="color: #ff0000;">..</span></strong>

make -j4
sudo make install
sudo ldconfig

# check if .so are installed in your specified location
# ex. cv2.so should be installed into
# /home/wew57/anaconda/lib/python2.7/site-packages/cv2.so

# CMD ["celery","-A","celeryTasks","worker","--loglevel=debug", "--logfile=/CloudCV_Server/celery.log"]

