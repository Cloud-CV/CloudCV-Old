from __future__ import absolute_import
from celeryTasks.celery import app
	
# The function takes as input:
# 1) src_path: Input image or directory.
# 2) socketid: The socket id of the connection.
# 4) result_path: Directory accessible by web.
#    It should be full path in case of a single file, else the directory path.
# NOTE:
# 1) Its job is to find the person of importance in a given image.
# 2) ignore_result=True signifies that celery won't pass any result to the backend.
# 3) It is important to import all the modules only inside the function.
@app.task(ignore_result=True)
def poiImages(src_path, socketid, result_path):
	#General import
	import glob, time, numpy, os

	#Establishing connection to send results and write messages
	import redis, json
	rs = redis.StrictRedis(host='redis', port=6379)

	#Get the absolute path to poi_files directory
	modelFolder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'poi_files')

	#Pre-req for performLinearRegression function
	from celeryTasks.webTasks.poi_files.svmutil import svm_load_model
	from celeryTasks.webTasks.poi_files.svmutil import svm_predict
	svmModel = svm_load_model(os.path.join(modelFolder, 'poi_linear.model'))

	#Some initialisations
	minSVR = -1.4
	maxSVR = 1.4

	def toFloat(x):
		return float(x)

	def extract_features(imagePath, model_path):
		import cv2
		from cv import CV_HAAR_SCALE_IMAGE
		from math import sqrt

		img = cv2.imread(imagePath, cv2.CV_LOAD_IMAGE_GRAYSCALE)
		sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
		sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
		edge_im = numpy.sqrt(numpy.square(sobelx) + numpy.square(sobely))

		imheight = float(len(img))
		imwidth = float(len(img[0]))

		face_cascade = cv2.CascadeClassifier(model_path)
		faces = face_cascade.detectMultiScale(img, scaleFactor=1.1, 
			minNeighbors=2, minSize=(0, 0), flags = CV_HAAR_SCALE_IMAGE)
		
		total_gradient = 0
		face_features = []
		numFaces = len(faces)
		scaled_faces = []

		for face in faces:
			(faceX, faceY, faceW, faceH) = map(toFloat, face)
			x = faceX / imwidth
			y = faceY / imheight
			w = faceW / imwidth
			h = faceH / imheight
			wickedDistance = sqrt((x-0.5)**2 + (y-0.5)**2)/ max(w,h)
			scale = faceW * faceH / (imwidth * imheight)
			roi = edge_im[faceY:faceY+faceH, faceX:faceX+faceW]
			sharpness = sum(sum(roi))
			face_features.append([wickedDistance, scale, sharpness])
			total_gradient = total_gradient + sharpness
			scaled_faces.append([x, y, w, h])

		for i in range(0, numFaces):
			face_features[i][2] = face_features[i][2] / total_gradient
		
		return scaled_faces, face_features

	def performLinearRegression(test_feature):
		(val, x, y) = svm_predict([1], [test_feature.tolist()], svmModel, '-q')
		return val[0]

	def rankPeopleLinear(face_features):
		numPeople = len(face_features)
		input_list = range(0, numPeople)
		for i in range(0, numPeople):
			input_list[i] = performLinearRegression(face_features[i])
		return input_list

	def findRelativeImportance(imagePath):
		#The defaul haarcascade used for face detection
		model_path = os.path.join(modelFolder, 'haarcascade_frontalface_alt.xml')

		#Processing
		[faces, face_features] = extract_features(imagePath, model_path)
		scores = rankPeopleLinear(numpy.array(face_features))
		normScores = []
		for x in scores:
			x = round((x-minSVR)/maxSVR, 2)*100
			if x < 0:
				x = 0.0
			if x > 100:
				x = 100.0
			normScores.append(x)
		sorted_tuple = sorted(enumerate(normScores), key=lambda x:x[1], reverse=True)
		ranked_faces = []
		for r in sorted_tuple:
			faces[r[0]].append(r[1])
			ranked_faces.append(faces[r[0]])

		# Return top 5 faces
		ranked_faces = ranked_faces[:5]
		return ranked_faces

	try:
		if os.path.isdir(src_path):
			for input_file in glob.glob(os.path.join(src_path, '*')):
				if os.path.isfile(input_file):
					#Processing file message
					rs.publish('chat', json.dumps({'message': 'Processing '+os.path.basename(input_file), 'socketid': str(socketid)}))

					#Send for processing
					start = time.time()
					tags = findRelativeImportance(input_file)
					timeMsg = "Completed in %.2f s." % (time.time() - start)
					rs.publish('chat', json.dumps({'message': timeMsg, 'socketid': str(socketid)}))
					
					#Publish result
					webResult = {}
					webResult[os.path.join(result_path, os.path.basename(input_file))] = tags
					rs.publish('chat', json.dumps({'web_result': json.dumps(webResult), 'socketid': str(socketid)}))

		else:
			input_file = src_path

			#Processing file message
			rs.publish('chat', json.dumps({'message': 'Processing '+os.path.basename(input_file), 'socketid': str(socketid)}))

			#Send for processing
			start = time.time()
			tags = findRelativeImportance(input_file)
			timeMsg = "Completed in %.2f s." % (time.time() - start)
			rs.publish('chat', json.dumps({'message': timeMsg, 'socketid': str(socketid)}))

			#Publish result
			webResult = {}
			webResult[result_path] = tags
			rs.publish('chat', json.dumps({'web_result': json.dumps(webResult), 'socketid': str(socketid)}))

		rs.publish('chat', json.dumps({'message': 'Thank you for using CloudCV', 'socketid': str(socketid)}))

	except Exception as e:
		#In case of an error, send the whole error with traceback
		import traceback
		rs.publish('chat', json.dumps({'message': str(traceback.format_exc()), 'socketid': str(socketid)}))
