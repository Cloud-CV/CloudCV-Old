import os
import sys
import numpy as np
import leveldb
import caffe
from caffe.proto import caffe_pb2
from glob import glob
import time
import math
from joblib import Parallel, delayed
import multiprocessing
import scipy.io as sio
import shutil
import subprocess
import app.conf as conf


def trainaclass(Imagepath):
    caffe_root = '/home/ubuntu/caffe/'
    train_features = np.zeros((4096, 0))

    # Extract features from input training images using feature extraction tool
    # Input: images in the directory Imagepath
    train_files = (glob(os.path.join(Imagepath, '*')))
    shutil.copy2(caffe_root + 'examples/feature_extraction/imagenet_val.prototxt', Imagepath)
    os.system('cp ' + caffe_root + 'examples/feature_extraction/imagenet_val.prototxt ' + Imagepath)
    s = open(os.path.join(Imagepath, 'imagenet_val.prototxt')).read()
    s = s.replace(
        'layers {\n  name: "data"\n  type: IMAGE_DATA\n  top: "data"\n  top: "label"\n  image_data_param {\n    source: "examples/_temp/file_list.txt"\n    batch_size: 50\n    new_height: 256\n    new_width: 256\n  }\n  transform_param {\n    crop_size: 227\n    mean_file: "data/ilsvrc12/imagenet_mean.binaryproto"\n    mirror: false\n  }\n}',
        'layers {\n  name: "data"\n  type: IMAGE_DATA\n  top: "data"\n  top: "label"\n  image_data_param {\n    source: "' + Imagepath + '/file_list.txt"\n    batch_size: 1\n    new_height: 256\n    new_width: 256\n  }\n  transform_param {\n    crop_size: 227\n    mean_file: "' + caffe_root + 'data/ilsvrc12/imagenet_mean.binaryproto"\n    mirror: false\n  }\n}')
    f = open(os.path.join(Imagepath, 'imagenet_val.prototxt'), 'w')
    f.write(s)
    f.close()

    f = open(os.path.join(Imagepath, 'file_list.txt'), 'w')
    for l in train_files:
        f.write(l + ' 0\n')
    f.close()

    train_size = len(train_files)
    p1 = caffe_root + 'build/tools/extract_features.bin '
    p2 = caffe_root + 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel '
    p3 = os.path.join(Imagepath, 'imagenet_val.prototxt fc7') + ' ' + os.path.join(Imagepath,
                                                                                   'features') + ' %d GPU' % (train_size)
    os.system(p1 + p2 + p3)

    p1 = caffe_root + 'build/tools/extract_features.bin'
    p2 = caffe_root + 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel'
    p3 = '"' + os.path.join(Imagepath, 'imagenet_val.prototxt') +'"'
    p4 ='"' + os.path.join(Imagepath, 'features')+'"'
    execlist = [p1,p2,p3,'fc7', p4]
    execlist.append(str(train_size))
    execlist.append('GPU')
    # os.system(p1 + p2 + p3)
    popen = subprocess.Popen(execlist, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    popen.communicate()

    train_features = np.zeros((4096, train_size))

    # Convert the train_features leveldb to numpy array
    db = leveldb.LevelDB(os.path.join(Imagepath, 'features'))
    for k in range(len(train_files)):
        datum = caffe_pb2.Datum.FromString(db.Get(str(k)))
        train_features = np.hstack([train_features, caffe.io.datum_to_array(datum)[0, :, :]])

    mean_new = np.resize(np.mean(train_features, axis=1), (4096, 1))
    sigmainv = np.load(os.path.join(conf.EXEC_DIR, 'LDA_files', 'sigmainv.npy'))

    weight_new = np.dot(sigmainv, mean_new)
    print 'min weight = ', np.min(weight_new)
    print 'max weight = ', np.max(weight_new)
    w0 = math.log(train_size) - math.log(1281167) - 0.5 * np.dot(np.dot(mean_new.transpose(), sigmainv), mean_new)
    print 'bias is ', w0
    # print 'Got the new weight vector at ',(time.clock()-start)
    os.system('rm -rf ' + Imagepath + '/features')
    os.system('rm -rf ' + Imagepath + '/imagenet_val.prototxt')
    os.system('rm -rf ' + Imagepath + '/file_list.txt')

    return (w0, weight_new)


def modelUpdate(jobPath):
    start = time.clock()
    caffe_root = '/home/ubuntu/caffe/'
    train_path = os.path.join(jobPath, 'train')
    model_path = os.path.join(jobPath, 'util')
    dirs = [os.path.join(train_path, d) for d in os.listdir(train_path) if os.path.isdir(os.path.join(train_path, d))]
    new_labels = np.array(os.listdir(train_path), dtype=object)
    print new_labels
    sio.savemat(os.path.join(model_path, 'new_labels.mat'), {'WNID': new_labels})
    print dirs
    num_labels = len(dirs)

    s = open(os.path.join(caffe_root, 'models/bvlc_reference_caffenet/deploy.prototxt')).read()
    s = s.replace(
        'layers {\n  name: "fc8"\n  type: INNER_PRODUCT\n  bottom: "fc7"\n  top: "fc8"\n  inner_product_param {\n    num_output: 1000\n  }\n}\nlayers {\n  name: "prob"\n  type: SOFTMAX\n  bottom: "fc8"\n  top: "prob"\n}',
        'layers {\n  name: "fc8-new"\n  type: INNER_PRODUCT\n  bottom: "fc7"\n  top: "fc8-new"\n  inner_product_param {\n    num_output: %d\n  }\n}\nlayers {\n  name: "prob"\n  type: SOFTMAX\n  bottom: "fc8-new"\n  top: "prob"\n}' % (
            1000 + num_labels))
    f = open(os.path.join(model_path, 'newCaffeModel.prototxt'), 'w')
    f.write(s)
    f.close()
    print 'Time when prototxt is prepared is ', time.clock() - start

    net = caffe.Classifier(caffe_root + 'models/bvlc_reference_caffenet/deploy.prototxt',
                           caffe_root + 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel')
    # net = caffe.Classifier(caffe_root+'models/bvlc_alexnet/deploy.prototxt', caffe_root+'models/bvlc_alexnet/bvlc_alexnet.caffemodel')

    net_new = caffe.Classifier(os.path.join(model_path, 'newCaffeModel.prototxt'),
                               caffe_root + 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel')
    net_new.set_mean('data', np.load(caffe_root + 'python/caffe/imagenet/ilsvrc_2012_mean.npy'))  # ImageNet mean
    net_new.set_raw_scale('data', 255)
    net_new.set_channel_swap('data', (2, 1, 0))
    #net_new.set_phase_test()
    #net_new.set_mode_gpu()
    pr = 'fc8'
    pr_new = 'fc8-new'
    fc_params = (net.params[pr][0].data, net.params[pr][1].data)
    fc_params_new = (net_new.params[pr_new][0].data, net_new.params[pr_new][1].data)
    net.set_mean('data', np.load(caffe_root + 'python/caffe/imagenet/ilsvrc_2012_mean.npy'))  # ImageNet mean
    net.set_raw_scale('data', 255)
    net.set_channel_swap('data', (2, 1, 0))
    #net.set_phase_test()
    #net.set_mode_gpu()
    caffe.set_mode_gpu()
    caffe.set_phase_test()
    print '{} weights are {} dimensional and biases are {} dimensional'.format(pr_new, fc_params_new[0].shape,
                                                                               fc_params_new[1].shape)
    fc_params_new[1][:, :, :, :1000] = fc_params[1]
    fc_params_new[0][:, :, :1000, :] = fc_params[0]
    print 'max bias = ', max(fc_params_new[1][0, 0, 0, :])
    print 'min bias = ', min(fc_params_new[1][0, 0, 0, :])
    print 'max weight =', max(fc_params_new[0][0, 0, 0, :])
    print 'min weight =', min(fc_params_new[0][0, 0, 0, :])
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs=num_cores)(delayed(trainaclass)(dirs[label].replace(' ', '_')) for label in range(num_labels))

    for label in range(num_labels):
        fc_params_new[1][0, 0, 0, 1000 + label] = results[label][0]
        fc_params_new[0][0, 0, 1000 + label, :] = results[label][1].transpose()[0, :]

    net_new.save(os.path.join(model_path, 'newCaffeModel.caffemodel'))

    print 'Time taken = ', time.clock() - start


if __name__ == '__main__':
    modelUpdate(sys.argv[1])
