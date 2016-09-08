#!/bin/bash
# This script must be run with sudo.

set -e
rm -r $TOOLS_DIR/opencv

if [ ! -d "$TOOLS_DIR/opencv/build" ]; then
    sudo apt-get update
    sudo apt-get install build-essential cmake git pkg-config
    sudo apt-get install libjpeg8-dev libtiff4-dev libjasper-dev libpng12-dev
    sudo apt-get install libgtk2.0-dev
    sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
    sudo apt-get install libatlas-base-dev gfortran
    sudo apt-get install python2.7-dev
    
    sudo apt-get -qq install checkinstall cmake pkg-config yasm libjpeg-dev libjasper-dev libavcodec-dev libavformat-dev libswscale-dev libdc1394-22-dev libxine-dev libgstreamer0.10-dev libgstreamer-plugins-base0.10-dev libv4l-dev python-dev python-numpy libtbb-dev libqt4-dev libgtk2.0-dev libmp3lame-dev libopencore-amrnb-dev libopencore-amrwb-dev libtheora-dev libvorbis-dev libxvidcore-dev x264 v4l-utils

    # clone source
    cd $TOOLS_DIR
    git clone https://github.com/Itseez/opencv.git
    cd opencv
    git checkout 2.4.11 
    mkdir build
    cd build
 else
  echo 'Using cached directory for OpenCV Installation.';
fi

cd "$TOOLS_DIR/opencv/build"
echo $(python -c "import sys; print(sys.prefix)")
echo $(which python)
echo $(python -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") 
echo $(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")

cmake -DCMAKE_BUILD_TYPE=RELEASE \
   -DWITH_TBB=ON \
   -DBUILD_NEW_PYTHON_SUPPORT=ON \
   -DINSTALL_C_EXAMPLES=OFF \
   -DINSTALL_PYTHON_EXAMPLES=OFF \
   -DBUILD_EXAMPLES=OFF \
   -DWITH_CUDA=OFF \
   -DBUILD_TIFF=ON \
   -DCMAKE_INSTALL_PREFIX=$(python -c "import sys; print(sys.prefix)") \
   -DPYTHON_EXECUTABLE=$(which python) \
   -DPYTHON_INCLUDE_DIR=$(python -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
   -DWITH_OPENGL=ON \
   -DINSTALL_TESTS=ON \
   -DENABLE_FAST_MATH=ON \
   -DWITH_IMAGEIO=ON \
   -DBUILD_SHARED_LIBS=OFF \
   -DPYTHON_PACKAGES_PATH=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") ..

make -j4
make install

