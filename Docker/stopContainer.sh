docker kill cloudcv_sd_nginx
docker kill cloudcv_sd_redis
docker kill cloudcv_sd_node
docker kill cloudcv_sd_worker_cpu
docker kill cloudcv_sd_django
docker kill cloudcv_sd_rabbitmq
docker rm $(docker ps -a -q)
