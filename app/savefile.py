from django.http import HttpResponse

from app.models import Picture
from celeryTasks.apiTasks.tasks import saveDropboxFiles
from app.log import log, logger, log_to_terminal, log_error_to_terminal
from cloudcv17 import config

import app.core.execute as core_execute
import app.thirdparty.ccv_dropbox as ccvdb
import app.conf as conf

from PIL import Image
from io import BytesIO

import time
import os
import traceback
import json
import sys
import redis
import base64
import re

r = redis.StrictRedis(host=config.REDIS_HOST, port=6379, db=0)

''' Not using getThumbnail code anymore
def getThumbnail(image_url_prefix, name):
    #image_url_prefix = /media/pictures/
    im = Image.open('/var/www/html/cloudcv/fileupload' + image_url_prefix + name)
    size = 128, 128
    im.thumbnail(size, Image.ANTIALIAS)
    list = name.split('.')
    file = image_url_prefix + 'thumbnails/' + name
    im.save('/var/www/html/cloudcv/fileupload' + file, list[1])
    return file
'''


def parseParameters(params):
    params = str(params)
    log(params, parseParameters.__name__)
    pat = re.compile('u\'[\w\s,]*\'')
    decoded_params = ''
    end = 0
    for i in pat.finditer(str(params)):
        decoded_params = decoded_params + params[end:i.start()] + '"' + params[i.start()+2:i.end()-1]+'"'
        end = i.end()
    decoded_params += params[end:]
    log(decoded_params, parseParameters.__name__)
    dict = json.loads(decoded_params)
    return dict


def resizeImageAndTransfer(path, directory, size, file):
    try:
        tick = time.time()
        print file.name
        strtick = str(tick).replace('.','_')
        fileName, fileExtension = os.path.splitext(file.name)
        imgstr = base64.b64encode(file.read())
        img_file = Image.open(BytesIO(base64.b64decode(imgstr)))
        img_file.thumbnail(size, Image.ANTIALIAS)
    except Exception as e:
        raise e
    if not os.path.exists(directory):
        os.makedirs(directory)
        os.chmod(directory, 0776)
    img_file.save(os.path.join(directory, file.name))
    

def getFilesFromRequest(request, count):
    files_all = request.FILES.getlist('file')
    if len(files_all) == 0:
        files_all = []
        for key in request.FILES.keys():
            files_all.append(request.FILES[key])
    return files_all


def saveFilesAndProcess(request, job_obj):
    """
        TODO: Specify four types of location
        1.) CloudCV General Dataset
        2.) CloudCV me folder, me folder represents the user folder
        3.) Dropbox folder
        4.) Local System - Either save it as a test and delete, or permanently by specifying a name
    """
    #  If the server is different. The storage path needs to be changed to shared folders.
    parsed_params = parseParameters(job_obj.params)

    if 'server' in parsed_params and parsed_params['server'] == 'decaf_server':
            job_obj.storage_path = '/srv/share/cloudcv/jobs/' + job_obj.userid + '/'

            if not os.path.exists(job_obj.storage_path):
                   os.mkdir(job_obj.storage_path)
                   os.chmod(job_obj.storage_path, 0775)

            job_obj.url = 'http://godel.ece.vt.edu/cloudcv/fileupload/media/pictures/decaf_server/'+ job_obj.userid + \
                          '/' + job_obj.jobid

            r.publish('chat', json.dumps({'error': str('Special Server Identified'), 'socketid': job_obj.socketid}))

    #    Save files either through dropbox or client local system for use an throw scenario
    if job_obj.dropbox_path is not None:
        result = saveDropboxFiles.delay(job_obj.__dict__)
        return 'Downloading content from dropbox. Execution will begin after downloading finishes'

    else:
        files_all = getFilesFromRequest(request, job_obj.count)

        if len(files_all) == 0:
            return 'Length of files = 0'

        if len(files_all) > 50:
            r.publish('chat', json.dumps({'error': str('Shutting down now.'),
                                          'socketid':job_obj.socketid, 'end': 'yes'}))

            return 'Length of files higher than the limit of 50. Please use dropbox'

        job_directory = os.path.join(job_obj.storage_path, str(job_obj.jobid))

        log_to_terminal('Processing files', job_obj.socketid)

        for single_file in files_all:
            try:
                # new_file_name = saveInPictureDatabase(single_file)
                path = conf.PIC_DIR
                size = (500, 500)
                resizeImageAndTransfer(path, job_directory, size, single_file)
            except Exception as e:
                raise e
        response = core_execute.execute(job_obj, job_directory, 'local')
        return response
