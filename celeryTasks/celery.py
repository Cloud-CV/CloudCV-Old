from __future__ import absolute_import
from celery import Celery

app = Celery('cloudcv',
             broker='amqp://guest:guest@rabbitmq:5672//',
             backend='redis://redis:6379',
             include=[
             'celeryTasks.webTasks.classifyTask',
             'celeryTasks.webTasks.decafTask',
             'celeryTasks.webTasks.poiTask'
             ])

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_ENABLE_UTC=True,
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    app.start()

