from __future__ import absolute_import
from celeryTasks.celery import app


# The function takes as input:
# 1) src_path: Input image, directory, or npy. 
# 2) socketid: The socket id of the connection.
# 3) result_path: The folder path where the result image will be stored.
#    It should be full path in case of a single file, else the directory path.
# NOTE:
# 1) Its job is to classify the images according to the pre-trained model.
# 2) ignore_result=True signifies that celery won't pass any result to the backend.
# 3) It is important to import all the modules only inside the function
# 4) When running with new version of caffe do np.load(MEAN_FILE).mean(1).mean(1)
@app.task(ignore_result=True)
def classifyImages(src_path, socketid, result_path):
	#Establishing connection to send results and write messages
	import redis, json
	rs = redis.StrictRedis(host='redis', port=6379)

	try:
		import caffe, numpy as np, os, glob, time, operator, scipy.io as sio

		#Used to assign labels to the results
		matWNID = sio.loadmat(os.path.join(os.path.dirname(os.path.abspath(__file__)),'WNID.mat'))
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
		
		#Classify and Send Results
		if os.path.isdir(src_path):
			for input_file in glob.glob(input_file + '/*'):
				if os.path.isfile(input_file):
					#Load file
					rs.publish('chat', json.dumps({'message': 'Processing '+os.path.basename(input_file), 'socketid': str(socketid)}))
					inputs = [caffe.io.load_image(input_file)]
					
					# Classify.
					start = time.time()
					prediction = classifier.predict(inputs)
					timeMsg = "Completed in %.2f s." % (time.time() - start)
					rs.publish('chat', json.dumps({'message': timeMsg, 'socketid': str(socketid)}))

					dictionary = {}
					for i, j in enumerate(prediction[0]):
						dictionary[i] = j
					predsorted = sorted(dictionary.iteritems(), key=operator.itemgetter(1), reverse=True)
					top5 = predsorted[0:5]
					topresults = []
					for item in top5:
						topresults.append([str(WNID_cells[item, 0][0][0]),str(item[1])])

					web_result = {}
					web_result[os.path.join(result_path, os.path.basename(input_file))] = topresults
					rs.publish('chat', json.dumps({'web_result': json.dumps(web_result), 'socketid': str(socketid)}))
		
		else:
			input_file = src_path
			
			#Load file
			rs.publish('chat', json.dumps({'message': 'Processing '+os.path.basename(input_file), 'socketid': str(socketid)}))
			inputs = [caffe.io.load_image(input_file)]
			
			# Classify.
			start = time.time()
			prediction = classifier.predict(inputs)
			timeMsg = "Completed in %.2f s." % (time.time() - start)
			rs.publish('chat', json.dumps({'message': timeMsg, 'socketid': str(socketid)}))

			dictionary = {}
			for i, j in enumerate(prediction[0]):
				dictionary[i] = j
			predsorted = sorted(dictionary.iteritems(), key=operator.itemgetter(1), reverse=True)
			top5 = predsorted[0:5]
			topresults = []
			for item in top5:
				topresults.append([str(WNID_cells[item, 0][0][0]),str(item[1])])

			web_result = {}
			web_result[result_path] = topresults
			rs.publish('chat', json.dumps({'web_result': json.dumps(web_result), 'socketid': str(socketid)}))
		
		rs.publish('chat', json.dumps({'message': 'Thank you for using CloudCV', 'socketid': str(socketid)}))

	except Exception as e:
		#In case of an error, send the whole error with traceback
		import traceback
		rs.publish('chat', json.dumps({'message': str(traceback.format_exc()), 'socketid': str(socketid)}))

