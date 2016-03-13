#/usr/bin/env bash
set -e
set -x

INSTALL_DIR=$(pwd)/deps/caffe
mkdir -p $INSTALL_DIR

NUM_THREADS=${NUM_THREADS-4}

CAFFE_BRANCH="master"
CAFFE_URL="https://github.com/BVLC/caffe.git"

# Install dependencies
./scripts/travis/travis_install_caffe.sh

# Get source
git clone --depth 1 --branch $CAFFE_BRANCH $CAFFE_URL $INSTALL_DIR
cd $INSTALL_DIR


# change permissions for installed python packages
sudo chown $USER -R ~/miniconda
sudo chown $USER -R ~/.cache

# Build source
cp Makefile.config.example Makefile.config
sed -i 's/# CPU_ONLY/CPU_ONLY/g' Makefile.config
sed -i 's/USE_CUDNN/#USE_CUDNN/g' Makefile.config
sed -i 's/# WITH_PYTHON_LAYER/WITH_PYTHON_LAYER/g' Makefile.config

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
make --jobs=$NUM_THREADS all
make --jobs=$NUM_THREADS pycaffe

# Install python dependencies
# conda (fast)
conda install --yes cython nose ipython h5py pandas python-gflags
# pip (slow)
for req in $(cat python/requirements.txt); do
    pip install $req
done
