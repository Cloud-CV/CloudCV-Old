import operator
import numpy as np
import sys
import os
import app.conf as conf
import caffe
import scipy.io as sio

# r = redis.StrictRedis(host = '127.0.0.1', port=6379, db=0)


def caffe_feat_image(single_image, feat_path):
    VGG_MODEL_FILE = os.path.join(conf.CAFFE_DIR, 'models/vggnet/deploy_features.prototxt')
    VGG_PRETRAINED = os.path.join(conf.CAFFE_DIR, 'models/vggnet/VGG_ILSVRC_16_layers.caffemodel')
    vggNet = caffe.Classifier(
        VGG_MODEL_FILE, VGG_PRETRAINED, 
        mean = np.load(os.path.join(conf.CAFFE_DIR, 'python/caffe/imagenet/ilsvrc_2012_mean.npy')),
        channel_swap = (2,1,0),
        raw_scale = 255,
        image_dims=(256,256)
    )
    caffe.set_mode_gpu()

    print "Starting feature extraction"
    caffe.set_mode_gpu()
    input_image = caffe.io.load_image(single_image)
    print "Loaded image"
    prediction = vggNet.predict([input_image])
    print "Prediction complete!"
    # Save prediction[0] to to file
    np.save(feat_path, prediction[0]) # Because it is single image. In case of batch predictions, save everything.
    print "Calculating features in VGG Net."
    return
