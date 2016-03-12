set -e
set -x

if [ "$#" -ne 1 ];
then
    echo "Usage: $0 INSTALL_DIR"
    exit 1
fi

INSTALL_DIR=$1
mkdir -p $INSTALL_DIR

# Download source code
wget -O $INSTALL_DIR/rc2.zip https://github.com/BVLC/caffe/archive/rc2.zip && unzip $INSTALL_DIR/rc2 && mv $INSTALL_DIR/caffe-rc2 $INSTALL_DIR/caffe && rm $INSTALL_DIR/rc2.zip

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
cp $INSTALL_DIR/caffe/build/bvlc_reference_caffenet.caffemodel $INSTALL_DIR/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel

export C_FORCE_ROOT=TRUE
# CMD ["celery","-A","celeryTasks","worker","--loglevel=debug", "--logfile=/CloudCV_Server/celery.log"]
