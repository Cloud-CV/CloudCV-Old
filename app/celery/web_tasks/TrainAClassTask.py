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
import scipy.io as sio
import caffe
import numpy as np

from app.conf import CAFFE_DIR

from app.executable.LDA_files.test import caffe_classify, caffe_classify_image
from app.executable.LDA_files import train_fast
from app.log import log, log_to_terminal, log_error_to_terminal, log_and_exit
# from app.celery.celery.celery import celery

r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

@celery.task
def classifyImagesWithNewModel(jobPath, socketid, result_path):
    print jobPath, socketid, result_path
    try:
        ImagePath = os.path.join(jobPath,'test')
        modelPath = os.path.join(jobPath,'util')

        new_labels = sio.loadmat(os.path.join(modelPath,'new_labels.mat'))
        new_labels_cells = new_labels['WNID']

        # Set the right path to your model file, pretrained model,
        # and the image you would like to classify.
        MODEL_FILE = os.path.join(modelPath,'newCaffeModel.prototxt')
        PRETRAINED = os.path.join(modelPath,'newCaffeModel.caffemodel')

        caffe.set_phase_test()
        caffe.set_mode_gpu()

        net = caffe.Classifier(MODEL_FILE, PRETRAINED,
                        mean=np.load(os.path.join(CAFFE_DIR, 'python/caffe/imagenet/ilsvrc_2012_mean.npy')),
                        channel_swap=(2, 1, 0),
                        raw_scale=255,
                        image_dims=(256, 256))

        results = {}

        if os.path.isdir(ImagePath):
            for file_name in os.listdir(ImagePath):
                image_path = os.path.join(ImagePath, file_name)
                if os.path.isfile(image_path):

                    tags = caffe_classify_image(net, image_path, new_labels_cells)
                    log_to_terminal("Results: "+str(tags), socketid)
                    webResult = {}
                    webResult[os.path.join(result_path,file_name)] = tags

                    r.publish('chat',
                                   json.dumps({'web_result': json.dumps(webResult), 'socketid': str(socketid)}))

            log_to_terminal('Thank you for using CloudCV', socketid)

    except Exception as e:
        log_to_terminal(str(traceback.format_exc()), socketid)

@celery.task
def trainModel(save_dir, socketid):
    train_fast.modelUpdate(save_dir+'/')

