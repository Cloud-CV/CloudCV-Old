__author__ = 'clint'

from django.views.generic import CreateView, DeleteView
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from urlparse import urlparse
from PIL import Image
from querystring_parser import parser
from os.path import splitext, basename

from app.models import Picture, RequestLog, Decaf, Classify, Trainaclass
from app.executable.LDA_files.test import caffe_classify, caffe_classify_image
from app.executable.LDA_files import train_fast
from app.classify_views import  classify_wrapper_local as default_classify

import app.conf as conf
import time
import os
import json
import traceback

from django.views.generic import CreateView, DeleteView
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

from PIL import Image
from querystring_parser import parser
import redis

from app.models import Picture, Trainaclass
from celeryTasks.webTasks.trainTask import trainImages
from celeryTasks.webTasks.trainTask import customClassifyImages
from cloudcv17 import config
import app.conf as conf

redis_obj = redis.StrictRedis(host=config.REDIS_HOST, port=6379, db=0)
classify_channel_name = 'classify_queue'

# SET OF PATH CONSTANTS - SOME UNUSED
# File initially downloaded here
download_directory = conf.PIC_DIR
# Input image is saved here (symbolic links) - after resizing to 500 x 500
physical_job_root = conf.LOCAL_CLASSIFY_JOB_DIR
demo_log_file = physical_job_root + 'classify_demo.log'
<<<<<<< HEAD

rs = redis.StrictRedis(host=config.REDIS_HOST, port=6379)
=======
>>>>>>> documentation changes

def log_to_terminal(message, socketid):
    redis_obj.publish('chat', json.dumps({'message': str(message), 'socketid': str(socketid)}))


def classify_wrapper_local(jobPath, socketid, result_path):
    customClassifyImages.delay(jobPath, socketid, result_path)


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
        """
        This function created the view and validates the form.
        It adds images to a new label. Makes directory and save them.
        """
        redis_obj.lpush('trainaclass', str(self.request))
        self.r = redis_obj
        socketid = self.request.POST['socketid']
        labelnames = self.request.POST['labelnames'].replace(' ', '_')
        log_to_terminal("Label: " + str(self.request.POST['labelnames']), socketid)
        self.socketid = socketid
        try:
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

            rs.publish('chat', json.dumps({'message': 'save_dir ' + save_dir, 'socketid': str(socketid)}))

            try:
                all_files = self.request.FILES.getlist('file')
                data = {'files': []}

                if len(all_files) == 1:
                    log_to_terminal(str('Downloading Image for label: ' + labelnames), self.socketid)
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
                        strtick = str(tick).replace('.', '_')
                        fileName, fileExtension = os.path.splitext(file.name)
                        file.name = fileName + strtick + fileExtension
                        a.file.save(file.name, file)
                        file.name = a.file.name
                        imgfile = Image.open(os.path.join(old_save_dir, file.name))
                        size = (500, 500)
                        imgfile.thumbnail(size, Image.ANTIALIAS)
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
            log_to_terminal(str(len(all_files)) + str(' images saved for ' + labelnames), self.socketid)
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


@csrf_exempt
def trainamodel(request):
    """
    Method for training a model
    """
    data = {}
    post_dict = parser.parse(request.POST.urlencode())
    socketid = post_dict['socketid']
    log_to_terminal('Beginning training a new model', post_dict['socketid'])

    # old_save_dir = conf.PIC_DIR
    folder_name = str(socketid)
    save_dir = os.path.join(conf.PIC_DIR, folder_name)
    # train_dir = os.path.join(save_dir, 'train')
    # test_dir = os.path.join(save_dir, 'test')
    # util_dir = os.path.join(save_dir, 'util')

    trainImages.delay(os.path.join(save_dir, ''), socketid)
    data['info'] = 'completed'
    response = JSONResponse(data, {}, response_mimetype(request))
    response['Content-Disposition'] = 'inline; filename=files.json'
    return response


@csrf_exempt
def testmodel(request):
    """
    Method for testing an already trained model.
    """
    data = {}
    try:
        post_dict = parser.parse(request.POST.urlencode())
        socketid = post_dict['socketid']
        log_to_terminal('Classifying test images', post_dict['socketid'])

        old_save_dir = conf.PIC_DIR
        folder_name = str(socketid)
        save_dir = os.path.join(conf.PIC_DIR, folder_name)
        # train_dir = os.path.join(save_dir, 'train')
        test_dir = os.path.join(save_dir, 'test')
        util_dir = os.path.join(save_dir, 'util')

        if not os.path.exists(os.path.join(old_save_dir, folder_name)):
            raise Exception('No training images has been provided for this job.')

        if len(os.listdir(os.path.join(test_dir))) == 0:
            raise Exception('No test images provided')

        if not os.path.isfile(os.path.join(util_dir, 'newCaffeModel.prototxt')):
            # default_classify(test_dir, socketid, os.path.join(conf.PIC_URL, folder_name, 'test'))
            raise Exception('No model has been trained for this job.')

        classify_wrapper_local(save_dir, socketid, os.path.join(conf.PIC_URL, folder_name, 'test'))
        data['info'] = 'completed'
        data['prototxt'] = os.path.join(conf.PIC_URL, folder_name, 'util', 'newCaffeModel.prototxt')
        data['caffemodel'] = os.path.join(conf.PIC_URL, folder_name, 'util', 'newCaffeModel.caffemodel')
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

    except:
        data['error'] = str(traceback.format_exc())
        log_to_terminal(str(traceback.format_exc()), socketid)
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response
