__author__ = 'parallels'
import sys
path = '/home/ubuntu/cloudcv/cloudcv17'
sys.path.append(path)

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloudcv17.settings")

from celery import Celery

import json
import operator
import traceback
import os
import os.path
import redis
from app.log import log, log_to_terminal, log_error_to_terminal, log_and_exit

from app.executable.caffe_classify import caffe_classify, caffe_classify_image
import app.conf as conf

celery = Celery('ClassifyTask', backend = 'redis://0.0.0.0:6379/0', broker='redis://0.0.0.0:6379/0')

r = redis.StrictRedis(host='cloudcv.org', port=6379, db=0)

@celery.task
def classifyImages(src_path, socketid, result_path):
    try:
        #Entire Directory
        if os.path.isdir(src_path):
            for file_name in os.listdir(src_path):
                image_path = os.path.join(src_path, file_name)
                if os.path.isfile(image_path):
                    """ Trying to get the output of classify python script to send to user - Part 1/4
                    myPrint = CustomPrint(socketid)
                    old_stdout=sys.stdout
                    sys.stdout = myPrint
                    """
                    print 'Running caffe classify...'
                    tags = caffe_classify_image(image_path)

                    """ Part 2/2
                    sys.stdout=old_stdout
                    """

                    log_to_terminal("Results: "+str(tags), socketid)

                    # tags = sorted(tags.iteritems(), key=operator.itemgetter(1),reverse=True)
                    webResult = {}
                    webResult[str(os.path.join(result_path, file_name))] = tags

                    r.publish('chat',
                                   json.dumps({'web_result': json.dumps(webResult), 'socketid': str(socketid)}))

            log_to_terminal('Thank you for using CloudCV', socketid)
        # Single File
        else:
            """ Part 3/4
            myPrint = CustomPrint(socketid)
            old_stdout=sys.stdout
            sys.stdout = myPrint
            """

            print 'Running caffe classify...'

            tags = caffe_classify_image(src_path)
            """ Part 4/4
            sys.stdout=old_stdout
            """

            log_to_terminal("Results: "+str(tags), socketid)

            # tags = sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)
            web_result = {}
            web_result[str(result_path)] = tags

            r.publish('chat', json.dumps({'web_result': json.dumps(web_result), 'socketid': str(socketid)}))

            log_to_terminal('Thank you for using CloudCV', socketid)

    except Exception as e:
        log_to_terminal(str(traceback.format_exc()), socketid)


