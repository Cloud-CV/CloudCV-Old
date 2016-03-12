#!/bin/bash
# Script called by Travis to build and test Caffe.
# Travis CI tests are CPU-only for lack of compatible hardware.

set -e
# change permissions for installed python packages
sudo chown $USER -R ~/miniconda
sudo chown $USER -R ~/.cache

cd $(pwd)/deps/caffe
make --jobs=$NUM_THREADS all
make --jobs=$NUM_THREADS pycaffe
