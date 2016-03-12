#!/bin/bash
# Script called by Travis to build and test Caffe.
# Travis CI tests are CPU-only for lack of compatible hardware.

set -e

make --jobs=$NUM_THREADS all
make --jobs=$NUM_THREADS pycaffe
