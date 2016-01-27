# from SocketServer import ThreadingMixIn
# import sys
# import threading

# path = '/var/www/html/cloudcv/fileupload'
# if path not in sys.path:
#     sys.path.append(path)

# import time
# import json
# import shortuuid
# import redis

# from cloudcvWorker import cvWorker


# max_mlabs = 3
# mlab_path = '/usr/local/MATLAB/R2013a/bin/matlab'

# socket_prefix = 'ipc:///tmp/cloudCVport'
# mlab_id_prefix = 'cloudcv-'

# ## THIS SHOULD GO.
# exec_path = '/cloudcv/SUN_py/code/scene_sun/extractFeatPy.m'

# # Global Variable to Maintain a list of all the workers.
# worker_list = []

# redis_pymat = redis.Redis()
# redis_pymat.set('cloudcv:stop', 'False')
# redis_pymat.delete('cloudcv:tasks')

# class Tasks:
#     def __init__(self, job_args):
#         json_args = json.dumps(job_args)
#         print job_args
#         #Push Unique Hash Name into a List, And create that hash
#         redis_pymat.rpush('cloudcv_jobs', json_args)
#         ###redis_pymat.hmset(self.prefix + job_id, {'job_id': self.jobid, 'job_args': json_args})

# class MasterScheduler(threading.Thread):
#     def __init__(self):
#         threading.Thread.__init__(self)
#         redis_pymat.set('cloudcv_all_workers_stop', 'False')

#     def run(self):
#         self.deploy_workers()

#     def deploy_workers(self):
#         redis_pymat.set('cloudcv_all_workers_stop', 'False')

#         for x in xrange(max_mlabs):
#             worker_id = 'ccvworker__' + str(shortuuid.uuid())
#             worker = cvWorker(worker_id, mlab_path, socket_prefix, mlab_id_prefix)
#             worker.start()
#             worker_list.append(worker)
#             # Log all worker ids for cleanup purposes
#             redis_pymat.rpush('cloudcv_workers', worker_id)
#             print 'Started worker number ' + str(x)

#         #Keep Listening for Stop Signal on Redis
#         while True:
#             if redis_pymat.get('cloudcv_all_workers_stop') == 'True':
#                 self.stop_workers()
#                 break
#             # Change this Value to 1 minute in production
#             time.sleep(10)
#         redis_pymat.set('cloudcv_all_workers_stop', 'False')

#     def stop_workers(self):
#         redis_pymat.set('cloudcv:stop','True')
#         print 'Stop command issued'
#         for w in worker_list:
#             w.join()
#         print 'Workers terminated'

#     def cleanup_redis(self):
#         # Cleanup code to remove all scheduler related entries
#         redis_pymat.delete('cloudcv:stop')

#         worker_id_list = redis_pymat.lrange('cloudcv_workers',0,-1)
#         for w in worker_id_list:
#             redis_pymat.delete('cloudcv:'+w+':status')
#         redis_pymat.delete('cloudcv:workers')
#         print 'Cleaned up Redis'

# '''
# def test_workers():
#     # Launch jobs for testing purpose
#     task_prefix = 'task'
#     for x in xrange(max_mlabs):
#         task_id = task_prefix + str(x)
#         task_args = {'imagePath': '/cloudcv/share/clint_pymat/testin', 'outputPath': '/cloudcv/share/clint_pymat/testout' + str(x), 'featList': 'lbp', 'verbosity': '2' }
#         json_args = json.dumps(task_args)

#         redis_pymat.set('cloudcv:'+task_id+':args', json_args)
#         redis_pymat.set('cloudcv:'+task_id+':exec', exec_path)

#         redis_pymat.rpush('cloudcv:tasks', task_id)
#         redis_pymat.rpush('cloudcv:taskhistory', task_id)
#     print 'Test jobs pushed into queue'
# '''
# #ms = MasterScheduler()
# #ms.deploy_workers()

# '''
# #For testing purposes
# # Function to run the module
# if __name__ == "__main__":
#     print 'Testing modules...'
#     test_workers()
# '''
