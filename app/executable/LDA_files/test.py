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

matWNID = sio.loadmat(os.path.join(conf.EXEC_DIR, 'WNID.mat'))
WNID_cells = matWNID['wordsortWNID']
caffe.set_phase_test()
caffe.set_mode_gpu()



# Set the right path to your model file, pretrained model,
# and the image you would like to classify.

def caffe_classify_image(net, single_image, new_labels_cells):

    input_image = caffe.io.load_image(single_image)
    prediction = net.predict([input_image])
    map = {}
    for i, j in enumerate(prediction[0]):
        map[i] = j

    predsorted = sorted(map.iteritems(), key=operator.itemgetter(1), reverse=True)
    top5 = predsorted[0:5]
    topresults = []

    for i in top5:
        if (i[0] >= 1000):
            topresults.append([str(new_labels_cells[0,i[0]-1000][0]),str(i[1])])
 	else:
	    topresults.append([str(WNID_cells[i,0][0][0]),str(i[1])])

    return topresults


def caffe_classify(jobPath):

    ImagePath = os.path.join(jobPath,'test')
    modelPath = os.path.join(jobPath,'util')

    new_labels = sio.loadmat(os.path.join(modelPath,'new_labels.mat'))
    new_labels_cells = new_labels['WNID']

    # Set the right path to your model file, pretrained model,
    # and the image you would like to classify.
    MODEL_FILE = os.path.join(modelPath,'newCaffeModel.prototxt')
    PRETRAINED = os.path.join(modelPath,'newCaffeModel.caffemodel')


    net = caffe.Classifier(MODEL_FILE, PRETRAINED,
                    mean=np.load(os.path.join(conf.CAFFE_DIR, 'python/caffe/imagenet/ilsvrc_2012_mean.npy')),
                    channel_swap=(2, 1, 0),
                    raw_scale=255,
                    image_dims=(256, 256))

    results = {}

    for file_name in os.listdir(ImagePath):
        if os.path.isfile(os.path.join(ImagePath, file_name)):
            input_image_path = os.path.join(ImagePath, file_name)
            topresults = caffe_classify_image(net,input_image_path,new_labels_cells)
            results[file_name] = topresults

    return results


if __name__ == "__main__":
    results = caffe_classify(sys.argv[1])
    print str(results)
