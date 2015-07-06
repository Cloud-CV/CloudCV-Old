from __future__ import absolute_import
from celeryTasks.celery import app


# The function takes as input:
# 1) src_path: Input image or directory.
# 2) socketid: The socket id of the connection.
# 3) output_path: Directory where the mat files are to be stored.
# 4) result_path: Directory accessible by web.

# NOTE:
# 1) Its job is to find the decaf features of images according to the pre-trained model.
# 2) ignore_result=True signifies that celery won't pass any result to the backend.
# 3) It is important to import all the modules only inside the function
# 4) When running with new version of caffe do np.load(MEAN_FILE).mean(1).mean(1)
@app.task(ignore_result=True)
def poiImages(image_path, socketid):
	#Establishing connection to send results and write messages
	import redis, json
	rs = redis.StrictRedis(host='redis', port=6379)

	try:
		pass
	except Exception as e:
		#In case of an error, send the whole error with traceback
		import traceback
		rs.publish('chat', json.dumps({'message': str(traceback.format_exc()), 'socketid': str(socketid)}))
