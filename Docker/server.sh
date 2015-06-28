#!/bin/bash

# Server setup script
# Author: Prashant Jalan

echo "Pulling the image and starting redis server."
sudo docker pull redis:3.0
sudo docker run -d --name cloudcv_redis redis

echo "Pulling the image and starting the node.js server"
cp ../nodejs/chat.js ./Node/
sudo docker build -t cloudcv/node ./Node/
sudo docker run -d --link cloudcv_redis:redis --name cloudcv_node cloudcv/node
rm ./Node/chat.js

echo "Pulling the image and starting nginx server"
cp ../fileupload_nginx.conf ./Nginx/default.conf
sudo docker build -t cloudcv/nginx ./Nginx/
sudo docker run -d -p 80:80 -p 443:443 --name cloudcv_nginx --link cloudcv_node:node --link cloudcv_redis:redis --link cloudcv_django:django cloudcv/nginx
rm Nginx/default.conf

echo "Pulling the image and starting django server"
cp ../../requirements.txt ./
wget -P ./Django/ http://dl.caffe.berkeleyvision.org/bvlc_reference_caffenet.caffemodel
sudo docker build -t cloudcv/django ./Django/
sudo docker run -it -p 80:80 --link cloudcv_redis:redis --name cloudcv_django cloudcv/django /bin/bash
rm ./Django/requirements.txt
rm ./Django/bvlc_reference_caffenet.caffemodel
