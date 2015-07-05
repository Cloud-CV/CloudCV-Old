docker stop cloudcv_nginx
docker stop cloudcv_redis
docker stop cloudcv_node
docker stop cloudcv_worker_cpu
docker stop cloudcv_django
docker stop cloudcv_rabbitmq
docker rm $(docker ps -a -q)
