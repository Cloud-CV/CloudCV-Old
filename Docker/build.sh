#!/bin/bash

# Server setup script
# Author: Harsh Agrawal

echo "Creating base image"
cp ../requirements.txt ./Base/
docker build -t cloudcv/base ./Base/
rm ./Base/requirements.txt

echo "Creating data container"
docker build --no-cache -t cloudcv/code ./Code/

echo "Pulling the image and starting redis server."
docker pull redis:3.0

echo "Pulling the image and starting rabbitmq server."
docker pull rabbitmq

echo "Pulling the image and starting the node.js server"
cp ../nodejs/chat.js ./Node/
docker build -t cloudcv/node ./Node/
rm ./Node/chat.js

echo "Pulling the image and starting django server"
docker build -t cloudcv/django ./Django/

echo "Pulling the image and starting nginx server"
docker build -t cloudcv/nginx ./Nginx/
