#!/bin/bash

# Worker setup script for CPU
# Author: Prashant Jalan

echo "Pulling the image and starting worker server for CPU"
#wget -P ./CPUWorker http://dl.caffe.berkeleyvision.org/bvlc_reference_caffenet.caffemodel
#sudo docker build -t cloudcv/cpu-worker ./CPUWorker/
sudo docker run -d --volumes-from cloudcv_sd_code1 --link cloudcv_sd_rabbitmq1:rabbitmq --link cloudcv_sd_redis1:redis --name cloudcv_sd_worker_cpu1 cloudcv/cpu-worker
#rm ./CPUWorker/bvlc_reference_caffenet.caffemodel
