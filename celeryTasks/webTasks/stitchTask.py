from __future__ import absolute_import
from celeryTasks.celery import app
    
# The function takes as input:
# 1) src_path: Input directory.
# 2) socketid: The socket id of the connection.
# 3) output_path: The directory where to store the result stitch image.
# 4) result_path: Directory accessible by web.
#    It should be full path in case to the result_stitch image.
# NOTE:
# 1) Its job is to stitch images.
# 2) ignore_result=True signifies that celery won't pass any result to the backend.
# 3) It is important to import all the modules only inside the function.
@app.task(ignore_result=True)
def stitchImages(src_path, socketid, output_path, result_path):
    
    #Establishing connection to send results and write messages
    import redis, json
    rs = redis.StrictRedis(host='redis', port=6379)

    try:
        import os, time

        #Execute the stitch_full executable
        src_path = os.path.join(src_path, '')
        output_path = os.path.join(output_path, '')
        start = time.time()
        cmd = './stitch_full '+'--img '+src_path+'--verbose 1 --output '+output_path
        os.system(cmd)
        timeMsg = "Completed in %.2f s." % (time.time() - start)
        rs.publish('chat', json.dumps({'message': timeMsg, 'socketid': str(socketid)}))


        #Publish result and say thank you
        rs.publish('chat', json.dumps({'web_result': result_path, 'socketid': str(socketid)}))
        rs.publish('chat', json.dumps({'message': 'Thank you for using CloudCV', 'socketid': str(socketid)}))

    except Exception as e:
        #In case of an error, send the whole error with traceback
        import traceback
        rs.publish('chat', json.dumps({'message': str(traceback.format_exc()), 'socketid': str(socketid)}))
