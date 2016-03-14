#!/bin/bash

set -e

INSTALL_DIR=$(pwd)/deps/caffe

if [ ! -d "$(pwd)/deps/caffe" ]; then
  mkdir -p $INSTALL_DIR

  NUM_THREADS=${NUM_THREADS-4}

  CAFFE_BRANCH="master"
  CAFFE_URL="https://github.com/BVLC/caffe.git"

  # Get source
  git clone --depth 1 --branch $CAFFE_BRANCH $CAFFE_URL $INSTALL_DIR
  cd $INSTALL_DIR

  mv Makefile.config.example Makefile.config

  if $WITH_CUDA; then
    # Only generate compute_50.
    GENCODE="-gencode arch=compute_50,code=sm_50"
    GENCODE="$GENCODE -gencode arch=compute_50,code=compute_50"
    echo "CUDA_ARCH := $GENCODE" >> Makefile.config
  fi

  # Remove IO library settings from Makefile.config
  # to avoid conflicts with CI configuration
  sed -i -e '/USE_LMDB/d' Makefile.config
  sed -i -e '/USE_LEVELDB/d' Makefile.config
  sed -i -e '/USE_OPENCV/d' Makefile.config

  cat << 'EOF' >> Makefile.config
  # Travis' nvcc doesn't like newer boost versions
  NVCCFLAGS := -Xcudafe --diag_suppress=cc_clobber_ignored -Xcudafe --diag_suppress=useless_using_declaration -Xcudafe --diag_suppress=set_but_not_used
  ANACONDA_HOME := $(CONDA_DIR)
  PYTHON_INCLUDE := $(ANACONDA_HOME)/include \
      $(ANACONDA_HOME)/include/python2.7 \
      $(ANACONDA_HOME)/lib/python2.7/site-packages/numpy/core/include
  PYTHON_LIB := $(ANACONDA_HOME)/lib
  INCLUDE_DIRS := $(PYTHON_INCLUDE) /usr/local/include
  LIBRARY_DIRS := $(PYTHON_LIB) /usr/local/lib /usr/lib
  WITH_PYTHON_LAYER := 1
  EOF

  # Travis Caffe Build Instructions
  cd $INSTALL_DIR

  MAKE="make --jobs=$NUM_THREADS --keep-going"

  if $WITH_CMAKE; then
    mkdir build
    cd build
    CPU_ONLY=" -DCPU_ONLY=ON"
    if ! $WITH_CUDA; then
      CPU_ONLY=" -DCPU_ONLY=OFF"
    fi
    PYTHON_ARGS=""
    if [ "$PYTHON_VERSION" = "3" ]; then
      PYTHON_ARGS="$PYTHON_ARGS -Dpython_version=3 -DBOOST_LIBRARYDIR=$CONDA_DIR/lib/"
    fi
    if $WITH_IO; then
      IO_ARGS="-DUSE_OPENCV=ON -DUSE_LMDB=ON -DUSE_LEVELDB=ON"
    else
      IO_ARGS="-DUSE_OPENCV=OFF -DUSE_LMDB=OFF -DUSE_LEVELDB=OFF"
    fi
    cmake -DBUILD_python=ON -DCMAKE_BUILD_TYPE=Release $CPU_ONLY $PYTHON_ARGS -DCMAKE_INCLUDE_PATH="$CONDA_DIR/include/" -DCMAKE_LIBRARY_PATH="$CONDA_DIR/lib/" $IO_ARGS ..
    $MAKE
  else
    if ! $WITH_CUDA; then
      export CPU_ONLY=1
    fi
    if $WITH_IO; then
      export USE_LMDB=1
      export USE_LEVELDB=1
      export USE_OPENCV=1
    fi
    $MAKE all
    $MAKE pycaffe
  fi

else
  echo 'Using cached directory for Caffe Installation.';
fi
