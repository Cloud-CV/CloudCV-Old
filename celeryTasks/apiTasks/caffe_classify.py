"""
This file is copied from app.executable master branch
It is required by the tasks.py file.

While editing please make sure:
1) Not to import unnecessary modules.
2) Import only within the function where it is necessary.
3) Any new import will require you to install it in the worker container.
   (See Docker/CPUWorker/Dockerfile)
"""


def caffe_classify_image(single_image):
    import operator
    import numpy as np

    import scipy.io as sio
    import caffe
    import os

    matWNID = sio.loadmat(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'WNID.mat'))
    WNID_cells = matWNID['wordsortWNID']

    CAFFE_DIR = os.path.normpath(os.path.join(
        os.path.dirname(caffe.__file__), "..", ".."))

    # Set the right path to your model file, pretrained model,
    # and the image you would like to classify.
    MODEL_FILE = os.path.join(
        CAFFE_DIR, 'models/bvlc_reference_caffenet/deploy.prototxt')
    PRETRAINED = os.path.join(
        CAFFE_DIR, 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel')

    # caffe.set_phase_test()
    caffe.set_mode_cpu()

    net = caffe.Classifier(MODEL_FILE, PRETRAINED,
                           mean=np.load(os.path.join(
                               CAFFE_DIR, 'python/caffe/imagenet/ilsvrc_2012_mean.npy')).mean(1).mean(1),
                           channel_swap=(2, 1, 0),
                           raw_scale=255,
                           image_dims=(256, 256))

    input_image = caffe.io.load_image(single_image)
    prediction = net.predict([input_image])
    map = {}
    for i, j in enumerate(prediction[0]):
        map[i] = j

    predsorted = sorted(
        map.iteritems(), key=operator.itemgetter(1), reverse=True)
    top5 = predsorted[0:5]
    topresults = []

    for i in top5:
        # topresults[str(WNID_cells[i, 0][0][0])] = str(i[1])
        topresults.append([str(WNID_cells[i, 0][0][0]), str(i[1])])
    return topresults


def caffe_classify(ImagePath):
    import os

    results = {}
    for file_name in os.listdir(ImagePath):
        if os.path.isfile(os.path.join(ImagePath, file_name)):
            input_image_path = os.path.join(ImagePath, file_name)
            topresults = caffe_classify_image(input_image_path)
            results[file_name] = topresults

    return results

import sys
if __name__ == "__main__":
    results = caffe_classify(sys.argv[1])
