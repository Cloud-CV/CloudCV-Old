from __future__ import absolute_import
from glob import glob

from celeryTasks.celery import app
from cloudcv17 import config

# Module imports
import os
import redis
import numpy as np
import leveldb
import time
import math
import shutil
import json
import traceback
import operator
import scipy.io as sio

# directory where all the executables reside
EXEC_DIR = os.path.join('/CloudCV_Server', 'app', 'executable')
matWNID = sio.loadmat(os.path.join(EXEC_DIR, 'WNID.mat'))
WNID_cells = matWNID['wordsortWNID']


# The functions are mostly copied from app.executable.LDA_files.train_fast
@app.task(ignore_result=True)
def trainImages(jobPath, socketid):
    from caffe.proto import caffe_pb2

    import caffe

    caffe_root = os.path.normpath(os.path.join(os.path.dirname(caffe.__file__), "..", ".."))

    # Establishing connection to send results and write messages
    rs = redis.StrictRedis(host=config.REDIS_HOST, port=6379)

    def trainaclass(Imagepath):

        train_features = np.zeros((4096, 0))

        # Extract features from input training images using feature extraction tool
        # Input: images in the directory Imagepath
        train_files = (glob(os.path.join(Imagepath, '*')))
        shutil.copy2(os.path.join(caffe_root, 'examples/feature_extraction/imagenet_val.prototxt'), Imagepath)
        os.system('cp ' + os.path.join(caffe_root, 'examples/feature_extraction/imagenet_val.prototxt') + ' ' + Imagepath)
        s = open(os.path.join(Imagepath, 'imagenet_val.prototxt')).read()
        s = s.replace(
            'layers {\n  name: "data"\n  type: IMAGE_DATA\n  top: "data"\n  top: "label"\n  image_data_param {\n    source: "examples/_temp/file_list.txt"\n    batch_size: 50\n    new_height: 256\n    new_width: 256\n  }\n  transform_param {\n    crop_size: 227\n    mean_file: "data/ilsvrc12/imagenet_mean.binaryproto"\n    mirror: false\n  }\n}',
            'layers {\n  name: "data"\n  type: IMAGE_DATA\n  top: "data"\n  top: "label"\n  image_data_param {\n    source: "' + Imagepath + '/file_list.txt"\n    batch_size: 1\n    new_height: 256\n    new_width: 256\n  }\n  transform_param {\n    crop_size: 227\n    mean_file: "' + caffe_root + '/data/ilsvrc12/imagenet_mean.binaryproto"\n    mirror: false\n  }\n}')
        f = open(os.path.join(Imagepath, 'imagenet_val.prototxt'), 'w')
        f.write(s)
        f.close()

        f = open(os.path.join(Imagepath, 'file_list.txt'), 'w')
        for l in train_files:
            f.write(l + ' 0\n')
        f.close()

        train_size = len(train_files)
        p1 = os.path.join(caffe_root, 'build/tools/extract_features ')
        p2 = os.path.join(caffe_root, 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel ')
        p3 = os.path.join(Imagepath, 'imagenet_val.prototxt fc7') + ' ' + os.path.join(Imagepath,
                                                                                       'features') + ' %d GPU' % (train_size)

        rs.publish('chat', json.dumps({'message': "COMMAND: " + p1 + p2 + p3, 'socketid': str(socketid)}))
        os.system(p1 + p2 + p3)

        # Convert the train_features leveldb to numpy array
        rs.publish('chat', json.dumps({'message': os.path.join(Imagepath, 'features'), 'socketid': str(socketid)}))
        db = leveldb.LevelDB(os.path.join(Imagepath, 'features'))

        for k in range(len(train_files)):
            datum = caffe_pb2.Datum.FromString(db.Get(str(k)))
            train_features = np.hstack([train_features, caffe.io.datum_to_array(datum)[0, :, :]])

        mean_new = np.resize(np.mean(train_features, axis=1), (4096, 1))
        sigma_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'LDA_files', 'sigmainv.npy')
        sigmainv = np.load(sigma_file)

        weight_new = np.dot(sigmainv, mean_new)
        w0 = - 0.5 * np.dot(np.dot(mean_new.transpose(), sigmainv), mean_new)
        # w0 = math.log(train_size) - math.log(1281167) - 0.5 * np.dot(np.dot(mean_new.transpose(), sigmainv), mean_new)

        # print 'bias is ', w0
        os.system('rm -rf ' + Imagepath + '/features')
        os.system('rm -rf ' + Imagepath + '/imagenet_val.prototxt')
        os.system('rm -rf ' + Imagepath + '/file_list.txt')

        return (w0, weight_new)

    try:
        if not os.path.exists(jobPath):
            raise Exception('No training images has been provided for this job.')

        start = time.time()

        train_path = os.path.join(jobPath, 'train')
        model_path = os.path.join(jobPath, 'util')
        dirs = [os.path.join(train_path, d) for d in os.listdir(train_path)
                if os.path.isdir(os.path.join(train_path, d))]
        new_labels = np.array(os.listdir(train_path), dtype=object)
        sio.savemat(os.path.join(model_path, 'new_labels.mat'), {'WNID': new_labels})
        num_labels = len(dirs)

        s = open(os.path.join(caffe_root, 'models/bvlc_reference_caffenet/deploy.prototxt')).read()
        s = s.replace('fc8', 'fc8-new')
        s = s.replace('1000', '%d' % (1000 + num_labels))

        f = open(os.path.join(model_path, 'newCaffeModel.prototxt'), 'w')
        f.write(s)
        f.close()

        net = caffe.Classifier(os.path.join(caffe_root, 'models/bvlc_reference_caffenet/deploy.prototxt'),
                               os.path.join(caffe_root, 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel'))

        net_new = caffe.Classifier(os.path.join(model_path, 'newCaffeModel.prototxt'),
                                   os.path.join(caffe_root, 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel'))

        pr = 'fc8'
        pr_new = 'fc8-new'
        fc_params = (net.params[pr][0].data, net.params[pr][1].data)
        fc_params_new = (net_new.params[pr_new][0].data, net_new.params[pr_new][1].data)
        fc_params_new[1][:, :, :, :1000] = fc_params[1]
        fc_params_new[0][:, :, :1000, :] = fc_params[0]

        results = [trainaclass(dirs[label]) for label in range(num_labels)]

        for label in range(num_labels):
            fc_params_new[1][0, 0, 0, 1000 + label] = results[label][0] - math.log(1000 + num_labels)
            # fc_params_new[1][0, 0, 0, 1000 + label] = results[label][0]
            fc_params_new[0][0, 0, 1000 + label, :] = results[label][1].transpose()[0, :]

        net_new.save(os.path.join(model_path, 'newCaffeModel.caffemodel'))

        timeMsg = "Completed in %.2f s." % (time.time() - start)
        rs.publish('chat', json.dumps({'message': timeMsg, 'socketid': str(socketid)}))

        completionMsg = 'Finished training your model with the new categories. Now, upload some test images to test this model.'
        rs.publish('chat', json.dumps({'message': completionMsg, 'socketid': str(socketid)}))

    except:
        # In case of an error, send the whole error with traceback
        import traceback
        rs.publish('chat', json.dumps({'message': str(traceback.format_exc()), 'socketid': str(socketid)}))


def caffe_classify_image(net, single_image, new_labels_cells):
    import caffe

    topresults = []
    try:
        input_image = caffe.io.load_image(single_image)
        prediction = net.predict([input_image])
        map = {}
        for i, j in enumerate(prediction[0]):
            map[i] = j

            predsorted = sorted(map.iteritems(), key=operator.itemgetter(1), reverse=True)
            top5 = predsorted[0:5]

            for i in top5:
                if (i[0] >= 1000):
                    topresults.append([str(new_labels_cells[0, i[0]-1000][0]), str(i[1])])
                else:
                    topresults.append([str(WNID_cells[i, 0][0][0]), str(i[1])])
    except Exception as e:
        print(str(e))

    return topresults


# The functions are mostly copied from app.executable.test
# and classify_wrapper_local in trainaclass_views
@app.task(ignore_result=True)
def customClassifyImages(jobPath, socketid, result_path):

    import caffe
    import scipy.io as sio

    # Establishing connection to send results and write messages
    rs = redis.StrictRedis(host=config.REDIS_HOST, port=6379)

    try:
        ImagePath = os.path.join(jobPath, 'test')
        modelPath = os.path.join(jobPath, 'util')

        new_labels = sio.loadmat(os.path.join(modelPath, 'new_labels.mat'))
        new_labels_cells = new_labels['WNID']

        # Set the right path to your model file, pretrained model,
        # and the image you would like to classify.
        MODEL_FILE = os.path.join(modelPath, 'newCaffeModel.prototxt')
        PRETRAINED = os.path.join(modelPath, 'newCaffeModel.caffemodel')

        # caffe.set_phase_test()
        caffe.set_mode_cpu()

        CAFFE_DIR = os.path.normpath(os.path.join(os.path.dirname(caffe.__file__), "..", ".."))
        net = caffe.Classifier(MODEL_FILE, PRETRAINED,
                               mean=np.load(os.path.join(
                                   CAFFE_DIR, 'python/caffe/imagenet/ilsvrc_2012_mean.npy')).mean(1).mean(1),
                               channel_swap=(2, 1, 0),
                               raw_scale=255,
                               image_dims=(256, 256))

        if os.path.isdir(ImagePath):
            for file_name in os.listdir(ImagePath):
                image_path = os.path.join(ImagePath, file_name)
                if os.path.isfile(image_path):
                    tags = caffe_classify_image(net, image_path, new_labels_cells)  # NOTE: UNDEFINED NAME caffe_classify_image
                    webResult = {}
                    webResult[os.path.join(result_path, file_name)] = tags
                    rs.publish('chat',
                               json.dumps({'web_result': json.dumps(webResult), 'socketid': str(socketid)}))

        rs.publish('chat', json.dumps(
            {'message': 'Classification completed. Thank you for using CloudCV', 'socketid': str(socketid)}))

    except:
        rs.publish('chat', json.dumps({'message': str(traceback.format_exc()), 'socketid': str(socketid)}))
