# config file for Celery Daemon

# default RabbitMQ broker
BROKER_URL = 'redis://redis:6379/0'

# default RabbitMQ backend
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'