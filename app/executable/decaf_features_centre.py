def decaf_features_centre(ImagePath):
	import sys
	import numpy
	import scipy.io as io
	sys.path.append("/share/code/caffe/python")
	from caffe import imagenet

	# Set the right path to your model file, pretrained model,
	# and the image you would like to classify.
	MODEL_FILE = '/share/code/caffe/examples_old/imagenet_deploy.prototxt'
	PRETRAINED = '/share/code/caffe/models/caffe_reference_imagenet_model'
	IMAGE_FILE = ImagePath
	net = imagenet.ImageNetClassifier(MODEL_FILE, PRETRAINED)
	net.caffenet.set_phase_test()
	net.caffenet.set_mode_cpu()
	
	# Compute the features
	net.predict(IMAGE_FILE)
	blobs = net.caffenet.blobs() 
	features = blobs[-3].data[4]
	features = numpy.resize(features, (1,4096))
	return features
