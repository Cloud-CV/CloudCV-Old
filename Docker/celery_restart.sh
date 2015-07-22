docker rm -f cloudcv_sd_worker_cpu
sudo docker run -d --volumes-from cloudcv_sd_code --link cloudcv_sd_rabbitmq:rabbitmq --link cloudcv_sd_redis:redis --name cloudcv_sd_worker_cpu cloudcv/cpu-worker


