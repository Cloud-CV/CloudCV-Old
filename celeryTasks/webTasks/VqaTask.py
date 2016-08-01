__author__ = 'clint'
from celeryTasks.celery import app
from app.log import log, log_to_terminal, log_error_to_terminal, log_and_exit

import json
import operator
import traceback
import os
import redis


@app.task
def answerQuestion(feat_path, question, socketid, imageid):
    try:
        from celery import Celery


        from app.executable.vqa_answer_image import vqa_answer
        import app.conf as conf
        celery = Celery('VqaFeatTask', backend = 'redis://0.0.0.0:6379/0', broker='redis://0.0.0.0:6379/0')

        r = redis.StrictRedis(host='cloudcv.org', port=6379, db=0)
        print 'Thinking...'
        # For now, using numpy archives
        feat_path = feat_path + '.npy'
        ans = vqa_answer(feat_path, question)

        log_to_terminal("Answer found: " + ans, socketid)

        # tags = sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)
        web_result = {}
        web_result[imageid] = [ans]

        r.publish('chat', json.dumps({'web_result': json.dumps(web_result), 'socketid': str(socketid)}))

        log_to_terminal('Thank you for using CloudCV', socketid)

    except Exception as e:
        log_to_terminal(str(traceback.format_exc()), socketid)


@app.task
def answerQuestion2(feat_path, question, socketid, imageid):
    try:
        import numpy as np
        print 'Thinking...'
        feat_path = feat_path + '.npy'
        feat = np.load(feat_path)
        r.publish('test_aws', json.dumps({'imgFeatures': feat.tolist(),
                              'question': question,
                              'imageid': imageid, 'socketid': socketid}))

        # ans = vqa_answer2(feat_path, question)
        # log_to_terminal("Answer for "+ imageid + " : " + str(ans), socketid)
        # web_result = {}
        # web_result[imageid] = ans
        # r.publish('chat', json.dumps({'web_result': json.dumps(web_result), 'socketid': str(socketid)}))

        # log_to_terminal('Thank you for using CloudCV', socketid)

    except Exception as e:
        log_to_terminal(str(traceback.format_exc()), socketid)
