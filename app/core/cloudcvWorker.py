import time
import threading
import json

import redis

from pymatbridge import Matlab
import run_executables as re



# mlab_path = '/usr/local/MATLAB/R2013a/bin/matlab' - mlab_path should be passed in as argument to thread
# socket_prefix = 'ipc:///tmp/cloudCVport' - socket_prefix should be passed in as argument to thread
# id_prefix = 'cloudcv-pymat' id_prefix should be passed in as argument to thread

class cvWorker (threading.Thread):

    def __init__(self, worker_id, mlab_path, socket_prefix, id_prefix):
        threading.Thread.__init__(self)
        self.redis_obj = redis.Redis()
        self.worker_id = worker_id

        #Create a matlab instance; ie one matlab instance is created per worker
        cv_socket = socket_prefix + worker_id
        mlab_id = id_prefix + worker_id
        self.mlab_inst = Matlab(matlab=mlab_path, socket_addr=cv_socket, id=mlab_id)
        self.mlab_inst.start()

        time.sleep(2)
        self.createHash()

    def createHash(self):
        self.redis_obj.hmset('cloudcv_worker:'+self.worker_id, {'status' : 'Started'})

    def run(self):
        # Keep polling the redis queue for jobs
        # If present, execute it else keep polling till instructed to stop
        loop = 1
        self.redis_obj.rpush('cloudcv:'+self.worker_id+':status', 'Running')

        while loop == 1:
            json_args = self.redis_obj.lpop('cloudcv_jobs')
            if json_args is not None:
                parsed_dict = json.loads(json_args)
                re.run(parsed_dict, self.mlab_inst)
                print json_args
            

            '''
            if task_id is not None:
                # Set status to "Executing Job<ID> @ Time" and execute the task
                json_args = self.redis_obj.get('cloudcv:'+task_id+':args')
                exec_path = self.redis_obj.get('cloudcv:'+task_id+':exec')
                ## HAVE TO CLEAN UP REDIS AFTER THIS
                task_args = json.loads(json_args)
                #task_args = {'imagePath': '/home/mclint/pythonbridge/testin','outputPath': '/home/mclint/pythonbridge/testout','featList': 'lbp','verbosity': '2' }
                ## HAVE TO ADD TIME
                time_str = time.asctime(time.localtime(time.time()))
                self.redis_obj.rpush('cloudcv:'+self.worker_id+':status', 'Executing Job: ' + task_id + ' at ' + time_str)
                self.redis_obj.set('cloudcv:'+task_id+':status', 'Executing on Worker: ' + self.worker_id + ' at ' + time_str)

                res = self.mlab_inst.run_func(exec_path, task_args)
                print res

                self.redis_obj.set('cloudcv:'+task_id+':result', res)
                ## HAVE TO ADD TIME
                time_str = time.asctime(time.localtime(time.time()))
                if res['result'] == 0:
                    # Set status to "Completed Job<ID> @ Time"
                    print task_id + ' Completed Successfully by Worker: ' + self.worker_id + ' at ' + time_str
                    self.redis_obj.set('cloudcv:'+task_id+':status', 'Completed by Worker: ' + self.worker_id + ' at ' + time_str)
                    self.redis_obj.rpush('cloudcv:'+self.worker_id+':status', 'Completed Job: ' + task_id + ' at ' + time_str)
                else:
                    # Set status to "FAILED Job<ID> @ Time"
                    print task_id + ' FAILED - worker: ' + self.worker_id + ' at ' + time_str
                    self.redis_obj.set('cloudcv:'+task_id+':status', 'Job FAILED - Worker: ' + self.worker_id + ' at ' + time_str)
                    self.redis_obj.rpush('cloudcv:'+self.worker_id+':status', 'Job FAILED: ' + task_id + ' at ' + time_str)
            '''
            if self.redis_obj.get('cloudcv:stop') != 'False':
                loop = 0
                self.redis_obj.rpush('cloudcv:'+self.worker_id+':status', 'Stopping Matlab')
                print 'Quit command issued'
            time.sleep(0.1)
        # Go to terminate here
        self.terminate()

    def terminate(self):
        # Stop Matlab instance and set status
        self.mlab_inst.stop()
        self.redis_obj.rpush('cloudcv:'+self.worker_id+':status', 'Stoped Matlab')
        self.redis_obj.rpush('cloudcv:'+self.worker_id+':status', 'Exiting Thread')