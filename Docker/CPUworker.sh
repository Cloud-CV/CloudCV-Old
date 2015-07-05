#!/bin/bash

# Worker setup script for CPU
# Author: Prashant Jalan

echo "Pulling the image and starting worker server for CPU"
wget -P ./Celery/ http://dl.caffe.berkeleyvision.org/bvlc_reference_caffenet.caffemodel
sudo docker build -t cloudcv/CPUworker ./CPUWorker/
sudo docker run -d --volumes-from cloudcv_code --link cloudcv_redis:redis --link rabbitmq:rabbitmq --name cloudcv_CPUworker cloudcv/CPUworker
rm ./Celery/bvlc_reference_caffenet.caffemodel
