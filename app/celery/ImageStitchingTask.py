__author__ = 'parallels'
import sys
path = '/home/ubuntu/cloudcv/cloudcv17'
sys.path.append(path)

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloudcv17.settings")

from celery import Celery
import subprocess
import json
import sqlite3
import re
import traceback
import os
import os.path
import redis
from app.log import log, log_to_terminal, log_error_to_terminal, log_and_exit
from app.executable import caffe_classify, decaf_cal_feature
from app.thirdparty import dropbox_upload as dbu
import app.conf as conf
import time
import envoy

celery = Celery('ImageStitchingTask', backend = 'redis://0.0.0.0:6379/0', broker='redis://0.0.0.0:6379/0')

r = redis.StrictRedis(host='cloudcv.org', port=6379, db=0)

@celery.task
def runImageStitching(list, result_path, socketid):
    try:
        popen = subprocess.Popen(list,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        count=1
        print 'Coming Here'
        while True:
            popen.poll()
            if(popen.stdout):
                line=popen.stdout.readline()
                popen.stdout.flush()

            if(popen.stderr):
                errline = popen.stderr.readline()
                popen.stderr.flush()
            # r = redis.StrictRedis(host = '127.0.0.1' , port=6379, db=0)

            if line:
                # r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
                log_to_terminal(line, str(socketid))
                # fi.write(line+'*!*'+socketid+'\n')
                print count,line, '\n'

                count += 1
                        # time.sleep(1)
            if errline:
                # r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
                log_to_terminal(errline, str(socketid))
                # fi.write(line+'*!*'+socketid+'\n')
                print count,line, '\n'
                count += 1

            if line == '':
                break

        log_to_terminal('Thank you for using CloudCV', str(socketid))
        r.publish('chat', json.dumps({'web_result': result_path, 'socketid': str(socketid)}))
    except Exception as e:
        log_to_terminal(str(traceback.format_exc()), str(socketid))
        print str(traceback.format_exc())

    return '\n', '\n'
