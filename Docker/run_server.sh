#!/bin/bash

# Server setup script
# Author: Prashant Jalan, Harsh Agrawal


echo "Running the image and starting redis server."
sudo docker run -d --name cloudcv_redis redis

echo "Running the image and starting rabbitmq server."
sudo docker run -d --name cloudcv_rabbitmq rabbitmq

echo "Running the image and starting the node.js server"
sudo docker run -d --link cloudcv_redis:redis --name cloudcv_node cloudcv/node

echo "Running the image and starting django server"
sudo docker run -d --volumes-from cloudcv_code --link cloudcv_rabbitmq:rabbitmq --link cloudcv_redis:redis --name cloudcv_django cloudcv/django uwsgi --emperor /CloudCV_Server/

echo "Running the image and starting nginx server"
sudo docker run -d -p $1:80 -p $2:443 --volumes-from cloudcv_code --name cloudcv_nginx --link cloudcv_node:node --link cloudcv_redis:redis --link cloudcv_django:django cloudcv/nginx
