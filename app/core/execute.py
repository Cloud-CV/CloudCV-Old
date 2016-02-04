from app.log import log_to_terminal, log_and_exit
from celeryTasks.apiTasks.tasks import run
from cloudcv17 import config
import app.conf as conf

import os
import traceback
import json
import redis

r = redis.StrictRedis(host=config.REDIS_HOST, port=6379, db=0)


def execute(job_obj, image_path=None, source_type=None):
    try:
        directory = os.path.join(job_obj.storage_path, str(job_obj.jobid))

        if not os.path.exists(directory):
            os.makedirs(directory)
            os.chmod(directory, 0776)

        result_path = directory

        # Run an executable as defined by the user
        if job_obj.url is None:
            job_obj.url = os.path.join(conf.PIC_URL, job_obj.userid, job_obj.jobid)

        log_to_terminal('Files Stored. Waiting for one of the worker nodes to handle this request', job_obj.socketid)
        parsed_dict = {'jobid': job_obj.jobid, 'userid': job_obj.userid,
                       'image_path': str(image_path), 'result_path': str(result_path),
                       'dir': str(directory), 'url': job_obj.url,
                       'source_type': source_type, 'exec': job_obj.executable,
                       'count': job_obj.count, 'token': job_obj.token,
                       'socketid': job_obj.socketid, 'params': job_obj.params,
                       'dropbox_token': job_obj.dropbox_token}

        r.publish('chat', json.dumps({'jobinfo': parsed_dict, 'socketid': str(job_obj.socketid)}))
        run.delay(parsed_dict)

    except:
        log_and_exit(str(traceback.format_exc()), job_obj.socketid)
        return str('Error pushing to the job queue')

    return str(parsed_dict)
