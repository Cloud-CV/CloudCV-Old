# encoding: utf-8

from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, DeleteView
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .response import JSONResponse, response_mimetype
from .serialize import serialize
from django.conf import settings
from PIL import Image
from io import BytesIO

from app.celery.web_tasks.ImageStitchingTask import runImageStitching
# from app.models import Picture, RequestLog, Decaf
from app.models import *
from app.core.job import Job
from querystring_parser import parser
from log import logger, log, log_to_terminal, log_and_exit
from savefile import saveFilesAndProcess
import app.thirdparty.dropbox_auth as dbauth
import app.thirdparty.google_auth as gauth
# from app.serializers import *

import app.conf as conf
import base64
import redis
import decaf_views
import StringIO
import time
import subprocess
import os
import json
import traceback
import uuid
import datetime
import shortuuid
import mimetypes

r = redis.StrictRedis(host='localhost', port=6379, db=0)

class Request:
    socketid = None

    def run_executable(self, list, result_path):
        """
        Deprecated Image Stitching code. We dont want to loose it. So, it is commented.
        """
        # try:
        #     popen = subprocess.Popen(list,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #     count=1
        #     print 'Coming Here'
        #     while True:
        #         popen.poll()
        #         if(popen.stdout):
        #             line=popen.stdout.readline()
        #             popen.stdout.flush()
        #
        #         if(popen.stderr):
        #             errline = popen.stderr.readline()
        #             popen.stderr.flush()
        #
        #         if line:
        #             self.log_to_terminal(line)
        #             # fi.write(line+'*!*'+socketid+'\n')
        #             print count,line, '\n'
        #
        #             count += 1
        #                     # time.sleep(1)
        #         if errline:
        #             self.log_to_terminal(errline)
        #             # fi.write(line+'*!*'+socketid+'\n')
        #             print count,line, '\n'
        #             count += 1
        #
        #         if line == '':
        #             break
        #
        #     self.log_to_terminal('Thank you for using CloudCV')
        #     r.publish('chat', json.dumps({'web_result': result_path, 'socketid': str(self.socketid)}))
        # except Exception as e:
        #     self.log_to_terminal(str(traceback.format_exc()))
        #     print str(traceback.format_exc())
        #
        # return '\n', '\n'

        runImageStitching.delay(list, result_path, self.socketid)

    def log_to_terminal(self, message):
        r.publish('chat', json.dumps({'message': str(message), 'socketid': str(self.socketid)}))

def run_executable(list, session, socketid, ):
        try:

            popen=subprocess.Popen(list,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            count=1

            while True:
                popen.poll()
                if(popen.stdout):
                    line=popen.stdout.readline()
                    popen.stdout.flush()

                if(popen.stderr):
                   errline=popen.stdout.readline()
                   popen.stderr.flush()


                if line:
                    r.publish('chat', json.dumps({'message': str(line), 'socketid': str(socketid)}))
                    print count,line, '\n'
                    count += 1

                if errline:
                    r.publish('chat', json.dumps({'message': str(errline), 'socketid': str(socketid)}))
                    print count,line, '\n'
                    count += 1

                if line == '':
                    break
            r.publish('chat', json.dumps({'message': str('Thank you for using CloudCV'), 'socketid': str(socketid)}))

        except Exception as e:
            r.publish('chat', json.dumps({'message': str(traceback.format_exc()), 'socketid': str(socketid)}))
        return '\n', '\n'


class PictureCreateView(CreateView):
    model = Picture

    def form_valid(self, form):
        """
        Method for checking the django form validation and then saving 
        the images after resizing them.  
        """
        try:
            r.publish('chat', json.dumps({'error': str('Entering form-valid'), 'socketid': self.request.POST['socketid-hidden']}))
            request_obj = Request()

            request_obj.socketid = self.request.POST['socketid-hidden']
            self.object = form.save()
            serialize(self.object)
            data = {'files': []}

            # List of Images: Url, Name, Type
            print data

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
                a = Images()
                tick = time.time()
                strtick = str(tick).replace('.','_')
                fileName, fileExtension = os.path.splitext(file.name)
                file.name = fileName + strtick + fileExtension
                a.file.save(file.name, file)


                file.name = a.file.name

                # imgstr = base64.b64encode(file.read())
                # img_file = Image.open(BytesIO(base64.b64decode(imgstr)))
                # img_file.thumbnail(size, Image.ANTIALIAS)
                imgfile = Image.open(os.path.join(old_save_dir, file.name))
                size = (500,500)
                imgfile.thumbnail(size,Image.ANTIALIAS)

                imgfile.save(os.path.join(save_dir, file.name))
                thumbPath = os.path.join(folder_name, file.name)
                data['files'].append({
                    'url': conf.PIC_URL+thumbPath,
                    'name': file.name,
                    'type': 'image/png',
                    'thumbnailUrl': conf.PIC_URL+thumbPath,
                    'size': 0,
                })
            path, dirs, files = os.walk(save_dir).next()
            file_count = len(files)

            list = [os.path.join(conf.EXEC_DIR, 'stitch_full'), '--img', save_dir, '--verbose', '1', '--output',
                    os.path.join(save_dir, 'results/'), ]

            print list
            r.publish('chat', json.dumps({'error': str('Calling run_executable in form_valid'), 'socketid': self.request.POST['socketid-hidden']}))
            request_obj.run_executable(list, os.path.join(conf.PIC_URL, folder_name, 'results/result_stitch.jpg'))

            response = JSONResponse(data, mimetype=response_mimetype(self.request))
            response['Content-Disposition'] = 'inline; filename=files.json'

            r.publish('chat', json.dumps({'error': str('Exiting form-valid before calling response'), 'socketid': self.request.POST['socketid-hidden']}))
            return response
        except Exception as e:
            print traceback.format_exc()
            r.publish('chat', json.dumps({'message': str(traceback.format_exc()), 'socketid': str(self.socketid)}))


class BasicPlusVersionCreateView(PictureCreateView):
    template_name_suffix = '_basicplus_form'

" All Views "
def homepage(request):
    """
    View for home page
    """
    return render(request, 'index.html')

def ec2(request):
    """
    This functionality is deprecated. We need to remove it from the codebase. 
    """
    token = request.GET['dropbox_token']
    emailid = request.GET['emailid']

    dirname = str(uuid.uuid4())
    result_path ='/home/cloudcv/detection_executable/detection_output/' + dirname +'/'

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
    """
    Method called when the image stitching of demo images is done by 
    clicking on the button 'Submit these' at /image-stitch url.   
    """
    try:
        if request.method == 'POST':

            r.publish('chat', json.dumps({'error': str('Entered demoUpload'), 'socketid': self.request.POST['socketid-hidden']}))
            request_obj = Request()

            if 'socketid-hidden' in request.POST:
                request_obj.socketid = request.POST['socketid-hidden']

            print request_obj.socketid
            data = []
            save_dir = os.path.join(conf.LOCAL_DEMO1_PIC_DIR)

            list = [os.path.join(conf.EXEC_DIR, 'stitch_full'), '--img', save_dir, '--verbose', '1', '--output',
                    save_dir + '/results/']

            path, dirs, files = os.walk(save_dir).next()
            file_count = len(files)

            list.append('--ncpus')
            list.append(str(min(file_count, 20)))

            r.publish('chat', json.dumps({'error': str('Calling run_executable in demo_upload'), 'socketid': self.request.POST['socketid-hidden']}))
            request_obj.log_to_terminal(str('Images Processed. Starting Executable'))
            request_obj.run_executable(list, '/app/media/pictures/demo1/results/result_stitch.jpg')

            data.append({'text': str('')})
            data.append({'result': '/app/media/pictures/demo/output/result_stitch.jpg'})
            response = JSONResponse(data, {}, response_mimetype(request))
            response['Content-Disposition'] = 'inline; filename=files.json'
            r.publish('chat', json.dumps({'error': str('Exiting demoUpload'), 'socketid': self.request.POST['socketid-hidden']}))
            return response

    except Exception as e:
        r.publish('chat', json.dumps({'message': str(traceback.format_exc()), 'socketid': str(request.POST['socketid-hidden'])}))
        return HttpResponse(str(traceback.format_exc()))

    return HttpResponse('Not a post request')

def log_every_request(job_obj):
    """
    Method for logging. 
    """
    try:
        now = datetime.datetime.utcnow()
        req_obj = RequestLog(cloudcvid=job_obj.userid, noOfImg=job_obj.count,
                          isDropbox = job_obj.isDropbox(), apiName=None,
                          function=job_obj.executable, dateTime=now)
        req_obj.save()
    except Exception as e:
        r.publish('chat', json.dumps({'error': str(traceback.format_exc()), 'socketid': job_obj.socketid}))

@csrf_exempt
def matlabReadRequest(request):
    """
    Method that makes request to the matlab api. 
    """
    if request.method == 'POST':    # post request
        post_dict = parser.parse(request.POST.urlencode())

        try:
            job_obj = Job(params_obj=post_dict)
            log_to_terminal('Server: Post Request Recieved', job_obj.socketid)
            response = saveFilesAndProcess(request, job_obj)

        except Exception as e:
            log_and_exit(str(traceback.format_exc()), job_obj.socketid)
            return HttpResponse('Error at server side')


        return HttpResponse(str(response))

    else:                           # get request
        response = JSONResponse({}, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response
        # return HttpResponse(str(request))

def authenticate(request, auth_name):
    """
    Authentication method: Currently used for Python API.
    """
    if auth_name == 'dropbox':
        is_API = 'type' in request.GET and request.GET['type']=='api'
        contains_UUID = 'userid' in request.GET

        str_response = dbauth.handleAuth(request, is_API, contains_UUID)

        # if the call comes from Matlab or Python API, send the obtained JSON string
        if is_API:
            return HttpResponse(str_response)

        # else if it comes from browser - redirect the browser
        else:
            return HttpResponseRedirect(str_response)

    if auth_name == 'google':
        is_API = 'type' in request.GET and request.GET['type']=='api'
        contains_UUID = 'userid' in request.GET

        str_response = gauth.handleAuth(request, is_API, contains_UUID)

        # if the call comes from Matlab or Python API, send the obtained JSON string
        if is_API:
            return HttpResponse(str_response)

        # else if it comes from browser - redirect the browser
        else:
            return HttpResponseRedirect(str_response)

    #Invalid URL if its not one of the above authentication system
    return HttpResponse('Invalid URL')


@csrf_exempt
def callback(request, auth_name):
    """
    Callback method associated with authentication part. 
    """
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

####################################################################

# from rest_framework.views import APIView
# from rest_framework import status
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from django.http import Http404
# from rest_framework import generics
# from serializers import *

# class UserList(generics.ListCreateAPIView):
#     """
#     List all Users, or create a new user.
#     """
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#     model = User

# class RequestLogList(generics.ListCreateAPIView):
#     queryset = RequestLog.objects.all()
#     serializer_class = RequestLogSerializer
#     model = RequestLog

# class GroupList(generics.ListCreateAPIView):
#     queryset = Group.objects.all()
#     serializer_class = GroupSerializer
#     model = Group

# class CurrentRequestList(generics.ListCreateAPIView):
#     queryset = CurrentRequest.objects.all()
#     serializer_class = CurrentRequestSerializer
#     model = CurrentRequest

# class ImagesList(generics.ListCreateAPIView):
#     queryset = Images.objects.all()
#     serializer_class = ImagesSerializer
#     model = Images


# class UserList(APIView):
#     """
#     List all Users, or create a new user.
#     """
#     queryset = User.objects.all()
#     model = User
#     def get(self, request, format=None):
#         user = self.queryset
#         serializer = UserSerializer(user, many=True)
#         return Response(serializer.data)

    # def post(self, request, format=None):
    #     serializer = UserSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class UserDetail(APIView):
#     """
#     Retrieve, update or delete a User instance.
#     """
#     queryset = User.objects.all()
#     def get_object(self, pk):
#         try:
#             return self.queryset.get(pk=pk)
#         except User.DoesNotExist:
#             raise Http404

#     def get(self, request, pk, format=None):
#         user = self.get_object(pk)
#         serializer = UserSerializer(user)
#         return Response(serializer.data)

#     def put(self, request, pk, format=None):
#         user = self.get_object(pk)
#         serializer = UserSerializer(user, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk, format=None):
#         user = self.get_object(pk)
#         user.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# class RequestLogList(APIView):
#     """
#     List all the requst jobs and their respective details. 
#     """
#     def get(self, request, format=None):
#         jobs = RequestLog.objects.all()
#         serializer = RequestLogSerializer(jobs, many=True)
#         return Response(serializer.data)

#     def post(self, request, format=None):
#         serializer = RequestLogSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class GroupList(APIView):
#     """
#     List all the Groups, or create a new Group.
#     """
#     def get(self, request, format=None):
#         groups = Group.objects.all()
#         serializer = GroupSerializer(groups, many=True)
#         return Response(serializer.data)

#     def post(self, request, format=None):
#         serializer = GroupSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class GroupDetail(APIView):
#     """
#     Retrieve, update or delete a Group instance.
#     """
#     def get_object(self, pk):
#         try:
#             return Group.objects.get(pk=pk)
#         except Group.DoesNotExist:
#             raise Http404

#     def get(self, request, pk, format=None):
#         group = self.get_object(pk)
#         serializer = GroupSerializer(group)
#         return Response(serializer.data)

#     def put(self, request, pk, format=None):
#         group = self.get_object(pk)
#         serializer = GroupSerializer(group, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk, format=None):
#         group = self.get_object(pk)
#         group.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# class CurrentRequestList(APIView):
#     """
#     List all the Curent Requests, or create a new Request.
#     """
#     def get(self, request, format=None):
#         current_requset = CurrentRequest.objects.all()
#         serializer = CurrentRequestSerializer(current_requset, many=True)
#         return Response(serializer.data)

#     def post(self, request, format=None):
#         serializer = CurrentRequestSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class CurrentRequestDetail(APIView):
#     """
#     Retrieve, update or delete a CurrentRequest instance.
#     """
#     def get_object(self, pk):
#         try:
#             return CurrentRequest.objects.get(pk=pk)
#         except CurrentRequest.DoesNotExist:
#             raise Http404

#     def get(self, request, pk, format=None):
#         current_requset = self.get_object(pk)
#         serializer = CurrentRequestSerializer(current_requset)
#         return Response(serializer.data)

#     def put(self, request, pk, format=None):
#         current_requset = self.get_object(pk)
#         serializer = CurrentRequestSerializer(current_requset, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk, format=None):
#         current_requset = self.get_object(pk)
#         current_requset.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

# class ImagesList(APIView):
#     """
#     List all the Image Details stored in the different locations.
#     """
#     def get(self, request, format=None):
#         images = Image.objects.all()
#         serializer = ImagesSerializer(images, many=True)
#         return Response(serializer.data)

#     def post(self, request, format=None):
#         serializer = ImagesSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)