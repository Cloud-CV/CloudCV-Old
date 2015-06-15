# config file for Celery Daemon

# default RabbitMQ broker
BROKER_URL = 'redis://0.0.0.0:6379/0'

# default RabbitMQ backend
CELERY_RESULT_BACKEND = 'redis://0.0.0.0:6379/0'