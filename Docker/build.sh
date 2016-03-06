#!/bin/bash

# Server setup script
# Author: Harsh Agrawal

echo "Creating base image"
cp ../requirements.txt ./Base/
sudo docker build -t cloudcv/base ./Base/
rm ./Base/requirements.txt

echo "Creating data container"
sudo docker build --no-cache -t cloudcv/code ./Code/
sudo docker create -v /CloudCV_Server --name cloudcv_code cloudcv/code /bin/true

echo "Pulling the image and starting redis server."
sudo docker pull redis:3.0

echo "Pulling the image and starting rabbitmq server."
sudo docker pull rabbitmq

echo "Pulling the image and starting the node.js server"
cp ../nodejs/chat.js ./Node/
sudo docker build -t cloudcv/node ./Node/
rm ./Node/chat.js

echo "Pulling the image and starting django server"
sudo docker build -t cloudcv/django ./Django/

echo "Pulling the image and starting nginx server"
cp ../fileupload_nginx.conf ./Nginx/default.conf
sudo docker build -t cloudcv/nginx ./Nginx/
rm Nginx/default.conf
