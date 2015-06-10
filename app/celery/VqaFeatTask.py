__author__ = 'clint'
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

from app.executable.vqa_feat_extract import caffe_feat_image
import app.conf as conf

celery = Celery('VqaFeatTask', backend = 'redis://0.0.0.0:6379/0', broker='redis://0.0.0.0:6379/0')

r = redis.StrictRedis(host='cloudcv.org', port=6379, db=0)

@celery.task
def featExtraction(src_path, socketid, result_url_prefix,  feat_folder):
    try:
        #Entire Directory
        if os.path.isdir(src_path):
            for file_name in os.listdir(src_path):
                image_path = os.path.join(src_path, file_name)
                feat_path = os.path.join(feat_folder, file_name)
                if os.path.isfile(image_path):
                    """ Trying to get the output of classify python script to send to user - Part 1/4
                    myPrint = CustomPrint(socketid)
                    old_stdout=sys.stdout
                    sys.stdout = myPrint
                    """
                    if os.path.isfile(feat_path + '.npy'):
                        # Features already extracted for this file - it can actually be a different image but fix later
                        continue

                    print 'Extracting caffe features...'
                    caffe_feat_image(image_path, feat_path)

                    """ Part 2/2
                    sys.stdout=old_stdout
                    """

                    log_to_terminal("Feature extraction done. ", socketid)

                    # tags = sorted(tags.iteritems(), key=operator.itemgetter(1),reverse=True)
                    webResult = {}
                    # webResult[str(os.path.join(result_url_prefix, file_name))] = [['Feature Extraction', 'Done']]
                    webResult["extracted"] = str(os.path.join(result_url_prefix, file_name))

                    r.publish('chat',
                                   json.dumps({'web_result': json.dumps(webResult), 'socketid': str(socketid)}))

        # Single File
        else:
            """ Part 3/4
            myPrint = CustomPrint(socketid)
            old_stdout=sys.stdout
            sys.stdout = myPrint
            """

            print 'Extracting caffe features...'
            # This is handled in vqa_views
            feat_path = feat_folder
            caffe_feat_image(src_path, feat_path)
            """ Part 4/4
            sys.stdout=old_stdout
            """

            log_to_terminal("Feature extraction done. ", socketid)

            # tags = sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)
            web_result = {}
            # web_result[str(result_url_prefix)] = [['Feature Extraction', 'Done']]
            web_result["extracted"] = str(result_url_prefix)

            r.publish('chat', json.dumps({'web_result': json.dumps(web_result), 'socketid': str(socketid)}))

    except Exception as e:
        log_to_terminal(str(traceback.format_exc()), socketid)


