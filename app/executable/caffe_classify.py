import operator
import numpy as np

import sys
path = '/home/ubuntu/cloudcv/cloudcv_gsoc'
sys.path.append(path)

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloudcv17.settings")

import app.conf as conf


import scipy.io as sio
import caffe

matWNID = sio.loadmat(os.path.join(conf.EXEC_DIR, 'WNID.mat'))
WNID_cells = matWNID['wordsortWNID']

# Set the right path to your model file, pretrained model,
# and the image you would like to classify.
MODEL_FILE = os.path.join(conf.CAFFE_DIR, 'models/bvlc_reference_caffenet/deploy.prototxt')
PRETRAINED = os.path.join(conf.CAFFE_DIR, 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel')

caffe.set_phase_test()
caffe.set_mode_cpu()

net = caffe.Classifier(MODEL_FILE, PRETRAINED,
                    mean=np.load(os.path.join(conf.CAFFE_DIR, 'python/caffe/imagenet/ilsvrc_2012_mean.npy')),
                    channel_swap=(2, 1, 0),
                    raw_scale=255,
                    image_dims=(256, 256))

def caffe_classify_image(single_image):
    input_image = caffe.io.load_image(single_image)
    prediction = net.predict([input_image])
    map = {}
    for i, j in enumerate(prediction[0]):
        map[i] = j

    predsorted = sorted(map.iteritems(), key=operator.itemgetter(1), reverse=True)
    top5 = predsorted[0:5]
    topresults = [] 

    for i in top5:
        #topresults[str(WNID_cells[i, 0][0][0])] = str(i[1])
        topresults.append([str(WNID_cells[i, 0][0][0]),str(i[1])])
    return topresults


def caffe_classify(ImagePath):

    results = {}

    for file_name in os.listdir(ImagePath):
        if os.path.isfile(os.path.join(ImagePath, file_name)):
            input_image_path = os.path.join(ImagePath, file_name)
            topresults = caffe_classify_image(input_image_path)
            results[file_name] = topresults

    return results


if __name__ == "__main__":
    results = caffe_classify(sys.argv[1])
    print str(results)
