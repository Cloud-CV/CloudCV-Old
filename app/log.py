from django.conf import settings

from time import gmtime, strftime
from cloudcv17 import config

import redis
import os
import json


class Logger:

    log_path = os.path.join(settings.BASE_ABS_DIR, 'logs')

    def __init__(self):
        print self.log_path

    def open(self, choice, type='w'):
        if(choice == 'S'):
            self._fi_server = open(os.path.join(
                self.log_path, 'log_server.txt'), type)
        if(choice == 'E'):
            self._fi_exec = open(os.path.join(
                self.log_path, 'log_error.txt'), type)
        if(choice == 'R'):
            self._fi_run = open(os.path.join(
                self.log_path, 'log_run.txt'), type)
        if(choice == 'P'):
            self._fi_process = open(os.path.join(
                self.log_path, 'log_process.txt'), type)

    def getData(self):
        return str(strftime("%Y-%m-%d %H:%M:%S", gmtime())) + ' : '

    def write_opening(self):
        self._fi_server.write(self.getData() + '_______________________\n')
        self._fi_exec.write(self.getData() + '________________________\n')

    def write(self, type, msg):
        if(type == 'S'):
            self._fi_server.write(self.getData() + str(msg) + '\n')
        if(type == 'E'):
            self._fi_exec.write(self.getData() + str(msg) + '\n')
        if(type == 'R'):
            self._fi_run.write(self.getData() + str(msg) + '\n')
        if(type == 'P'):
            self._fi_process.write(self.getData() + str(msg) + '\n')

    def close(self, type):
        if(type == 'S'):
            self._fi_server.close()
        if(type == 'E'):
            self._fi_exec.close()
        if(type == 'R'):
            self._fi_run.close()
        if(type == 'P'):
            self._fi_process.close()

logger = Logger()

r = redis.StrictRedis(host=config.REDIS_HOST, port=6379, db=0)


def log(message, name):
    r.lpush('message', str(name) + '  :  ' + str(message))


def log_to_terminal(message, socketid):
    r.publish('chat', json.dumps(
        {'message': str(message), 'socketid': str(socketid)}))


def log_and_exit(message, socketid):
    r.publish('chat', json.dumps(
        {'exit': str(message), 'socketid': str(socketid)}))


def log_error_to_terminal(message, socketid, end):

    if(end):
        r.publish('chat', json.dumps(
            {'error': message, 'socketid': socketid, 'end': 'yes'}))
    else:
        r.publish('chat', json.dumps({'error': message, 'socketid': socketid}))
