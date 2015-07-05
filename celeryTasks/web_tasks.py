"""
This file caters to all the jobs for the web server.

Author - Prashant Jalan
"""

from __future__ import absolute_import
from celeryTasks.celery import app

#Establishing connection to send results and write messages
import redis
rs = redis.StrictRedis(host='redis', port=6379)

"""
The function takes as input:
1) src_path: Input image, directory, or npy. 
2) socketid: The socket id of the connection.
NOTE:
1) Its job is to classify the images according to the pre-trained model.
2) ignore_result=True signifies that celery won't pass any result to the backend.
3) It is important to import all the modules only inside the function
4) When running with new version of caffe do np.load(MEAN_FILE).mean(1).mean(1)
"""
@app.task(ignore_result=True)
def classifyImages(src_path, socketid):
	try:
		import caffe, numpy as np, os, glob, time, operator, scipy.io as sio

		#Used to assign labels to the results
		matWNID = sio.loadmat(os.path.join(os.path.dirname(__file__),'WNID.mat'))
		WNID_cells = matWNID['wordsortWNID']

		#Caffe Initialisations
		CAFFE_DIR = os.path.normpath(os.path.join(os.path.dirname(caffe.__file__),"..",".."))
		MODEL_FILE = os.path.join(CAFFE_DIR, 'models/bvlc_reference_caffenet/deploy.prototxt')
		PRETRAINED = os.path.join(CAFFE_DIR, 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel')
		MEAN_FILE = os.path.join(CAFFE_DIR, 'python/caffe/imagenet/ilsvrc_2012_mean.npy')
		RAW_SCALE = 255.0
		IMAGE_DIMS = (256, 256)
		CHANNEL_SWAP = (2, 1, 0)

		#Set CPU mode
		caffe.set_mode_cpu()

		# Make classifier.
		classifier = caffe.Classifier(MODEL_FILE, PRETRAINED, image_dims=IMAGE_DIMS, 
		mean=np.load(MEAN_FILE).mean(1).mean(1), raw_scale=RAW_SCALE,
		channel_swap=CHANNEL_SWAP)

		# Load numpy array (.npy), directory glob (*), or image file.
		input_file = os.path.abspath(src_path)
		if input_file.endswith('npy'):
			inputs = np.load(args.input_file)
		elif os.path.isdir(input_file):
			inputs = [caffe.io.load_image(im_f) for im_f in glob.glob(input_file + '/*')]
		else:
			inputs = [caffe.io.load_image(input_file)]

		# Classify.
		prediction = classifier.predict(inputs)

		#Send Results
		if os.path.isdir(input_file):
			for im_f in glob.glob(input_file + '/*'):
				dictionary = {}
				for i, j in enumerate(prediction[count]):
					dictionary[i] = j
				predsorted = sorted(dictionary.iteritems(), key=operator.itemgetter(1), reverse=True)
				top5 = predsorted[0:5]
				topresults = []
				for item in top5:
					topresults.append([str(WNID_cells[item, 0][0][0]),str(item[1])])

				web_result = {}
				web_result[str(im_f)] = topresults
				rs.publish('chat', json.dumps({'web_result': json.dumps(web_result), 'socketid': str(socketid)}))
		
		else:
			dictionary = {}
			for i, j in enumerate(prediction[0]):
				dictionary[i] = j
			predsorted = sorted(dictionary.iteritems(), key=operator.itemgetter(1), reverse=True)
			top5 = predsorted[0:5]
			topresults = [] 
			for item in top5:
				topresults.append([str(WNID_cells[item, 0][0][0]),str(item[1])])

			web_result = {}
			web_result[str(input_file)] = topresults
			rs.publish('chat', json.dumps({'web_result': json.dumps(web_result), 'socketid': str(socketid)}))
		
		rs.publish('chat', json.dumps({'message': 'Thank you for using CloudCV', 'socketid': str(socketid)}))

	except Exception as e:
		#In case of an error, print the whole error with traceback
		import traceback
		rs.publish('chat', json.dumps({'message': str(traceback.format_exc()), 'socketid': str(socketid)}))

