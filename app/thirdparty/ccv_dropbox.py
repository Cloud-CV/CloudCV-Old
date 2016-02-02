__author__ = 'dexter'
import sys
import os

import sys
path = '/home/ubuntu/cloudcv/cloudcv17'
sys.path.append(path)

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloudcv17.settings")

from app.log import logger, log, log_to_terminal, log_error_to_terminal, log_and_exit
from app.core.job import Job
from app.core import execute as core_execute

import pickle
import redis
import dropbox
import traceback
import time
import ntpath
import threading
from PIL import Image
from StringIO import StringIO
import shortuuid

def downloadFiles(job_dict):

    log_to_terminal('Dropbox Queue Handler: Downloading images', job_dict['socketid'])

    client = dropbox.client.DropboxClient(job_dict['dropbox_token'])
    try:
        folder_metadata = client.metadata(job_dict['dropbox_path'])
    except Exception as e:
        log_and_exit('Path: ' + job_dict['dropbox_path'] + ' not found', job_dict['socketid'])
        return

    log(job_dict['dropbox_path'], downloadFiles.__name__)
    log(job_dict['dropbox_token'], downloadFiles.__name__)

    for content in folder_metadata['contents']:
        if content['is_dir'] is False and 'image' in str(content['mime_type']):
            file, file_metadata = client.get_file_and_metadata(content['path'])

            rel_path = ntpath.dirname(str(content['path'])).lstrip('/')
            log_to_terminal(os.path.join(job_dict['storage_path'] ,rel_path , ntpath.basename(content['path'])),
                            job_dict['socketid'])

            if not os.path.exists(os.path.join(job_dict['storage_path'], rel_path)):
                os.makedirs(os.path.join(job_dict['storage_path'],  rel_path))
                os.chmod(os.path.join(job_dict['storage_path'] , rel_path), 0775)

            img = Image.open(StringIO(file.read()))
            img.save(os.path.join(job_dict['storage_path'], rel_path,
                                  ntpath.basename(content['path'])),
                                  file_metadata['mime_type'].split('/')[1])


    try:
        job_obj = Job()
        for k,v in job_dict.iteritems():
            setattr(job_obj, k, v)

        log(str(job_dict['storage_path'] + job_dict['dropbox_path'].strip('/')), 'directory')

        if job_obj.count is None or int(job_obj.count) <= 0:
            count = 0
            for name in os.listdir(os.path.join(job_dict['storage_path'], job_dict['dropbox_path'].strip('/'))):
                log(str(name), 'name')
                if os.path.isfile(os.path.join(job_dict['storage_path'], job_dict['dropbox_path'].strip('/'),  name)):
                    count +=1
                    log(str(name), 'name')
            job_obj.count = count

        # log_to_terminal('JobID: ' + str(job_obj.jobid), job_obj.socketid)
        # log_to_terminal('Count: ' + str(job_obj.count), job_obj.socketid)

        core_execute.execute(job_obj, os.path.join(job_dict['storage_path'], job_dict['dropbox_path'].strip('/')), 'dropbox')
    except Exception as e:
        print str(traceback.format_exc())
        log_and_exit(str(traceback.format_exc()), job_dict['socketid'])

'''
# Dropbox Connection Class
class DropboxConnections(threading.Thread):
    is_busy = False
    recursiveMode = False
    SLEEP_TIME = 10
    name = None
    client = None

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.redis_obj = redis.StrictRedis(host = '127.0.0.1', port=6379, db=0)

    def downloadFiles(self, job_dict):

        self.client = dropbox.client.DropboxClient(job_dict['dropbox_token'])
        try:
            folder_metadata = self.client.metadata(job_dict['dropbox_path'])
        except Exception as e:
            log_to_terminal('Path: ' + job_dict['dropbox_path'] + ' not found', job_dict['socketid'])
            return

        log(job_dict['dropbox_path'], self.downloadFiles.__name__)
        log(job_dict['dropbox_token'], self.downloadFiles.__name__)

        for content in folder_metadata['contents']:
            if content['is_dir'] is False and 'image' in str(content['mime_type']):
                file, file_metadata = self.client.get_file_and_metadata(content['path'])

                rel_path = ntpath.dirname(str(content['path'])).lstrip('/')


                if not os.path.exists(os.path.join(job_dict['storage_path'], rel_path)):
                    os.makedirs(os.path.join(job_dict['storage_path'],  rel_path))
                    os.chmod(os.path.join(job_dict['storage_path'] , rel_path), 0776)

                img = Image.open(StringIO(file.read()))
                img.save(os.path.join(job_dict['storage_path'], rel_path,
                                      ntpath.basename(content['path'])),
                                      file_metadata['mime_type'].split('/')[1])



        try:
            job_obj = Job()
            for k,v in job_dict.iteritems():
                setattr(job_obj, k, v)

            log(str(job_dict['storage_path'] + job_dict['dropbox_path'].strip('/')), 'directory')

            if job_obj.count is None or int(job_obj.count) <= 0:
                count = 0
                for name in os.listdir(os.path.join(job_dict['storage_path'], job_dict['dropbox_path'].strip('/'))):
                    log(str(name), 'name')
                    if os.path.isfile(os.path.join(job_dict['storage_path'], job_dict['dropbox_path'].strip('/'),  name)):
                        count +=1
                        log(str(name), 'name')
                job_obj.count = count

            core_execute.execute(job_obj, job_dict['storage_path'] + job_dict['dropbox_path'].strip('/'), 'dropbox')
        except Exception as e:
            self.redis_obj.lpush('message', 'Error ' + str(e))


    def getLastElement(self):
        return self.redis_obj.rpop('thread')

    def isQueueEmpty(self):
        # print self.name, ' queue length: ', int(self.redis_obj.llen('thread')), '\n'
        if int(self.redis_obj.llen('thread')) > 0:
            return False
        return True

    def run(self):
        # print 'Starting', self.name, '\n'

        while True:
            # This code is not synchronised. Race Condition. Fix it later. Not super important.
            try:
                while self.isQueueEmpty():
                    print 'sleeping'
                    time.sleep(5)
                if not self.is_busy:
                    print 'busy'
                    self.is_busy = True
                    name = self.name
                    element = self.getLastElement()
                    element = pickle.loads(element)
                    log({'name':str(name), 'element': element}, self.run.__name__)
                    self.downloadFiles(job_dict=element)
                    time.sleep(2)
                    self.is_busy = False
            except TypeError as te:
                log({'name': self.name, 'error':str(str(traceback.format_exc()))}, self.run.__name__)
            except Exception as e:
                log({'name': self.name, 'error': str(str(traceback.format_exc()))}, self.run.__name__)
        log({'name': 'Ending' + self.name + '\n'})

    def getBusyStatus(self):
        return self.is_busy


class DBConnectionScheduler:
    def __init__(self):
        logger.open('P','a')
        logger.write('P', 'starting scheduler')
        self.queue_length = 5
        self.queue_count = 0
        self.thread_dict = {}
        self.redis_obj = redis.StrictRedis(host = '127.0.0.1', port=6379, db=0)

        for i in range(self.queue_length):
            self.thread_dict[str(i)] = DropboxConnections('thread'+str(i))
            self.thread_dict[str(i)].start()
            logger.write('P', str(i))
        logger.close('P')


def pushToIdealQueue(param_dict):
    try:
        redis_obj = redis.StrictRedis(host = '127.0.0.1', port=6379, db=0)
        logger.open('P','a')
        logger.write('P', 'pushing to queue')
        logger.write('P', 'Dictionary: ' + pickle.dumps(param_dict))
        redis_obj.lpush('thread', pickle.dumps(param_dict))

    except Exception as e:
        log_to_terminal(str(traceback.format_exc()), param_dict['socketid']);
        print str(traceback.format_exc())
        logger.write('P', str(traceback.format_exc()))
    logger.close('P')

#dbscheduler = DBConnectionScheduler()

# Function to run the module
if __name__ == "__main__":
    print 'main'
    dbscheduler = DBConnectionScheduler()
    for i in range(20):
        # print 'Pushing', i, '\n'
        time.sleep(.50)
        dbscheduler.pushToIdealQueue({'number':i, 'jobid': str(shortuuid.uuid())})
'''
