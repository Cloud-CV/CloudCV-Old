
from django.http import HttpResponse

from fileupload.models import Picture
from PIL import Image

import time
import subprocess
import json
import os


def run_executable(list, fi):
    try:
        fi.write(str(list))
        popen = subprocess.Popen(list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, errdata) = popen.communicate()
        fi.write("Successfully started execution")

        if popen.returncode is None:
            output = "Error! Signal: Not Terminated" + str(errdata)
        else:
            output = str(output) + 'Signal:' + str(popen.returncode)

    except Exception as e:
        output = "Exception Caught!!" + str(e)
        fi.write('exception caught' + str(e))
    return output, '\n'


def getThumbnail(image_url_prefix, name):
    im = Image.open('/var/www/html/cloudcv/fileupload' + image_url_prefix + name)
    size = 128, 128
    im.thumbnail(size, Image.ANTIALIAS)
    file = image_url_prefix + 'thumbnails/' + name[:-3] + 'jpg'
    im.save('/var/www/html/cloudcv/fileupload' + file, "JPEG")
    return file


def saveInPictureDatabase(file, log):
    try:
        pic = Picture()
        tick = time.time()

        strtick = str(tick).replace('.', '_')

        log.write('S', str(file.name))

        format = file.name[-4:]
        name = file.name[:-4]
        new_name = name + strtick + format

        pic.file.save(new_name, file)

        return new_name

    except Exception as e:
        log.write('E', str('Error while saving to Picture Database'))
        raise e


def resizeImageAndTransfer(path, name, directory, size, oldname):
    img_file = Image.open(path + name.replace(" ", "_"))
    img_file.thumbnail(size, Image.ANTIALIAS)

    if not os.path.exists(directory):
        os.makedirs(directory)
        os.chmod(directory, 0776)
    img_file.save(directory + '/' + oldname)


def saveFilesAndProcess(request, param_obj, log):
    data = []
    log.write('S', str(request.FILES))

    files_all = request.FILES.getlist('file')

    if(len(files_all) == 0):
        files_all = []
        for x in range(param_obj._count):
            files_all.append(request.FILES['file' + str(x)])

    if(len(files_all) == 0):
        return 'Length of files = 0'

    tickdir = time.time()

    directory = '/var/www/html/cloudcv/fileupload/media/pictures/' + str(tickdir).replace('.', '_')

    log.write('S', 'Begin Uploading')

    for file in files_all:
        try:
            new_file_name = saveInPictureDatabase(file, log)
            log.write('S', str(new_file_name))

            image_url_prefix = '/media/pictures/'

            path = '/var/www/html/cloudcv/fileupload/media/pictures/'
            size = (500, 500)
            resizeImageAndTransfer(path, new_file_name, directory, size, file.name)

            getThumbnail(image_url_prefix, new_file_name)

            # data.append({'name': file.name,
            # 'url': 'fileupload'+settings.MEDIA_URL + "pictures/" + new_file_name,                'thumbnail_url': 'fileupload'+thumbnail_url,
            # 'delete_type': "DELETE"})

        except Exception as e:
            log.write('S', 'Error in loop' + str(e))
            response = JSONResponse(data, {}, response_mimetype(request))
            response['Content-Disposition'] = 'inline; filename=files.json'
            return response
    try:
        list1 = ['/var/www/html/cloudcv/fileupload/run_executable.py']
        list1.append(str(directory))
        list1.extend(param_obj.getListOfParameters())
        list1.append('http://godel.ece.vt.edu/cloudcv/fileupload/media/pictures/' + str(tickdir).replace('.', '_'))
        subprocess.Popen(list1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    except Exception as e:
        log.write('S', str(e))

    result = 'new process spawned'
    log.write('S', str(result))

    data.append(result)

    log.write('S', str(data))

    response = None

    try:
        response = JSONResponse(data, {}, "application/json")
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

    except Exception as e:
        log.write('S', str(e))
        return response


def response_mimetype(request):
    if "application/json" in request.META['HTTP_ACCEPT']:
        return "application/json"
    else:
        return "text/plain"


class JSONResponse(HttpResponse):
    """JSON response class."""

    def __init__(self, obj='', json_opts={}, mimetype="application/json", *args, **kwargs):
        content = json.dumps(obj, **json_opts)
        super(JSONResponse, self).__init__(content, mimetype, *args, **kwargs)
