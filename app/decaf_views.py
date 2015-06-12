__author__ = 'dexter'
import time
import subprocess
import os
import json
import traceback
import operator
import shortuuid
import requests
from os.path import splitext, basename
from urlparse import urlparse
import traceback
from django.views.generic import CreateView, DeleteView
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import redis
from querystring_parser import parser
from app.models import Picture, RequestLog, Decaf, Decafmodel
import app.conf as conf
from .response import JSONResponse, response_mimetype

from app.celery.web_tasks.DecafTask import decafImages

redis_obj = redis.StrictRedis(host='localhost', port=6379, db=0)
ps_obj = redis_obj.pubsub()
decaf_channel_name = 'decaf_server_queue'
IMAGEFOLDER = '/srv/share/cloudcv/jobs/'
DEMO_IMAGE_PATH = '/srv/share/cloudcv/jobs/demo'


def log_to_terminal(message, socketid):
        redis_obj.publish('chat', json.dumps({'error': str(message), 'socketid': str(socketid)}))

def decaf_wrapper_local(src_path, output_path, socketid, result_path, single_file_name='', modelname=''):
    # try:
    #     #Entire Directory
    #     if os.path.isdir(os.path.join(src_path,single_file_name)):
    #
    #         for file_name in os.listdir(src_path):
    #             tags = {}
    #             image_path = os.path.join(src_path, file_name)
    #             if os.path.isfile(image_path):
    #
    #                 """ Trying to get the output of classify python script to send to user - Part 1/4
    #                 myPrint = CustomPrint(socketid)
    #                 old_stdout=sys.stdout
    #                 sys.stdout = myPrint
    #                 """
    #                 print 'Running caffe classify on multiple images'
    #
    #                 mat_file_path = decaf.calculate_decaf_image(file_name, src_path, output_path, 3, socketid, tags)
    #                 print tags
    #                 """ Part 2/2
    #                 sys.stdout=old_stdout
    #                 """
    #                 log_to_terminal("Results: "+str(tags), socketid)
    #                 sorted_tags = sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)
    #
    #                 webResult = {}
    #                 webResult[str(result_path + file_name)] = sorted_tags
    #                 result_url = urlparse(result_path).path
    #                 redis_obj.publish('chat',
    #                                json.dumps({'web_result': os.path.join(result_url, 'results', file_name+'.mat'), 'socketid': str(socketid)}))
    #
    #         log_to_terminal('Thank you for using CloudCV', socketid)
    #     # Single File
    #     else:
    #         """ Part 3/4
    #         myPrint = CustomPrint(socketid)
    #         old_stdout=sys.stdout
    #         sys.stdout = myPrint
    #         """
    #         tags = {}
    #         print 'Running caffe classify on a single image: ' + single_file_name
    #
    #         mat_file_path = decaf.calculate_decaf_image(single_file_name, src_path, output_path, 3, socketid, tags)
    #         """ Part 4/4
    #         sys.stdout=old_stdout
    #         """
    #         log_to_terminal("Results: "+str(tags), socketid)
    #
    #         tags = sorted(tags.iteritems(), key=operator.itemgetter(1), reverse=True)
    #         web_result = {}
    #         web_result[str(result_path)] = tags
    #         result_url = os.path.dirname(urlparse(result_path).path)
    #         redis_obj.publish('chat', json.dumps({'web_result': os.path.join(result_url, 'results', single_file_name+'.mat'), 'socketid': str(socketid)}))
    #
    #         log_to_terminal('Thank you for using CloudCV', socketid)
    #
    # except Exception as e:
    #     log_to_terminal(str(traceback.format_exc()), socketid)
    print "Inside decaf_wrapper_local: ModelName: " + modelname
    try:
    	decafImages.delay(src_path, output_path, socketid, result_path, single_file_name, modelname)
    except Exception as e:
	log_to_terminal(str(traceback.format_exc()),socketid);

class DecafCreateView(CreateView):
    model = Decaf
    r = None
    socketid = None

    def getThumbnail(self, image_url_prefix, name):
        im = Image.open('/var/www/html/cloudcv/fileupload'+image_url_prefix+name)
        size = 128, 128
        im.thumbnail(size, Image.ANTIALIAS)
        filename, fileext = splitext(basename(name))
        file = image_url_prefix + 'thumbnails/' + filename + '.' + fileext
        im.save('/var/www/html/cloudcv/fileupload'+file)
        return file

    count_hits = 0


    def form_valid(self, form):

        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        session = self.request.session.session_key
        socketid = self. request.POST['socketid-hidden']
        self.socketid = socketid

        try:
            self.object = form.save()
            all_files = self.request.FILES.getlist('file')
            data = {'files':[]}

        except Exception as e:
            log_to_terminal(str(traceback.format_exc()), self.socketid)

        old_save_dir = os.path.dirname(conf.PIC_DIR)
        folder_name = str(shortuuid.uuid())
        save_dir = os.path.join(conf.PIC_DIR, folder_name)
        output_path = os.path.join(save_dir, 'results')
        # Make the new directory based on time
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            os.makedirs(os.path.join(save_dir, 'results'))


        if len(all_files) == 1:
            log_to_terminal(str('Downloading Image...'), self.socketid)
        else:
            log_to_terminal(str('Downloading Images...'), self.socketid)


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
                imgfile.save(os.path.join(save_dir, file.name))
                thumbPath = os.path.join(folder_name, file.name)
                data['files'].append({
                    'url': conf.PIC_URL+thumbPath,
                    'name': file.name,
                    'type': 'image/png',
                    'thumbnailUrl': conf.PIC_URL+thumbPath,
                    'size': 0,
                })
            except Exception as e:
                log_to_terminal(str(traceback.format_exc()), self.socketid)

        if len(all_files) == 1:
            log_to_terminal(str('Processing Image...'), self.socketid)
        else:
            log_to_terminal(str('Processing Images...'), self.socketid)

        time.sleep(.5)

        # This is for running it locally ie on Godel
        decaf_wrapper_local(save_dir, output_path, socketid, os.path.join(conf.PIC_URL, folder_name))

        # This is for posting it on Redis - ie to Rosenblatt
        #classify_wrapper_redis(job_directory, socketid, result_folder)

        response = JSONResponse(data, {}, response_mimetype(self.request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

    def get_context_data(self, **kwargs):
        context = super(DecafCreateView, self).get_context_data(**kwargs)
        context['pictures'] = Decaf.objects.all()
        return context

@csrf_exempt
def demoDecaf(request):
    post_dict = parser.parse(request.POST.urlencode())
    try:

        if 'src' not in post_dict:
            # Run on all images:
            image_path = conf.LOCAL_DEMO_PIC_DIR
            imgname = ''

            img_url = os.path.join(os.path.dirname(urlparse(conf.PIC_URL.rstrip('/')).path), 'demo')
            print img_url
        else:
            data = {'info': 'Processing'}
            img_url = post_dict['src']
            print img_url

            imgname = basename(urlparse(img_url).path)
            image_path = os.path.join(conf.LOCAL_DEMO_PIC_DIR, imgname)

        output_path = os.path.join(conf.LOCAL_DEMO_PIC_DIR, 'results')
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        print image_path
        print output_path
        log_to_terminal('Processing image...', post_dict['socketid'])

        # This is for running it locally ie on Godel
        decaf_wrapper_local(conf.LOCAL_DEMO_PIC_DIR, output_path, post_dict['socketid'], img_url, imgname)

        # This is for posting it on Redis - ie to Rosenblatt
        #classify_wrapper_redis(image_path, post_dict['socketid'], result_path)

        data = {'info': 'Completed'}

        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

    except Exception as e:
        data = {'result': str(traceback.format_exc())}
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

def decafDemo(request):
    post_dict = parser.parse(request.POST.urlencode())
    log_to_terminal('Processing Demo Images Now', post_dict['socketid'])
    if 'src' in post_dict and post_dict['src']!='':
        file_name = basename(urlparse(post_dict['src']).path)
        redis_obj.publish(decaf_channel_name, json.dumps({'dir': DEMO_IMAGE_PATH, 'flag': '2', 'socketid': post_dict['socketid'], 'demo':'True', 'filename': file_name}))
    else:
        redis_obj.publish(decaf_channel_name, json.dumps({'dir': DEMO_IMAGE_PATH, 'flag': '2', 'socketid': post_dict['socketid']}))

import re
def downloadAndSaveImages(url_list, socketid):
    try:
        uuid = shortuuid.uuid()
        directory = os.path.join(conf.PIC_DIR , str(uuid))
        if not os.path.exists(directory):
            os.mkdir(directory)

        for url in url_list[""]:
            try:
                log_to_terminal(str(url), socketid)

                file = requests.get(url)
                file_full_name_raw = basename(urlparse(url).path)
                file_name_raw, file_extension = os.path.splitext(file_full_name_raw)
                print file_name_raw, file_extension
                regex = re.compile('[^a-zA-Z0-9]')
                #First parameter is the replacement, second parameter is your input string
                file_name = re.sub('[^a-zA-Z0-9]+', '', file_name_raw)
                print file_name_raw
                print file_name

                f = open(os.path.join(conf.PIC_DIR, str(uuid)+file_name+file_extension), 'wb')
                f.write(file.content)
                f.close()

                imgFile = Image.open(os.path.join(conf.PIC_DIR, str(uuid)+file_name+file_extension))
                size = (500, 500)
                imgFile.thumbnail(size, Image.ANTIALIAS)
                imgFile.save(os.path.join(conf.PIC_DIR, str(uuid), file_name+file_extension))
                log_to_terminal('Saved Image: '+str(url), socketid)
            except Exception as e:
                print str(e)
        return uuid, directory
    except Exception as e:
        print 'Exception'+str(traceback.format_exc())



@csrf_exempt
def decafDropbox(request):
    post_dict = parser.parse(request.POST.urlencode())
    try:
        if 'urls' not in post_dict:
            data = {'error': 'NoFileSelected'}
        else:
            data = {'info': 'ProcessingImages'}
            #Download these images. Run Feature Extraction. Post results.
            uuid, image_path = downloadAndSaveImages(post_dict['urls'], post_dict['socketid'])

            output_path = os.path.join(image_path, 'results')
            print image_path
            print output_path
            print uuid
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            decaf_wrapper_local(image_path, output_path, post_dict['socketid'], os.path.join(conf.PIC_URL, uuid))
            log_to_terminal('Processing Images Now', post_dict['socketid'])

        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response
    except Exception as e:
        data = {'result': str(traceback.format_exc())}
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

class DecafModelCreateView(CreateView):
    model = Decafmodel
    r = None
    socketid = None

    def getThumbnail(self, image_url_prefix, name):
        im = Image.open('/var/www/html/cloudcv/fileupload'+image_url_prefix+name)
        size = 128, 128
        im.thumbnail(size, Image.ANTIALIAS)
        filename, fileext = splitext(basename(name))
        file = image_url_prefix + 'thumbnails/' + filename + '.' + fileext
        im.save('/var/www/html/cloudcv/fileupload'+file)
        return file

    count_hits = 0


    def form_valid(self, form):

        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        session = self.request.session.session_key
        socketid = self. request.POST['socketid-hidden']
        modelname = ''
        if 'model-name' in self.request.POST:
            modelname = self.request.POST['model-name']
            print modelname

        self.socketid = socketid

        try:
            self.object = form.save()
            all_files = self.request.FILES.getlist('file')
            data = {'files':[]}

        except Exception as e:
            log_to_terminal(str(traceback.format_exc()), self.socketid)

        old_save_dir = os.path.dirname(conf.PIC_DIR)
        folder_name = str(shortuuid.uuid())
        save_dir = os.path.join(conf.PIC_DIR, folder_name)
        output_path = os.path.join(save_dir, 'results')
        # Make the new directory based on time
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            os.makedirs(os.path.join(save_dir, 'results'))

        log_to_terminal(str('SocketID: '+str(self.socketid)), self.socketid)
        if len(all_files) == 1:
            log_to_terminal(str('Downloading Image...'), self.socketid)
        else:
            log_to_terminal(str('Downloading Images...'), self.socketid)


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
                imgfile.save(os.path.join(save_dir, file.name))
                thumbPath = os.path.join(folder_name, file.name)
                data['files'].append({
                    'url': conf.PIC_URL+thumbPath,
                    'name': file.name,
                    'type': 'image/png',
                    'thumbnailUrl': conf.PIC_URL+thumbPath,
                    'size': 0,
                })
            except Exception as e:
                log_to_terminal(str(traceback.format_exc()), self.socketid)

        if len(all_files) == 1:
            log_to_terminal(str('Processing Image...'), self.socketid)
        else:
            log_to_terminal(str('Processing Images...'), self.socketid)

        time.sleep(.5)

        # This is for running it locally ie on Godel
        decaf_wrapper_local(save_dir, output_path, socketid, os.path.join(conf.PIC_URL, folder_name), modelname=modelname)

        # This is for posting it on Redis - ie to Rosenblatt
        #classify_wrapper_redis(job_directory, socketid, result_folder)

        response = JSONResponse(data, {}, response_mimetype(self.request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

    def get_context_data(self, **kwargs):
        context = super(DecafModelCreateView, self).get_context_data(**kwargs)
        context['pictures'] = Decaf.objects.all()
        return context

@csrf_exempt
def decaf_train(request):
    post_dict = parser.parse(request.POST.urlencode())
    try:
        if 'urls' not in post_dict:
            data = {'error': 'NoFileSelected'}
        else:
            data = {'info': 'ProcessingImages'}

            #Download these images. Run Feature Extraction. Post results.
            uuid, image_path = downloadAndSaveImages(post_dict['urls'], post_dict['socketid'])

            output_path = os.path.join(image_path, 'results')
            print image_path
            print output_path
            print uuid
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            decaf_wrapper_local(image_path, output_path, post_dict['socketid'], os.path.join(conf.PIC_URL, uuid))
            log_to_terminal('Processing Images Now', post_dict['socketid'])

        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response
    except Exception as e:
        data = {'result': str(traceback.format_exc())}
        response = JSONResponse(data, {}, response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response
