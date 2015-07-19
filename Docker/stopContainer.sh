docker kill cloudcv_desh_nginx
docker kill cloudcv_desh_redis
docker kill cloudcv_desh_node
docker kill cloudcv_desh_worker_cpu
docker kill cloudcv_desh_django
docker kill cloudcv_desh_rabbitmq
docker rm $(docker ps -a -q)
