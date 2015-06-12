__author__ = 'parallels'
import sys
path = '/home/ubuntu/cloudcv/cloudcv_gsoc'
sys.path.append(path)

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloudcv17.settings")


import json
import operator
import traceback
import os
import os.path
import redis
from app.log import log, log_to_terminal, log_error_to_terminal, log_and_exit

import app.executable.caffe_classify as default_classify

from app.celery.celery.celery import celery

r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

@celery.task
def classifyImages(src_path, socketid, result_path):
    try:
        #Entire Directory
        if os.path.isdir(src_path):
            for file_name in os.listdir(src_path):
                image_path = os.path.join(src_path, file_name)
                if os.path.isfile(image_path):

                    print 'Running caffe classify...'
                    tags = default_classify.caffe_classify_image(image_path)

                    log_to_terminal("Results: "+str(tags), socketid)

                    # tags = sorted(tags.iteritems(), key=operator.itemgetter(1),reverse=True)
                    webResult = {}
                    webResult[str(os.path.join(result_path, file_name))] = tags

                    r.publish('chat',
                                   json.dumps({'web_result': json.dumps(webResult), 'socketid': str(socketid)}))

            log_to_terminal('Thank you for using CloudCV', socketid)
        # Single File
        else:

            print 'Running caffe classify...'

            tags = default_classify.caffe_classify_image(src_path)

            log_to_terminal("Results: "+str(tags), socketid)

            # tags = sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)
            web_result = {}
            web_result[str(result_path)] = tags

            r.publish('chat', json.dumps({'web_result': json.dumps(web_result), 'socketid': str(socketid)}))

            log_to_terminal('Thank you for using CloudCV', socketid)

    except Exception as e:
        log_to_terminal(str(traceback.format_exc()), socketid)


