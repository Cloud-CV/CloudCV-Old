import operator
import os


def caffe_classify_image(ImagePath):
    import sys

    sys.path.append("/share/code/caffe/python")
    import scipy.io as sio
    from caffe import imagenet

    results = {}

    matWNID = sio.loadmat('/var/www/html/cloudcv/fileupload/executable/WNID.mat')
    WNID_cells = matWNID['wordsortWNID']

    # Set the right path to your model file, pretrained model,
    # and the image you would like to classify.
    MODEL_FILE = '/share/code/caffe/examples_old/imagenet_deploy.prototxt'
    PRETRAINED = '/share/code/caffe/models/caffe_reference_imagenet_model'
    numoutputs = 1000
    net = imagenet.ImageNetClassifier(MODEL_FILE, PRETRAINED, False, numoutputs)

    # Predict the image classes, then return the top 5 indicies
    net.caffenet.set_phase_test()
    net.caffenet.set_mode_cpu()

    print('Making predictions...')

    if os.path.isfile(ImagePath):
        prediction = net.predict(ImagePath)
        print('Computed scores')
        map = {}
        for i, j in enumerate(prediction):
            map[i] = j

        print('Getting top five tags...')
        predsorted = sorted(map.iteritems(), key=operator.itemgetter(1), reverse=True)
        top5 = predsorted[0:5]
        topresults = {}

        m = 0
        n = 1
        for i in top5:
            topresults[str(WNID_cells[i, 0][0][0])] = str(i[1])
        results[ImagePath] = topresults

    return results