import time
import subprocess
import os

from django.http import HttpResponse
from django.utils import simplejson
import shortuuid
from PIL import Image

from fileupload.models import Picture
import thirdparty.ccv_dropbox as ccvdb
from log import logger
from core.job import Job


""" OLD CODE. REMOVE LATER

def run_executable(list, fi):
    try:
        fi.write(str(list))
        popen = subprocess.Popen(list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, errdata) = popen.communicate()
        fi.write("Successfully started execution")

 
        if(popen.returncode==None):
            output="Error! Signal: Not Terminated"+str(errdata)
        else:
            output=str(output)+ 'Signal:' +str(popen.returncode)

    except Exception as e:
        output="Exception Caught!!"+str(e)
        fi.write('exception caught'+str(e))
    
    return output,'\n'
"""

def getThumbnail(image_url_prefix, name):
    im = Image.open('/var/www/html/cloudcv/fileupload' + image_url_prefix + name)
    size = 128, 128
    im.thumbnail(size, Image.ANTIALIAS)
    file = image_url_prefix + 'thumbnails/' + name[:-3]+'jpg'
    im.save('/var/www/html/cloudcv/fileupload' + file, "JPEG")
    return file


def saveInPictureDatabase(file):
    try:
        pic = Picture()
        tick = time.time()
        
        strtick = str(tick).replace('.','_')

        logger.write('S', str(file.name))
        
        format = file.name[-4:]
        name = file.name[:-4]
        new_name = name + strtick + format
        
        pic.file.save(new_name, file)
        
        return new_name

    except Exception as e:
        logger.write('E', str('Error while saving to Picture Database'))
        raise e

def resizeImageAndTransfer(path, name, directory, size, oldname):
    img_file = Image.open(path + name.replace(" ","_"))
    img_file.thumbnail(size, Image.ANTIALIAS)
    
    if not os.path.exists(directory):
        os.makedirs(directory)
        os.chmod(directory, 0776)
    img_file.save(directory + '/' + oldname)
    

def getFilesFromRequest(files, count):
    files_all = files.getlist('file')
    if len(files_all) == 0:
        files_all = []
        for x in range(count):
            files_all.append(files.FILES['file' + str(x)])
    return files_all


def execute(job_obj):
    directory = job_obj.storage_path + str(job_obj.jobid)

    # Run an executable as defined by the user
    try:
        list1 = ['/var/www/html/cloudcv/fileupload/run_executable.py', '-d', str(directory),
                 '-u', 'http://godel.ece.vt.edu/cloudcv/fileupload/media/pictures/' + job_obj.userid + '/' + job_obj.jobid]
        list1.extend(job_obj.getListOfParameters())
        subprocess.Popen(list1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        logger.write('S', str(e))

    result = 'new process spawned'
    data = [result]
    logger.write('S', str(data))

    try:
        response = JSONResponse(data, {}, "application/json")
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

    except Exception as e:
        logger.write('S',str(e))
        return ''


def saveFilesAndProcess(request, job_obj):

    """
        TODO: Specify four types of location
        1.) CloudCV General Dataset
        2.) CloudCV me folder, me folder represents the user folder
        3.) Dropbox folder
        4.) Local System - Either save it as a test and delete, or permanently by specifying a name
    """

    # Save files either through dropbox or client local system for use an throw scenario
    if job_obj.dropbox_path is not None:
        ccvdb.dbscheduler.pushToIdealQueue(job_obj.__dict__)
        return job_obj.__dict__
    else:
        files_all = getFilesFromRequest(request.FILES, job_obj.count)
        if len(files_all) == 0:
            return 'Length of files = 0'

        tickdir = time.time()
        directory = job_obj.storage_path + str(job_obj.jobid)

        logger.write('S', 'Begin Uploading')

        for single_file in files_all:
            try:
                new_file_name = saveInPictureDatabase(single_file, logger)
                logger.write('S', str(new_file_name))

                image_url_prefix = '/media/pictures/'

                path = '/var/www/html/cloudcv/fileupload/media/pictures/'
                size = (500, 500)
                resizeImageAndTransfer(path, new_file_name, directory, size, single_file.name)

                thumbnail_url = getThumbnail(image_url_prefix, new_file_name)

            except Exception as e:
                logger.write('S', 'Error in loop'+str(e))
                response = JSONResponse([], {}, response_mimetype(request))
                response['Content-Disposition'] = 'inline; filename=files.json'
                return response

        execute(job_obj)


def response_mimetype(request):
    if "application/json" in request.META['HTTP_ACCEPT']:
        return "application/json"
    else:
        return "text/plain"

class JSONResponse(HttpResponse):
    """JSON response class."""
    def __init__(self,obj='', json_opts={},mimetype="application/json",*args,**kwargs):
        content = simplejson.dumps(obj,**json_opts)
        super(JSONResponse, self).__init__(content,mimetype,*args,**kwargs)


