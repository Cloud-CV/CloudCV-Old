from __future__ import absolute_import
from celeryTasks.celery import app


# The function takes as input:
# 1) src_path: Input image or directory.
# 2) socketid: The socket id of the connection.
# 3) output_path: Directory where the mat files are to be stored.
# 4) result_path: Directory accessible by web.
#    It should be full path in case of a single file, else the directory path.
# NOTE:
# 1) Its job is to find the decaf features of images according to the pre-trained model.
# 2) ignore_result=True signifies that celery won't pass any result to the backend.
# 3) It is important to import all the modules only inside the function
# 4) When running with new version of caffe do np.load(MEAN_FILE).mean(1).mean(1)
@app.task(ignore_result=True)
def decafImages(src_path, socketid, output_path, result_path):
	#Establishing connection to send results and write messages
	import redis, json
	rs = redis.StrictRedis(host='redis', port=6379)

	try:
		import caffe, numpy as np, os, glob, time, operator, scipy.io as sio

		#Needed to fix error https://github.com/BVLC/caffe/issues/438
		from skimage import io; io.use_plugin('matplotlib')

		#Caffe Initialisations
		CAFFE_DIR = os.path.normpath(os.path.join(os.path.dirname(caffe.__file__),"..",".."))
		MODEL_FILE = os.path.join(CAFFE_DIR, 'models/bvlc_reference_caffenet/deploy.prototxt')
		PRETRAINED = os.path.join(CAFFE_DIR, 'models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel')

		#Set CPU mode
		caffe.set_mode_cpu()

		# Make classifier.
		classifier = caffe.Classifier(MODEL_FILE, PRETRAINED)

		#Find decaf features and send Results
		if os.path.isdir(src_path):
			for input_file in glob.glob(os.path.join(src_path, '*')):
				if os.path.isfile(input_file):
					rs.publish('chat', json.dumps({'message': 'Processing '+os.path.basename(input_file), 'socketid': str(socketid)}))

					#Loading Image
					input_image = caffe.io.load_image(input_file)
					
					#Finding decaf features
					start = time.time()
					classifier.predict([input_image])
					blobs = classifier.blobs.items()
					features = blobs[-3][1].data[:,:,0,0]
					features_center = blobs[-3][1].data[4,:,0,0]
					features_center = np.resize(features_center, (1,4096))
					timeMsg = "Completed in %.2f s." % (time.time() - start)
					rs.publish('chat', json.dumps({'message': timeMsg, 'socketid': str(socketid)}))
					
					#Saving decaf features
					matfile = {}
					matfile['decaf'] = features
					matfile['decaf_center'] = features_center
					out_file = os.path.join(output_path, os.path.basename(input_file)+'.mat')
					publish_file = os.path.join(result_path, os.path.basename(input_file)+'.mat')
					sio.savemat(out_file, matfile)
					rs.publish('chat', json.dumps({'web_result': publish_file, 'socketid': str(socketid)}))
		else:
			input_file = src_path

			rs.publish('chat', json.dumps({'message': 'Processing '+os.path.basename(input_file), 'socketid': str(socketid)}))
			
			#Loading Image
			input_image = caffe.io.load_image(input_file)
			
			#Finding decaf features
			start = time.time()
			classifier.predict([input_image])
			blobs = classifier.blobs.items()
			features = blobs[-3][1].data[:,:,0,0]
			features_center = blobs[-3][1].data[4,:,0,0]
			features_center = np.resize(features_center, (1,4096))
			timeMsg = "Completed in %.2f s." % (time.time() - start)
			rs.publish('chat', json.dumps({'message': timeMsg, 'socketid': str(socketid)}))
			
			#Saving decaf features
			matfile = {}
			matfile['decaf'] = features
			matfile['decaf_center'] = features_center
			out_file = os.path.join(result_path, os.path.basename(input_file)+'.mat')
			out_file = os.path.join(output_path, os.path.basename(input_file)+'.mat')
			publish_file = os.path.join(result_path, os.path.basename(input_file)+'.mat')
			sio.savemat(out_file, matfile)
			rs.publish('chat', json.dumps({'web_result': publish_file, 'socketid': str(socketid)}))

		rs.publish('chat', json.dumps({'message': 'Thank you for using CloudCV', 'socketid': str(socketid)}))

	except Exception as e:
		#In case of an error, send the whole error with traceback
		import traceback
		rs.publish('chat', json.dumps({'message': str(traceback.format_exc()), 'socketid': str(socketid)}))
