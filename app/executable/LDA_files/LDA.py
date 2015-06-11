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

def classify(Imagepath):
	caffe_root = '~/caffe/'
	#print 'Imagepath is ',Imagepath
	train_features = np.zeros((4096,0))
	
	# Extract features from input training images using feature extraction tool
	# Input: images in the directory Imagepath
	# Output: 'features' leveldb in dir train_features
	train_files = (glob(os.path.join(Imagepath,'*.jpg')))
	#os.system('rm -rf '+caffe_root+'dir_LDA/train_features/features')
	os.system('cp ../examples/feature_extraction/imagenet_val.prototxt '+Imagepath)
        s = open(Imagepath+"/imagenet_val.prototxt").read()
        s = s.replace('layers {\n  name: "data"\n  type: IMAGE_DATA\n  top: "data"\n  top: "label"\n  image_data_param {\n    source: "examples/_temp/file_list.txt"\n    batch_size: 50\n    new_height: 256\n    new_width: 256\n  }\n  transform_param {\n    crop_size: 227\n    mean_file: "data/ilsvrc12/imagenet_mean.binaryproto"\n    mirror: false\n  }\n}', 'layers {\n  name: "data"\n  type: IMAGE_DATA\n  top: "data"\n  top: "label"\n  image_data_param {\n    source: "'+Imagepath+'/file_list.txt"\n    batch_size: 1\n    new_height: 256\n    new_width: 256\n  }\n  transform_param {\n    crop_size: 227\n    mean_file: "../data/ilsvrc12/imagenet_mean.binaryproto"\n    mirror: false\n  }\n}')
        f = open(Imagepath+"/imagenet_val.prototxt", 'w')
        f.write(s)
        f.close()

	os.system('rm -rf '+Imagepath+'/features')
	#os.system('rm -rf '+caffe_root+'dir_LDA/train_features/file_list.txt')
	os.system('rm -rf '+Imagepath+'/file_list.txt')
	f= open(Imagepath + '/file_list.txt','w')
	#f= open(caffe_root + 'dir_LDA/train_features/file_list.txt','w')
	for l in train_files:
		f.write(l + ' 0\n')
	f.close()
	train_size = len(train_files)
	p1 = caffe_root + 'build/tools/extract_features.bin '
	p2 = caffe_root + 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel '
	#p3 = caffe_root + 'dir_LDA/train_features/imagenet_val.prototxt fc7 '+Imagepath+'features %d GPU 1' %(train_size)
	p3 = Imagepath + '/imagenet_val.prototxt fc7 '+Imagepath+'/features %d GPU 1' %(train_size)	
	os.system('./'+p1+p2+p3)

	print 'Extracted features of train images at ',(time.clock()-start)

        train_features = np.zeros((4096,train_size))
	# Convert the train_features leveldb to numpy array
	db = leveldb.LevelDB(Imagepath+'/features')
	for k in range(len(train_files)):
		datum = caffe_pb2.Datum.FromString(db.Get(str(k)))
		train_features = np.hstack([train_features,caffe.io.datum_to_array(datum)[0,:,:]])

	mean_new = np.resize(np.mean(train_features,axis=1),(4096,1))
	sigmainv = np.load('sigmainv.npy')

	weight_new = np.dot(sigmainv,mean_new)
        #w0 = 0
	w0 = math.log(train_size)-math.log(1281167) - 0.5*np.dot(np.dot(mean_new.transpose(),sigmainv),mean_new)
        print 'Got the new weight vector at ',(time.clock()-start)
	return (w0,weight_new)


if __name__ == '__main__':
	start = time.clock()
	dirs = [os.path.join(train_path,d) for d in os.listdir(train_path) if os.path.isdir(os.path.join(train_path,d))]
	num_labels = len(dirs)

	s = open("../models/bvlc_reference_caffenet/deploy.prototxt").read()
	s = s.replace('layers {\n  name: "fc8"\n  type: INNER_PRODUCT\n  bottom: "fc7"\n  top: "fc8"\n  inner_product_param {\n    num_output: 1000\n  }\n}\nlayers {\n  name: "prob"\n  type: SOFTMAX\n  bottom: "fc8"\n  top: "prob"\n}', 'layers {\n  name: "fc8-new"\n  type: INNER_PRODUCT\n  bottom: "fc7"\n  top: "fc8-new"\n  inner_product_param {\n    num_output: %d\n  }\n}\nlayers {\n  name: "prob"\n  type: SOFTMAX\n  bottom: "fc8-new"\n  top: "prob"\n}'%(1000+num_labels))
	f = open("newcaffemodel.prototxt", 'w')
	f.write(s)
	f.close()
	print 'Time when prototxt is prepared is ',time.clock()-start
	caffe_root = '~/caffe/'
	train_path = os.path.join(sys.argv[1],'train/')
	#dirs = [os.path.join(train_path,d) for d in os.listdir(train_path) if os.path.isdir(os.path.join(train_path,d))]

        test_path = os.path.join(sys.argv[1],'test/')
        test_files = (glob(os.path.join(test_path,'*.jpg')))
	test_size = len(test_files)
        net = caffe.Classifier('../models/bvlc_reference_caffenet/deploy.prototxt', '../models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel')

        net_new = caffe.Classifier('newcaffemodel.prototxt', '../models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel')
        net_new.set_mean('data', np.load(caffe_root + 'python/caffe/imagenet/ilsvrc_2012_mean.npy'))  # ImageNet mean
        net_new.set_raw_scale('data', 255)
        net_new.set_channel_swap('data', (2,1,0))
        net_new.set_phase_test()
        net_new.set_mode_gpu()
        pr = 'fc8'
        pr_new = 'fc8-new'
        fc_params = (net.params[pr][0].data, net.params[pr][1].data)
        fc_params_new = (net_new.params[pr_new][0].data, net_new.params[pr_new][1].data)
        net.set_mean('data', np.load(caffe_root + 'python/caffe/imagenet/ilsvrc_2012_mean.npy'))  # ImageNet mean
        net.set_raw_scale('data', 255)
        net.set_channel_swap('data', (2,1,0))
        net.set_phase_test()
        net.set_mode_gpu()
        print '{} weights are {} dimensional and biases are {} dimensional'.format(pr_new, fc_params_new[0].shape, fc_params_new[1].shape)
        fc_params_new[1][:,:,:,:1000] = fc_params[1]
        fc_params_new[0][:,:,:1000,:] = fc_params[0]

	num_cores = multiprocessing.cpu_count()
	results = Parallel(n_jobs=num_cores)(delayed(classify)(dirs[label]) for label in range(num_labels))
	print results
	print results[0][0]
	for label in range(num_labels):
        #	w0,weight_new = classify(dirs[label])
		fc_params_new[1][0,0,0,1000+label] = results[label][0]
		fc_params_new[0][0,0,1000+label,:] = results[label][1].transpose()[0,:]
        
        scores_new = np.zeros(test_size)
        scores = np.zeros(test_size)
        for i in range(test_size):
		#print test_files[i]
                scores_new[i] = net_new.predict([caffe.io.load_image(test_files[i])])[0].argmax()
                scores[i] = net.predict([caffe.io.load_image(test_files[i])])[0].argmax()
		#print scores_new[i]
        print scores_new

        net_new.save('newcaffemodel.caffemodel')

        print 'Time taken = ',time.clock() - start

