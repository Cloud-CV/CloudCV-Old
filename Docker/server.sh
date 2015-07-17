#!/bin/bash

# Server setup script
# Author: Prashant Jalan

echo "Creating base image"
cp ../requirements.txt ./Base/
sudo docker build -t cloudcv/desh_base ./Base/
rm ./Base/requirements.txt

echo "Creating data container"
sudo docker build --no-cache -t cloudcv/desh_code ./Code/
sudo docker create -v /CloudCV_Server --name cloudcv_desh_code cloudcv/desh_code /bin/true

echo "Pulling the image and starting redis server."
sudo docker pull redis:3.0
sudo docker run -d --name cloudcv_desh_redis redis

echo "Pulling the image and starting rabbitmq server."
sudo docker pull rabbitmq
sudo docker run -d --name cloudcv_desh_rabbitmq rabbitmq

echo "Pulling the image and starting the node.js server"
cp ../nodejs/chat.js ./Node/
sudo docker build -t cloudcv/desh_node ./Node/
sudo docker run -d --link cloudcv_desh_redis:redis --name cloudcv_desh_node cloudcv/desh_node
rm ./Node/chat.js

echo "Pulling the image and starting DIGITS server"
sudo docker pull kaixhin/digits
sudo docker run -d --name cloudcv_desh_digits kaixhin/digits ./digits-devserver

echo "Pulling the image and starting django server"
sudo docker build -t cloudcv/desh_django ./Django/
sudo docker run -d --volumes-from cloudcv_desh_code --link cloudcv_desh_rabbitmq:rabbitmq --link cloudcv_desh_redis:redis --name cloudcv_desh_django cloudcv/desh_django uwsgi --emperor /CloudCV_Server/

echo "Pulling the image and starting nginx server"
cp ../fileupload_nginx.conf ./Nginx/default.conf
sudo docker build -t cloudcv/desh_nginx ./Nginx/
sudo docker run -d -p 80:80 -p 443:443 --volumes-from cloudcv_desh_code --name cloudcv_desh_nginx --link cloudcv_desh_node:node --link cloudcv_desh_redis:redis --link cloudcv_desh_digits:digits --link cloudcv_desh_django:django cloudcv/desh_nginx