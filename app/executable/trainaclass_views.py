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
import scipy.io as sio
import caffe
import numpy as np

from urlparse import urlparse
from django.views.generic import CreateView, DeleteView
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt

from PIL import Image
from querystring_parser import parser
from os.path import splitext, basename
import redis

from app.models import Picture, RequestLog, Decaf, Classify, Trainaclass
from app.executable.LDA_files.test import caffe_classify, caffe_classify_image
from app.executable.LDA_files import train_fast
from app.classify_views import  classify_wrapper_local as default_classify
import app.conf as conf
redis_obj = redis.StrictRedis(host='localhost', port=6379, db=0)
classify_channel_name = 'classify_queue'

### SET OF PATH CONSTANTS - SOME UNUSED
##
# File initially downloaded here
download_directory = conf.PIC_DIR
# Input image is saved here (symbolic links) - after resizing to 500 x 500
physical_job_root = conf.LOCAL_CLASSIFY_JOB_DIR
demo_log_file = physical_job_root + 'classify_demo.log'
##
###


def log_to_terminal(message, socketid):
    redis_obj.publish('chat', json.dumps({'message': str(message), 'socketid': str(socketid)}))


def classify_wrapper_local(jobPath, socketid, result_path):
    try:
        ImagePath = os.path.join(jobPath,'test')
        modelPath = os.path.join(jobPath,'util')

        new_labels = sio.loadmat(os.path.join(modelPath,'new_labels.mat'))
        new_labels_cells = new_labels['WNID']

        # Set the right path to your model file, pretrained model,
        # and the image you would like to classify.
        MODEL_FILE = os.path.join(modelPath,'newCaffeModel.prototxt')
        PRETRAINED = os.path.join(modelPath,'newCaffeModel.caffemodel')

        caffe.set_phase_test()
        caffe.set_mode_gpu()

        net = caffe.Classifier(MODEL_FILE, PRETRAINED,
                        mean=np.load(os.path.join(conf.CAFFE_DIR, 'python/caffe/imagenet/ilsvrc_2012_mean.npy')),
                        channel_swap=(2, 1, 0),
                        raw_scale=255,
                        image_dims=(256, 256))

        results = {}

        if os.path.isdir(ImagePath):
            for file_name in os.listdir(ImagePath):
                image_path = os.path.join(ImagePath, file_name)
                if os.path.isfile(image_path):

                    tags = caffe_classify_image(net, image_path, new_labels_cells)
                    log_to_terminal("Results: "+str(tags), socketid)
                    webResult = {}
                    webResult[os.path.join(result_path,file_name)] = tags

                    redis_obj.publish('chat',
                                   json.dumps({'web_result': json.dumps(webResult), 'socketid': str(socketid)}))

            log_to_terminal('Thank you for using CloudCV', socketid)

    except Exception as e:
        log_to_terminal(str(traceback.format_exc()), socketid)


class ClassifyThread(threading.Thread):
    def __init__(self, image_path, result_path, socketid):
        threading.Thread.__init__(self)
        self.r = redis_obj
        self.image_path = image_path
        self.result_path = result_path
        self.socketid = socketid
        self.log_to_terminal("inside thread")

    def run(self):
        try:
            result = caffe_classify(self.image_path)
            self.log_to_terminal(result)

            image, tags = result.popitem()
            web_result = {}
            web_result[self.result_path] = tags
            self.r.publish('chat',json.dumps({'web_result': json.dumps(web_result), 'socketid': str(self.socketid)}))
        except Exception as e:
            self.log_to_terminal(str(traceback.format_exc()))

    def log_to_terminal(self, message):
        self.r.publish('chat', json.dumps({'message': str(message), 'socketid': str(self.socketid)}))


def response_mimetype(request):
    if "application/json" in request.META['HTTP_ACCEPT']:
        return "application/json"
    else:
        return "text/plain"


class TrainaclassCreateView(CreateView):
    model = Trainaclass
    r = None
    socketid = None

    count_hits = 0

    def form_valid(self, form):

        redis_obj.lpush('trainaclass', str(self.request))
        self.r = redis_obj
        session = self.request.session.session_key
        socketid = self.request.POST['socketid']
        labelnames = self.request.POST['labelnames'].replace(' ', '_')
        log_to_terminal(str(self.request.POST['labelnames']), socketid)

        self.socketid = socketid

        try:
            #log_to_terminal('Logging user ip....', self.socketid)
            client_address = self.request.META['REMOTE_ADDR']
            #client_address = self.request.environ.get('HTTP_X_FORWARDED_FOR')
            #log_to_terminal(client_address, self.socketid)

            self.object = form.save()

            fcountfile = open(os.path.join(conf.LOG_DIR, 'log_count.txt'), 'a')
            fcountfile.write(str(self.request.META.get('REMOTE_ADDR')) + '\n')
            fcountfile.close()

            self.count_hits += 1


            old_save_dir = os.path.dirname(conf.PIC_DIR)

            folder_name = str(socketid)
            save_dir = os.path.join(conf.PIC_DIR, folder_name)
            train_dir = os.path.join(save_dir, 'train')
            test_dir = os.path.join(save_dir, 'test')
            util_dir = os.path.join(save_dir, 'util')

            # Make the new directory based on time
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                os.makedirs(train_dir)
                os.makedirs(util_dir)
                os.makedirs(test_dir)



            try:
                all_files = self.request.FILES.getlist('file')
                data = {'files':[]}

                if len(all_files) == 1:
                    log_to_terminal(str('Downloading Image for label:' + labelnames), self.socketid)
                else:
                    log_to_terminal(str('Downloading Images for label: ' + labelnames), self.socketid)

                if labelnames.strip().lower() != 'test':
                    label_dir = os.path.join(train_dir, labelnames)
                    url = os.path.join(conf.PIC_URL, socketid, 'train', labelnames)
                else:
                    label_dir = test_dir
                    url = os.path.join(conf.PIC_URL, socketid, 'test')

                if not os.path.exists(label_dir):
                    os.makedirs(label_dir)


                for file in all_files:
                    try:
                        a = Picture()
                        tick = time.time()
                        strtick = str(tick).replace('.','_')
                        fileName, fileExtension = os.path.splitext(file.name)
                        file.name = fileName + strtick + fileExtension
                        a.file.save(file.name, file)
                        file.name = a.file.name
                        imgfile = Image.open(os.path.join(old_save_dir, file.name))
                        size = (500,500)
                        imgfile.thumbnail(size,Image.ANTIALIAS)
                        imgfile.save(os.path.join(label_dir, file.name))
                        data['files'].append({
                            'label': labelnames,
                            'url': os.path.join(url, file.name),
                            'name': file.name,
                            'type': 'image/png',
                            'thumbnailUrl': os.path.join(url, file.name),
                            'size': 0,
                        })
                    except Exception as e:
                        log_to_terminal(str(traceback.format_exc()), self.socketid)


            except Exception as e:
                print e
                log_to_terminal(str(traceback.format_exc()), self.socketid)
            log_to_terminal(str(len(all_files)) + str(' images saved for '+ labelnames), self.socketid)
            response = JSONResponse(data, {}, response_mimetype(self.request))
            response['Content-Disposition'] = 'inline; filename=files.json'
            return response

        except Exception as e:
            redis_obj.lpush('trainaclass_exception', str(traceback.format_exc()))
            log_to_terminal(str(traceback.format_exc()), self.socketid)

    def get_context_data(self, **kwargs):
        context = super(TrainaclassCreateView, self).get_context_data(**kwargs)
        context['pictures'] = Trainaclass.objects.all()
        return context


class TrainaclassDeleteView(DeleteView):
    model = Trainaclass

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

def trainModel(save_dir, socketid):
    train_fast.modelUpdate(save_dir+'/')

@csrf_exempt
def trainamodel(request):
    data = {}
    try:
        post_dict = parser.parse(request.POST.urlencode())

        socketid = post_dict['socketid']
        log_to_terminal('Beginning training a new model', post_dict['socketid'])

        old_save_dir = conf.PIC_DIR
        folder_name = str(socketid)
        save_dir = os.path.join(conf.PIC_DIR, folder_name)
        train_dir = os.path.join(save_dir, 'train')
        test_dir = os.path.join(save_dir, 'test')
        util_dir = os.path.join(save_dir, 'util')

        if not os.path.exists(os.path.join(old_save_dir, folder_name)):
            raise Exception('No training images has been provided for this job.')

        trainModel(save_dir, post_dict['socketid'])

        data['info'] = 'completed'
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        log_to_terminal('Finished training your model with the new categories. Now, upload some test images to test this model. ', socketid)
        return response
    except Exception as e:
        data['error'] = str(traceback.format_exc())
        log_to_terminal(str(traceback.format_exc()), socketid)
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

@csrf_exempt
def testmodel(request):
    data = {}
    try:
        post_dict = parser.parse(request.POST.urlencode())
        socketid = post_dict['socketid']
        log_to_terminal('Classifying test images', post_dict['socketid'])

        old_save_dir = conf.PIC_DIR
        folder_name = str(socketid)
        save_dir = os.path.join(conf.PIC_DIR, folder_name)
        train_dir = os.path.join(save_dir, 'train')
        test_dir = os.path.join(save_dir, 'test')
        util_dir = os.path.join(save_dir, 'util')

        if not os.path.exists(os.path.join(old_save_dir, folder_name)):
            raise Exception('No training images has been provided for this job.')

        if len(os.listdir(os.path.join(test_dir))) == 0:
            raise Exception('No test images provided')


        if not os.path.isfile(os.path.join(util_dir,'newCaffeModel.prototxt')):
            default_classify(test_dir, socketid, os.path.join(conf.PIC_URL, folder_name, 'test'))
            raise Exception('No model has been trained for this job.')


        classify_wrapper_local(save_dir, socketid,os.path.join(conf.PIC_URL, folder_name, 'test'))

        data['info'] = 'completed'
        data['prototxt'] = os.path.join(conf.PIC_URL, folder_name, 'util', 'newCaffeModel.prototxt')
        data['caffemodel'] = os.path.join(conf.PIC_URL, folder_name, 'util', 'newCaffeModel.caffemodel')
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        log_to_terminal('Classification completed', post_dict['socketid'])
        return response
    except Exception as e:
        data['error'] = str(traceback.format_exc())
        log_to_terminal(str(traceback.format_exc()), socketid)
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

@csrf_exempt
def demoTrainaclass(request):
    post_dict = parser.parse(request.POST.urlencode())
    try:
        if not os.path.exists(demo_log_file):
            log_file = open(demo_log_file, 'w')
        else:
            log_file = open(demo_log_file, 'a')

        if 'src' not in post_dict:
            data = {'error': 'NoImageSelected'}
        else:
            data = {'info': 'Processing'}
            result_path = post_dict['src']
            imgname = basename(urlparse(result_path).path)

            image_path = os.path.join(conf.LOCAL_DEMO_PIC_DIR, imgname)
            print image_path
            print result_path
            log_to_terminal('Processing image...', post_dict['socketid'])

            # This is for running it locally ie on Godel
            classify_wrapper_local(image_path, post_dict['socketid'], result_path)

            # This is for posting it on Redis - ie to Rosenblatt
            #classify_wrapper_redis(image_path, post_dict['socketid'], result_path)

            data = {'info': 'Finished training a new Model. Upload some test images to test the model'}

        try:
            client_address = request.META['REMOTE_ADDR']
            log_file.write('Demo classify request from IP:'+client_address)
            log_file.close();

        except Exception as e:
            log_file.write('Exception when finding client ip:'+str(traceback.format_exc())+'\n');
            log_file.close();

        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

    except Exception as e:
        data = {'result': str(traceback.format_exc())}
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response
