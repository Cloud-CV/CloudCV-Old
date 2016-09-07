#!/bin/bash

# Server setup script
# Author: Deshraj, Harsh Agrawal


echo "Running the image and starting redis server."
if [ "$1" == "run" ] 
then
    sudo docker create -v $PWD/..:/CloudCV_Server --name cloudcv_code cloudcv/code /bin/true

    sudo docker $1 -d --name cloudcv_redis redis

    echo "Running the image and starting rabbitmq server."
    sudo docker $1 -d --name cloudcv_rabbitmq rabbitmq

    echo "Running the image and starting the node.js server"
    sudo docker $1 -d --volumes-from cloudcv_code --link cloudcv_redis:redis --name cloudcv_node cloudcv/node

    echo "Running the image and starting django server"
    sudo docker $1 -d --volumes-from cloudcv_code --link cloudcv_rabbitmq:rabbitmq --link cloudcv_redis:redis --name cloudcv_django cloudcv/django uwsgi --emperor /CloudCV_Server/

    echo "Running the image and starting nginx server"
    sudo docker $1 -d -p $2:80 -p $3:443 --volumes-from cloudcv_code --name cloudcv_nginx --link cloudcv_node:node --link cloudcv_redis:redis --link cloudcv_django:django cloudcv/nginx
else
    sudo docker restart cloudcv_redis

    echo "Running the image and starting rabbitmq server."
    sudo docker restart cloudcv_rabbitmq

    echo "Running the image and starting the node.js server"
    sudo docker restart cloudcv_node

    echo "Running the image and starting django server"
    sudo docker restart cloudcv_django  
    echo "Running the image and starting nginx server"
    sudo docker restart cloudcv_nginx 
fi
