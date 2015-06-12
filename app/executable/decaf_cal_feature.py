
"""
    Hard Coded Path: I think it does not matter when run through django
     environment because this path is already added by the Django python environment.
"""
import sys
path = '/home/ubuntu/cloudcv/cloudcv_gsoc'
sys.path.append(path)

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloudcv17.settings")
import app.conf as conf
import scipy.io as sio
import caffe

import redis
import json
import traceback
import sys
import os
import operator
import numpy as np


os.environ['OMP_NUM_THREADS'] = '4'

r = redis.StrictRedis(host = '127.0.0.1', port=6379, db=0)

print "Started test script"
# Set the right path to your model file, pretrained model,
# and the image you would like to classify.
MODEL_FILE = os.path.join(conf.CAFFE_DIR, 'models/bvlc_reference_caffenet/deploy.prototxt')
PRETRAINED = os.path.join(conf.CAFFE_DIR, 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel')
caffe.set_phase_test()
caffe.set_mode_cpu()
net = caffe.Classifier(MODEL_FILE, PRETRAINED)


def decaf_features(single_image, modelnet=net):
    print str(modelnet)
    try:
        # Compute the features
        input_image = caffe.io.load_image(single_image)
        modelnet.predict([input_image])
        blobs = modelnet.blobs.items()
        features = blobs[-3][1].data[:,:,0,0]
        print features.shape, features[1].shape
        return features
    except Exception as e:
        raise e

def decaf_features_centre(single_image, modelnet=net):

    input_image = caffe.io.load_image(single_image)
    modelnet.predict([input_image])
    blobs = modelnet.blobs.items()
    features = blobs[-3][1].data[4,:,0,0]
    features = np.resize(features, (1,4096))
    return features

def calculate_decaf_image(file, imagepath, resultpath, flag, socketid, all_results, modelname = '', modelnet=net):
    if modelnet is None:
	modelnet=net

    r.publish('chat', json.dumps({'error': str('Using '+modelname+' model for calculating features'), 'socketid': socketid}))
    try:
        if os.path.exists(resultpath + '/' + file + '.mat'):
            matfile = sio.loadmat(resultpath + '/' + file + '.mat')
        else:
            matfile = {}

        image = os.path.join(imagepath, file)
        r.publish('chat', json.dumps({'error': str(image), 'socketid': socketid}))
        if int(flag) & 1 == 1:
            results = decaf_features(image, modelnet)
            matfile['decaf'] = results
            all_results[str(file)] = {'decaf': results}
            r.publish('chat', json.dumps({'error': str('Decaf Feature Calculated'), 'socketid': socketid}))

        if int(flag) & 2 == 2:
            results = decaf_features_centre(image, modelnet)
            matfile['decaf_center'] = results
            if str(file) in all_results:
                all_results[str(file)]['decaf_centre'] = results
            else:
                all_results[str(file)] = {'decaf_centre':results}
            r.publish('chat', json.dumps({'error': str('Decaf-Centre Feature Calculated'), 'socketid': socketid}))

        sio.savemat(os.path.join(resultpath, file + '.mat'), matfile)
        r.publish('chat', json.dumps({'error': str(file), 'socketid': socketid}))

    except Exception as e:
        r.publish('chat', json.dumps({'error': str(e), 'socketid': socketid}))
        r.publish('chat', json.dumps({'error': str(traceback.format_exc()), 'socketid': socketid}))

    return str(os.path.join(resultpath, file + '.mat'))

def calculate_decaf(imagepath, resultpath, flag, socketid, all_results):
    mat_files_paths = {}
    for file in os.listdir(imagepath):
        if os.path.isfile(os.path.join(imagepath, file)):
            mat_file_path = calculate_decaf_image(file, imagepath, resultpath, flag, socketid, all_results)
            mat_files_paths[file] = mat_file_path
    return mat_files_paths


if __name__ == '__main__':
    print sys.argv[1]
    calculate_decaf(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

