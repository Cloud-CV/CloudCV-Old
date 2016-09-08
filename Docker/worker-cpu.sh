#!/bin/bash

# Worker setup script for CPU
# Author: Deshraj

echo "Pulling the image and starting worker server for CPU"
wget -nc -P ./CPUWorker http://dl.caffe.berkeleyvision.org/bvlc_reference_caffenet.caffemodel
sudo docker build -t cloudcv/cpu-worker ./CPUWorker/
sudo docker run -d -p 5555:5555 --volumes-from cloudcv_code --link cloudcv_rabbitmq:rabbitmq --link cloudcv_redis:redis --link cloudcv_django:django --name cloudcv_worker_cpu cloudcv/cpu-worker
# rm ./CPUWorker/bvlc_reference_caffenet.caffemodel
