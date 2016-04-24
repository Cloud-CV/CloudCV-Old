# encoding: utf-8
from django.views.generic import CreateView
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from cloudcv17 import config
from .response import JSONResponse, response_mimetype
from .serialize import serialize
from app.models import Picture, RequestLog
from celeryTasks.webTasks.stitchTask import stitchImages
from log import log_to_terminal, log_and_exit
from app.core.job import Job
from savefile import saveFilesAndProcess
import app.thirdparty.dropbox_auth as dbauth
import app.thirdparty.google_auth as gauth
import app.conf as conf

from PIL import Image
from querystring_parser import parser

import time
import subprocess
import os
import json
import traceback
import uuid
import datetime
import shortuuid
import redis

r = redis.StrictRedis(host=config.REDIS_HOST, port=6379, db=0)


class Request:
    socketid = None

    def run_executable(self, src_path, output_path, result_path):
        stitchImages.delay(src_path, self.socketid, output_path, result_path)

    def log_to_terminal(self, message):
        r.publish('chat', json.dumps({'message': str(message), 'socketid': str(self.socketid)}))


class PictureCreateView(CreateView):
    model = Picture

    def form_valid(self, form):
        try:
            request_obj = Request()

            request_obj.socketid = self.request.POST['socketid-hidden']
            self.object = form.save()
            serialize(self.object)
            data = {'files': []}

            old_save_dir = os.path.dirname(conf.PIC_DIR)

            folder_name = str(shortuuid.uuid())
            save_dir = os.path.join(conf.PIC_DIR, folder_name)

            # Make the new directory based on time
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                os.makedirs(os.path.join(save_dir, 'results'))

            all_files = self.request.FILES.getlist('file')

            for file in all_files:
                log_to_terminal(str('Saving file:' + file.name), request_obj.socketid)
                a = Picture()
                tick = time.time()
                strtick = str(tick).replace('.', '_')
                fileName, fileExtension = os.path.splitext(file.name)
                file.name = fileName + strtick + fileExtension
                a.file.save(file.name, file)

                file.name = a.file.name

                # imgstr = base64.b64encode(file.read())
                # img_file = Image.open(BytesIO(base64.b64decode(imgstr)))
                # img_file.thumbnail(size, Image.ANTIALIAS)
                imgfile = Image.open(os.path.join(old_save_dir, file.name))
                size = (500, 500)
                imgfile.thumbnail(size, Image.ANTIALIAS)

                imgfile.save(os.path.join(save_dir, file.name))
                thumbPath = os.path.join(folder_name, file.name)
                data['files'].append({
                    'url': conf.PIC_URL + thumbPath,
                    'name': file.name,
                    'type': 'image/png',
                    'thumbnailUrl': conf.PIC_URL + thumbPath,
                    'size': 0,
                })

            request_obj.run_executable(save_dir, os.path.join(save_dir, 'results/'),
                                       os.path.join(conf.PIC_URL, folder_name, 'results/result_stitch.jpg'))

            response = JSONResponse(data, mimetype=response_mimetype(self.request))
            response['Content-Disposition'] = 'inline; filename=files.json'

            return response
        except:
            r.publish('chat', json.dumps({'message': str(traceback.format_exc()), 'socketid': str(self.socketid)}))


class BasicPlusVersionCreateView(PictureCreateView):
    template_name_suffix = '_basicplus_form'


def homepage(request):
    return render(request, 'index.html')


def ec2(request):
    token = request.GET['dropbox_token']
    emailid = request.GET['emailid']

    dirname = str(uuid.uuid4())
    result_path = '/home/cloudcv/detection_executable/detection_output/' + dirname + '/'

    list = ['starcluster', 'sshmaster', 'demoCluster',
            'cd /home/cloudcv/detection_executable/PascalImagenetDetector/distrib; '
            'mkdir ' + result_path + ';' +
            'qsub run_one_category.sh ' + result_path]

    popen = subprocess.Popen(list, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    complete_output = ''
    count = 0
    errline = ''
    line = ''

    while popen.poll() is None:
        if popen.stdout:
            line = popen.stdout.readline()
            popen.stdout.flush()

        if popen.stderr:
            errline = popen.stdout.readline()
            popen.stderr.flush()

        if line:
            print count, line, '\n'
            complete_output += str(line)
            count += 1

        if errline:
            print count, errline, '\n'
            complete_output += str(errline)
            count += 1

    complete_output += result_path
    list = ['starcluster', 'sshmaster', 'demoCluster',
            'cd /home/cloudcv/detection_executable/PascalImagenetDetector/distrib; '
            'python sendJobs1.py ' + token + ' ' + emailid + ' ' + result_path + ' ' + dirname + ';']
    popen = subprocess.Popen(list, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    popen.communicate()
    return HttpResponse(complete_output)


@csrf_exempt
def demoUpload(request, executable):
    try:
        if request.method == 'POST':

            request_obj = Request()

            if 'socketid-hidden' in request.POST:
                request_obj.socketid = request.POST['socketid-hidden']

            print request_obj.socketid
            data = []
            save_dir = os.path.join(conf.LOCAL_DEMO1_PIC_DIR)

            request_obj.log_to_terminal(str('Images Processed. Starting Executable'))
            request_obj.run_executable(save_dir, os.path.join(save_dir, 'results/'),
                                       '/app/media/pictures/demo1/results/result_stitch.jpg')

            data.append({'text': str('')})
            data.append({'result': '/app/media/pictures/demo/output/result_stitch.jpg'})
            response = JSONResponse(data, {}, response_mimetype(request))
            response['Content-Disposition'] = 'inline; filename=files.json'
            return response

    except Exception as e:
        return HttpResponse(str(e))

    return HttpResponse('Not a post request')


def log_every_request(job_obj):
    try:
        now = datetime.datetime.utcnow()
        req_obj = RequestLog(cloudcvid=job_obj.userid, noOfImg=job_obj.count,
                             isDropbox=job_obj.isDropbox(), apiName=None,
                             function=job_obj.executable, dateTime=now)
        req_obj.save()
    except:
        r = redis.StrictRedis(host=config.REDIS_HOST, port=6379, db=0)
        r.publish('chat', json.dumps({'error': str(traceback.format_exc()), 'socketid': job_obj.socketid}))


@csrf_exempt
def pass1(request):
    try:
        data = {'success': 'false'}
        if request.method == 'POST':
            post_dict = parser.parse(request.POST.urlencode())
            print post_dict
            if post_dict['pass'] == 'Passphrase#123!':
                data = {'success': 'true'}
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response
    except:
        # print str(traceback.format_exc())
        data['error'] = 'Error'
        response = JSONResponse(data, {}, response_mimetype(request))
        return response


@csrf_exempt
def matlabReadRequest(request):
    redis.StrictRedis(host=config.REDIS_HOST, port=6379, db=0)

    if request.method == 'POST':
        post_dict = parser.parse(request.POST.urlencode())

        try:
            job_obj = Job(params_obj=post_dict)
            log_to_terminal('Server: Post Request Recieved', job_obj.socketid)
            response = saveFilesAndProcess(request, job_obj)

        except:
            log_and_exit(str(traceback.format_exc()), job_obj.socketid)
            return HttpResponse('Error at server side')

        return HttpResponse(str(response))

    else:
        response = JSONResponse({}, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response


def authenticate(request, auth_name):
    if auth_name == 'dropbox':
        is_API = 'type' in request.GET and request.GET['type'] == 'api'
        contains_UUID = 'userid' in request.GET

        str_response = dbauth.handleAuth(request, is_API, contains_UUID)

        # if the call comes from Matlab or Python API, send the obtained JSON string
        if is_API:
            return HttpResponse(str_response)

        # else if it comes from browser - redirect the browser
        else:
            return HttpResponseRedirect(str_response)

    if auth_name == 'google':
        is_API = 'type' in request.GET and request.GET['type'] == 'api'
        contains_UUID = 'userid' in request.GET

        str_response = gauth.handleAuth(request, is_API, contains_UUID)

        # if the call comes from Matlab or Python API, send the obtained JSON string
        if is_API:
            return HttpResponse(str_response)

        # else if it comes from browser - redirect the browser
        else:
            return HttpResponseRedirect(str_response)

    # Invalid URL if its not one of the above authentication system
    return HttpResponse('Invalid URL')


@csrf_exempt
def callback(request, auth_name):
    if auth_name == 'dropbox':
        post_dict = parser.parse(request.POST.urlencode())
        code = str(post_dict['code'])
        userid = str(post_dict['userid'])
        json_response = dbauth.handleCallback(userid, code, request)
        return HttpResponse(json_response)

    if auth_name == 'google':
        post_dict = parser.parse(request.POST.urlencode())
        code = str(post_dict['code'])
        json_response = gauth.handleCallback(code, request)
        return HttpResponse(json_response)

    return HttpResponse('Invalid URL')
