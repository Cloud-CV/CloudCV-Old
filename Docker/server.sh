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
