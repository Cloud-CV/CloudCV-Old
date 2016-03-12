set -e
set -x

if [ "$#" -ne 1 ];
then
    echo "Usage: $0 INSTALL_DIR"
    exit 1
fi

INSTALL_DIR=$1
mkdir -p $INSTALL_DIR

# Install dependencies
sudo apt-get install -y gfortran git wget unzip build-essential

# Download source code
wget -O $INSTALL_DIR/OpenCV-2.4.11.zip http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.11/opencv-2.4.11.zip/download && unzip $INSTALL_DIR/OpenCV-2.4.11.zip && mv $INSTALL_DIR/opencv-2.4.11 $INSTALL_DIR && rm $INSTALL_DIR/OpenCV-2.4.11.zip
# OpenCV Installation
# OpenCV dependencies
sudo apt-get install -y cmake libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
sudo apt-get install -y python-numpy libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libjasper-dev libdc1394-22-dev


cd $INSTALL_DIR && \
    mkdir release && \
    cd release && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local .. && \
    make -j 4 && \
    make install
