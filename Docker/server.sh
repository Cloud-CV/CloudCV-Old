#!/bin/bash

# Server setup script
# Author: Prashant Jalan

echo "Creating base image"
#cp ../requirements.txt ./Base/
#sudo docker build -t cloudcv/base ./Base/
#rm ./Base/requirements.txt

echo "Creating data container"
#sudo docker build --no-cache -t cloudcv/shubham_code ./Code/
#sudo docker create -v /CloudCV_Server --name cloudcv_sd_code cloudcv/shubham_code /bin/true
sudo docker run -d -P --name cloudcv_sd_code -v /home/ubuntu/cloudcv/CloudCV_Shubham/CloudCV_Server:/CloudCV_Server  cloudcv/shubham_code bin/true
 

echo "Pulling the image and starting redis server."
#sudo docker pull redis:3.0
sudo docker run -d --name cloudcv_sd_redis redis

echo "Pulling the image and starting rabbitmq server."
#sudo docker pull rabbitmq
sudo docker run -d --name cloudcv_sd_rabbitmq rabbitmq

echo "Pulling the image and starting the node.js server"
#cp ../nodejs/chat.js ./Node/
#sudo docker build -t cloudcv/node ./Node/
sudo docker run -d --link cloudcv_sd_redis:redis --name cloudcv_sd_node cloudcv/node
#rm ./Node/chat.js

echo "Pulling the image and starting django server"
#sudo docker build -t cloudcv/django ./Django/
sudo docker run -d --volumes-from cloudcv_sd_code --link cloudcv_sd_rabbitmq:rabbitmq --link cloudcv_sd_redis:redis --name cloudcv_sd_django cloudcv/django uwsgi --py-autoreload 1 --emperor /CloudCV_Server/

echo "Pulling the image and starting nginx server"
#cp ../fileupload_nginx.conf ./Nginx/default.conf
#sudo docker build -t cloudcv/nginx ./Nginx/
sudo docker run -d -p 8600:80 --volumes-from cloudcv_sd_code --name cloudcv_sd_nginx --link cloudcv_sd_node:node --link cloudcv_sd_redis:redis --link cloudcv_sd_django:django cloudcv/nginx
#rm Nginx/default.conf
