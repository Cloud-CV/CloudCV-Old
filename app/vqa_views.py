__author__ = 'clint'

import time
import subprocess
import os
import json
import traceback
import uuid
import shortuuid
import datetime
import json
import threading
import operator
import sys

from urlparse import urlparse
from django.views.generic import CreateView, DeleteView
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt

from PIL import Image
from querystring_parser import parser
from os.path import splitext, basename
import redis

from app.models import Picture, RequestLog, Decaf, Classify, Vqa
from app.executable.caffe_classify import caffe_classify, caffe_classify_image
import app.conf as conf
from app.celery.web_tasks.VqaFeatTask import featExtraction
from app.celery.web_tasks.VqaTask import answerQuestion

redis_obj = redis.StrictRedis(host='localhost', port=6379, db=0)

##
# LOG File
demo_log_file = conf.DEMO_VQA_LOG_FILE
##



def log_to_terminal(message, socketid):
    redis_obj.publish('chat', json.dumps({'message': str(message), 'socketid': str(socketid)}))


def vqa_wrapper_feat(src_path, socketid, result_url_prefix, feat_folder):

    featExtraction.delay(src_path, socketid, result_url_prefix,  feat_folder)


def vqa_wrapper_answer(feat_path, question, socketid, imageid):

    answerQuestion.delay(feat_path, question, socketid, imageid)


def response_mimetype(request):
    if "application/json" in request.META['HTTP_ACCEPT']:
        return "application/json"
    else:
        return "text/plain"


class VqaCreateView(CreateView):
    model = Vqa
    r = None
    socketid = None

    count_hits = 0

    def form_valid(self, form):
        self.r = redis_obj
        session = self.request.session.session_key
        socketid = self.request.POST['socketid-hidden']
        self.socketid = socketid

        try:
            #log_to_terminal('Logging user ip....', self.socketid)
            client_address = self.request.META['REMOTE_ADDR']
            #client_address = self.request.environ.get('HTTP_X_FORWARDED_FOR')
            #log_to_terminal(client_address, self.socketid)

            self.object = form.save()
            all_files = self.request.FILES.getlist('file')
            data = {'files':[]}

            fcountfile = open(os.path.join(conf.LOG_DIR, 'log_count.txt'), 'a')
            fcountfile.write(str(self.request.META.get('REMOTE_ADDR')) + '\n')
            fcountfile.close()

            self.count_hits += 1

        except Exception as e:
            log_to_terminal(str(traceback.format_exc()), self.socketid)

        old_save_dir = os.path.dirname(conf.PIC_DIR)

        # folder_name = str(shortuuid.uuid())
        # For now lets use socket id
        folder_name = self.socketid
        save_dir = os.path.join(conf.PIC_DIR, folder_name)
        save_url = os.path.join(conf.PIC_URL, folder_name)
        feat_folder = os.path.join(save_dir, 'results')

        # Make the new directory based on time
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            os.makedirs(feat_folder)


        log_to_terminal(str('VQA Phase 1...'), self.socketid)

        if len(all_files) == 1:
            log_to_terminal(str('Downloading Image...'), self.socketid)
        else:
            log_to_terminal(str('Downloading Images...'), self.socketid)


        for file in all_files:
            try:
                a = Picture()
                tick = time.time()
                strtick = str(tick).replace('.', '_')
                fileName, fileExtension = os.path.splitext(file.name)
                file.name = fileName + strtick + fileExtension
                a.file.save(file.name, file)
                file.name = a.file.name
                imgfile = Image.open(os.path.join(old_save_dir, file.name))
                size = (500, 500)
                imgfile.thumbnail(size, Image.ANTIALIAS)
                imgfile.save(os.path.join(save_dir, file.name))
                thumbPath = os.path.join(save_url, file.name)
                data['files'].append({
                    'url': thumbPath,
                    'name': file.name,
                    'type': 'image/png',
                    'thumbnailUrl': thumbPath,
                    'size': 0,
                })
            except Exception as e:
                log_to_terminal(str(traceback.format_exc()), self.socketid)

        if len(all_files) == 1:
            log_to_terminal(str('Processing Image...'), self.socketid)
        else:
            log_to_terminal(str('Processing Images...'), self.socketid)

        time.sleep(.5)

        # This is for running it locally
        vqa_wrapper_feat(save_dir, socketid, save_url, feat_folder)

        # This is for posting it on Redis - ie to Rosenblatt
        #classify_wrapper_redis(job_directory, socketid, result_folder)

        response = JSONResponse(data, {}, response_mimetype(self.request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

    def get_context_data(self, **kwargs):
        context = super(VqaCreateView, self).get_context_data(**kwargs)
        context['pictures'] = Classify.objects.all()
        return context


class VqaDeleteView(DeleteView):
    model = Classify

    def delete(self, request, *args, **kwargs):
        """
        This does not actually delete the file, only the database record.  But
        that is easy to implement.
        """
        self.object = self.get_object()
        self.object.delete()
        if request.is_ajax():
            response = JSONResponse(True, {}, response_mimetype(self.request))
            response['Content-Disposition'] = 'inline; filename=files.json'
            return response
        else:
            return HttpResponseRedirect('/upload/new')


class JSONResponse(HttpResponse):
    """JSON response class."""

    def __init__(self, obj='', json_opts={}, mimetype="application/json", *args, **kwargs):
        content = json.dumps(obj, **json_opts)
        super(JSONResponse, self).__init__(content, mimetype, *args, **kwargs)

@csrf_exempt
def demoVqa(request):
    post_dict = parser.parse(request.POST.urlencode())
    try:
        socketid = post_dict['socketid']
        if not os.path.exists(demo_log_file):
            log_file = open(demo_log_file, 'w')
        else:
            log_file = open(demo_log_file, 'a')

        if 'src' not in post_dict:
            data = {'error': 'NoImageSelected'}
        else:
            data = {'info': 'Processing'}
            result_prefix_url = post_dict['src']
            imgname = basename(urlparse(result_prefix_url).path)

            image_path = os.path.join(conf.LOCAL_DEMO_VQA_PIC_DIR, imgname)

            # folder_name = str(shortuuid.uuid())
            # For now lets use socket id
            folder_name = socketid
            save_dir = os.path.join(conf.PIC_DIR, folder_name)
            feat_folder = os.path.join(save_dir, 'results')

            # Make the new directory based on time
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                os.makedirs(feat_folder)

            feat_path = os.path.join(feat_folder, imgname)

            print image_path
            print result_prefix_url
            log_to_terminal('Processing image...', socketid)

            # This is for running it locally ie on Godel
            vqa_wrapper_feat(image_path, socketid, result_prefix_url, feat_path)

            # This is for posting it on Redis - ie to Rosenblatt
            #classify_wrapper_redis(image_path, post_dict['socketid'], result_path)

            data = {'info': 'Completed'}

        try:
            client_address = request.META['REMOTE_ADDR']
            log_file.write('Demo classify request from IP:'+client_address)
            log_file.close()

        except Exception as e:
            log_file.write('Exception when finding client ip:'+str(traceback.format_exc())+'\n');
            log_file.close()

        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

    except Exception as e:
        data = {'result': str(traceback.format_exc())}
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

@csrf_exempt
def handleQuestion(request):
    post_dict = parser.parse(request.POST.urlencode())
    try:
        socketid = post_dict['socketid']
        imageid = post_dict['imageid']

        result_url = post_dict['src']
        question = post_dict['qn']

        data = {'info': 'Processing'}

        imgname = basename(urlparse(result_url).path)

        # folder_name = str(shortuuid.uuid())
        # For now lets use socket id

        feat_folder = os.path.join(conf.PIC_DIR, socketid, 'results')
        feat_path = os.path.join(feat_folder, imgname)

        # Throw exception here if file does not exist
        # if not os.path.exists(feat_path):

        log_to_terminal(feat_path, socketid)
        log_to_terminal(result_url, socketid)
        log_to_terminal('Processing image...', socketid)

        # This is for running it locally ie on Godel
        vqa_wrapper_answer(feat_path, question, socketid, imageid)

        # This is for posting it on Redis - ie to Rosenblatt
        #classify_wrapper_redis(image_path, post_dict['socketid'], result_path)

        data = {'info': 'Completed'}

        # try:
        #     client_address = request.META['REMOTE_ADDR']
        #     log_file.write('Demo classify request from IP:'+client_address)
        #     log_file.close()
        #
        # except Exception as e:
        #     log_file.write('Exception when finding client ip:'+str(traceback.format_exc())+'\n');
        #     log_file.close()

        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

    except Exception as e:
        data = {'result': str(traceback.format_exc())}
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response