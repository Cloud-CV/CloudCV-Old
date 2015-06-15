import operator
import numpy as np

import sys
path = '/home/ubuntu/cloudcv/cloudcv17'
sys.path.append(path)

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloudcv17.settings")

import app.conf as conf


import scipy.io as sio
import caffe

# r = redis.StrictRedis(host = '127.0.0.1', port=6379, db=0)

# Set the right path to your model file, pretrained model,
# and the image you would like to classify.
MODEL_FILE = os.path.join(conf.CAFFE_DIR, 'models/bvlc_reference_caffenet/deploy.prototxt')
PRETRAINED = os.path.join(conf.CAFFE_DIR, 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel')

caffe.set_phase_test()
caffe.set_mode_gpu()

net = caffe.Classifier(MODEL_FILE, PRETRAINED,
                    mean=np.load(os.path.join(conf.CAFFE_DIR, 'python/caffe/imagenet/ilsvrc_2012_mean.npy')),
                    channel_swap=(2, 1, 0),
                    raw_scale=255,
                    image_dims=(256, 256))

def caffe_feat_image(single_image, feat_path):
    input_image = caffe.io.load_image(single_image)
    prediction = net.predict([input_image])
    # Save prediction[0] to to file
    np.save(feat_path, prediction[0])
    return