from __future__ import absolute_import

from celery import Celery

# instantiate Celery object
celery = Celery(include=[
                         'app.celery.api_tasks.tasks'
                        ])

# import celery config file
celery.config_from_object('app.celery.celeryconfig')

if __name__ == '__main__':
    celery.start()