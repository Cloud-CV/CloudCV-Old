# Install dependencies
sudo apt-get install -y gfortran git wget unzip build-essential

# Download source code
# git clone https://github.com/graphlab-code/graphlab.git
wget -O $(pwd)/dep/rc2.zip https://github.com/BVLC/caffe/archive/rc2.zip && unzip $(pwd)/dep/rc2 && mv $(pwd)/dep/caffe-rc2 $(pwd)/dep/caffe && rm $(pwd)/dep/rc2.zip
wget -O $(pwd)/dep/OpenCV-2.4.11.zip http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.11/opencv-2.4.11.zip/download && unzip $(pwd)/dep/OpenCV-2.4.11.zip && mv $(pwd)/dep/opencv-2.4.11 $(pwd)/dep/opencv && rm $(pwd)/dep/OpenCV-2.4.11.zip

# OpenCV Installation
# OpenCV dependencies
sudo apt-get install -y cmake libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
sudo apt-get install -y python-numpy libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libjasper-dev libdc1394-22-dev

cd $(pwd)/dep/opencv && \
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
for req in $(cat $(pwd)/dep/caffe/python/requirements.txt)
do
    pip install $req
done

cd $(pwd)/dep/caffe && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j 4 all 

# In order to import caffe in python
export PYTHONPATH=$PYTHONPATH:$(pwd)/dep/caffe/python

# Copying the required caffe model
cp $(pwd)/dep/caffe/build/bvlc_reference_caffenet.caffemodel $(pwd)/dep/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel

export C_FORCE_ROOT=TRUE
# CMD ["celery","-A","celeryTasks","worker","--loglevel=debug", "--logfile=/CloudCV_Server/celery.log"]
