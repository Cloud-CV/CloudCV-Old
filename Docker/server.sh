#!/bin/bash

# Server setup script
# Author: Prashant Jalan

echo "Creating base image"
cp ../requirements.txt ./Base/
sudo docker build -t cloudcv/desh_base1 ./Base/
rm ./Base/requirements.txt

#echo "Creating data container"
sudo docker build --no-cache -t cloudcv/desh_code1 ./Code/
sudo docker create -v /CloudCV_Server --name cloudcv_desh_code1 cloudcv/desh_code1 /bin/true

echo "Pulling the image and starting redis server."
sudo docker pull redis:3.0
sudo docker run -d --name cloudcv_desh_redis1 redis

#echo "Pulling the image and starting rabbitmq server."
sudo docker pull rabbitmq
sudo docker run -d --name cloudcv_desh_rabbitmq1 rabbitmq

echo "Pulling the image and starting the node.js server"
cp ../nodejs/chat.js ./Node/
sudo docker build -t cloudcv/desh_node1 ./Node/
sudo docker run -d --link cloudcv_desh_redis1:redis --name cloudcv_desh_node1 cloudcv/desh_node1
rm ./Node/chat.js

#echo "Pulling the image and starting DIGITS server"
# sudo docker pull kaixhin/digits
docker build -t cloudcv/desh_digits1 ./DIGITS/
sudo docker run -d --name cloudcv_desh_digits1 cloudcv/desh_digits1 ./digits-devserver

echo "Pulling the image and starting django server"
sudo docker build -t cloudcv/desh_django1 ./Django/
sudo docker run -d --volumes-from cloudcv_desh_code1 --link cloudcv_desh_rabbitmq1:rabbitmq --link cloudcv_desh_redis1:redis --name cloudcv_desh_django1 cloudcv/desh_django1 uwsgi --emperor /CloudCV_Server/

echo " the image and starting nginx server"
cp ../fileupload_nginx.conf ./Nginx/default.conf
sudo docker build -t cloudcv/desh_nginx1 ./Nginx/
sudo docker run -d -p 8500:80 --volumes-from cloudcv_desh_code1 --name cloudcv_desh_nginx1 --link cloudcv_desh_node1:node --link cloudcv_desh_redis1:redis --link cloudcv_desh_digits1:digits --link cloudcv_desh_django1:django cloudcv/desh_nginx1
