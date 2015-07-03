#!/bin/bash

# Server setup script
# Author: Prashant Jalan

echo "Creating base image"
cp ../requirements.txt ./Base/
sudo docker build -t cloudcv/base ./Base/
rm ./Base/requirements.txt

echo "Creating data container"
sudo docker build --no-cache -t cloudcv/code ./Code/
sudo docker create -v /CloudCV_Server --name cloudcv_code cloudcv/code /bin/true

echo "Pulling the image and starting redis server."
sudo docker pull redis:3.0
sudo docker run -d --name cloudcv_redis redis

echo "Pulling the image and starting the node.js server"
cp ../nodejs/chat.js ./Node/
sudo docker build -t cloudcv/node ./Node/
sudo docker run -d --link cloudcv_redis:redis --name cloudcv_node cloudcv/node
rm ./Node/chat.js

echo "Pulling the image and starting django server"
wget -P ./Django/ http://dl.caffe.berkeleyvision.org/bvlc_reference_caffenet.caffemodel
sudo docker build -t cloudcv/django ./Django/
sudo docker run -d --volumes-from cloudcv_code --link cloudcv_redis:redis --name cloudcv_django cloudcv/django 
rm ./Django/bvlc_reference_caffenet.caffemodel

echo "Pulling the image and starting nginx server"
cp ../fileupload_nginx.conf ./Nginx/default.conf
sudo docker build -t cloudcv/nginx ./Nginx/
sudo docker run -d -p 80:80 -p 443:443 --volumes-from cloudcv_code --name cloudcv_nginx --link cloudcv_node:node --link cloudcv_redis:redis --link cloudcv_django:django cloudcv/nginx
rm Nginx/default.conf
