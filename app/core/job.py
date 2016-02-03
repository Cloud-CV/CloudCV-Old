__author__ = 'dexter'
import shortuuid
import app.conf as conf
import os

IMAGE_PARENT_PATH = conf.PIC_DIR


class Parameters:
    count = 0
    token = None

    socketid = None

    executable = None
    params = None

    dropbox_path = None
    dropbox_token = None
    userid = None

    def __init__(self, params=None):
        if params is not None:
            self.setListOfParameters(params)

    def setListOfParameters(self, dict):
        if 'dropbox_path' in dict:
            self.dropbox_path = dict['dropbox_path']
            self.dropbox_token = dict['dropbox_token']

        if 'userid' in dict:
            self.userid = dict['userid']
        if 'token' in dict:
            self.token = dict['token']
        if 'socketid' in dict:
            self.socketid = dict['socketid']
        if 'executable' in dict:
            self.executable = dict['executable']
        if 'exec_params' in dict:
            self.params = str(dict['exec_params'])

        if 'count' in dict:
            self.count = dict['count']

    def getListOfParameters(self):
        list = ['-e', self.executable, '-c', str(self.count), '-t', self.token, '-s', self.socketid, '-p', self.params]
        return list


class Job(Parameters):
    jobid = None
    storage_path = None
    url = None

    def __init__(self, params_obj=None):
        if params_obj is not None:
            Parameters.__init__(self, params=params_obj)

        if self.userid is None:
            self.userid = 'anonymous'

        self.createUniqueJobID()

        self.storage_path = os.path.join(IMAGE_PARENT_PATH, str(self.userid))
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def createUniqueJobID(self):
        self.jobid = shortuuid.uuid()

    def getJobID(self):
        if self.jobid is None:
            self.createUniqueJobID()
        return self.jobid

    def getUserPath(self):
        return self.storage_path

    def isDropbox(self):
        if self.dropbox_token is None:
            return False
        return True

    def __str__(self):
        return 'JobID: ' + str(self.jobid) + ', Storage Path: ' + str(self.storage_path) + '\n'
