from django.views.generic import CreateView
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from cloudcv17 import config
from .response import JSONResponse, response_mimetype
from .serialize import serialize
from app.models import Picture, RequestLog
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


def homepage(request):
    return render(request, 'index.html')


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
