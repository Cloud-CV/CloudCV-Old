INSTALL_DIR=$(pwd)/dep
mkdir -p $INSTALL_DIR/caffe
mkdir -p $INSTALL_DIR/opencv

# Install dependencies
sudo -E ./scripts/travis/travis_install.sh
cd $INSTALL_DIR
# change permissions for installed python packages
sudo chown $USER -R ~/miniconda
sudo chown $USER -R ~/.cache

# Download Opencv source code
wget -O OpenCV-2.4.11.zip http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.11/opencv-2.4.11.zip/download && unzip -qq OpenCV-2.4.11.zip && mv opencv-2.4.11 opencv && rm OpenCV-2.4.11.zip

# OpenCV Installation
cd $INSTALL_DIR/opencv && \
    mkdir release && \
    cd release && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local .. && \
    make -j 4 && \
    make install

# Caffe installation
wget https://github.com/BVLC/caffe/archive/rc2.zip && unzip -qq rc2 && mv caffe-rc2/* caffe && rm rc2.zip
cd $INSTALL_DIR/caffe

# Build source
cp Makefile.config.example Makefile.config
sed -i 's/# CPU_ONLY/CPU_ONLY/g' Makefile.config
sed -i 's/USE_CUDNN/#USE_CUDNN/g' Makefile.config

# Use miniconda
sed -i 's/# ANACONDA_HOME/ANACONDA_HOME/' Makefile.config
sed -i 's/# PYTHON_INCLUDE/PYTHON_INCLUDE/' Makefile.config
sed -i 's/# $(ANACONDA_HOME)/$(ANACONDA_HOME)/' Makefile.config
sed -i 's/# PYTHON_LIB/PYTHON_LIB/' Makefile.config
sed -i 's/ANACONDA/MINICONDA/g' Makefile.config
sed -i 's/Anaconda/Miniconda/g' Makefile.config
sed -i 's/anaconda/miniconda/g' Makefile.config
echo 'LINKFLAGS += -Wl,-rpath,/home/travis/miniconda/lib' >> Makefile.config

# compile
mkdir build && cd build && cmake .. && make -j 4 all

# Install python dependencies
# conda (fast)
conda install --yes cython nose ipython h5py pandas python-gflags

for req in $(cat $INSTALL_DIR/caffe/python/requirements.txt)
do
    pip install $req
done
# In order to import caffe in python
export PYTHONPATH=$PYTHONPATH:$INSTALL_DIR/caffe/python

# Copying the required caffe model
mkdir -p $INSTALL_DIR/caffe/models/bvlc_reference_caffenet
wget -nc -P $INSTALL_DIR/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel http://dl.caffe.berkeleyvision.org/bvlc_reference_caffenet.caffemodel

export C_FORCE_ROOT=TRUE
# CMD ["celery","-A","celeryTasks","worker","--loglevel=debug", "--logfile=/CloudCV_Server/celery.log"]
