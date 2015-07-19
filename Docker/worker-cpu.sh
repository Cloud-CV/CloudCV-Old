#!/bin/bash

# Worker setup script for CPU
# Author: Prashant Jalan

echo "Pulling the image and starting worker server for CPU"
wget -P ./CPUWorker http://dl.caffe.berkeleyvision.org/bvlc_reference_caffenet.caffemodel
sudo docker build -t cloudcv/cpu-desh-worker ./CPUWorker/
sudo docker run -d --volumes-from cloudcv_desh_code --link cloudcv_desh_rabbitmq:rabbitmq --link cloudcv_desh_redis:redis --name cloudcv_desh_worker_cpu cloudcv/cpu-desh-worker
rm ./CPUWorker/bvlc_reference_caffenet.caffemodel
