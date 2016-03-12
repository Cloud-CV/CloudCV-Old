# Install dependencies
sudo apt-get install -y gfortran git wget unzip build-essential

INSTALL_DIR=$(pwd)/dep
mkdir -p $INSTALL_DIR/caffe
mkdir -p $INSTALL_DIR/opencv

# Download source code
# git clone https://github.com/graphlab-code/graphlab.git
cd $INSTALL_DIR
wget https://github.com/BVLC/caffe/archive/rc2.zip && unzip -qq rc2 && mv caffe-rc2/* caffe && rm rc2.zip
wget -O OpenCV-2.4.11.zip http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.11/opencv-2.4.11.zip/download && unzip -qq OpenCV-2.4.11.zip && mv opencv-2.4.11 opencv && rm OpenCV-2.4.11.zip

# OpenCV Installation
# OpenCV dependencies
sudo apt-get install -y cmake libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
sudo apt-get install -y python-numpy libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libjasper-dev libdc1394-22-dev

cd $INSTALL_DIR/opencv && \
    mkdir release && \
    cd release && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local .. && \
    make -j 4 && \
    make install

# Caffe installation
# Caffe dependencies
sudo apt-get install -y libprotobuf-dev libleveldb-dev libsnappy-dev libopencv-dev libhdf5-serial-dev
sudo apt-get install -y --no-install-recommends libboost-all-dev
sudo apt-get install -y libatlas-base-dev
sudo apt-get install -y libgflags-dev libgoogle-glog-dev liblmdb-dev protobuf-compiler
for req in $(cat $INSTALL_DIR/caffe/python/requirements.txt)
do
    pip install $req
done

cd $INSTALL_DIR/caffe && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j 4 all

# In order to import caffe in python
export PYTHONPATH=$PYTHONPATH:$INSTALL_DIR/caffe/python

# Copying the required caffe model
wget -nc -P $INSTALL_DIR/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel http://dl.caffe.berkeleyvision.org/bvlc_reference_caffenet.caffemodel

export C_FORCE_ROOT=TRUE
# CMD ["celery","-A","celeryTasks","worker","--loglevel=debug", "--logfile=/CloudCV_Server/celery.log"]
