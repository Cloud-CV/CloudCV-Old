import sys
path = '/home/ubuntu/cloudcv/cloudcv17'
sys.path.append(path)

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloudcv17.settings")

import subprocess
import json
import sqlite3
import re
import traceback
import os
import os.path
import redis
from app.log import log, log_to_terminal, log_error_to_terminal, log_and_exit
from app.executable import caffe_classify, decaf_cal_feature
from app.thirdparty import dropbox_upload as dbu
import app.conf as conf
import time
import envoy

from app.celery.celery.celery import celery

@celery.task
def add(x, y):
    return x + y


@celery.task
def saveDropboxFiles(job_dict):
    from app.thirdparty import ccv_dropbox
    ccv_dropbox.downloadFiles(job_dict)

os.environ['OMP_NUM_THREADS'] = '4'
r = redis.StrictRedis(host = '127.0.0.1', port=6379, db=0)
jobid = ''

import sys

class CustomPrint():
    def __init__(self, socketid):
        self.old_stdout=sys.stdout #save stdout
        self.socketid = socketid

    def write(self, text):
        r.publish('chat', json.dumps({'error': str(text), 'socketid': str(self.socketid)}))

def sendsMessageToRedis(userid, jobid, source_type, socketid, complete_output,
                        result_path=None, result_url=None, result_text=None, dropbox_token=None):
    #logger.write('P', 'Inside send message to redis')
    try:

        r.hset(jobid, 'output', str(complete_output))
        r.hset(jobid, 'socketid', str(socketid))

        if source_type != 'dropbox':
            if result_url is not None:
                r.hset(jobid, 'result_path', str(jobid) + '_resultdir')
                for file_name in os.listdir(result_path):
                    if os.path.isfile(os.path.join(result_path,file_name)):
                        r.lpush(str(jobid) + '_resultdir', os.path.join(result_url, str(file_name)))
            elif result_text is not None:
                r.hset(jobid, 'output', result_text)

        elif source_type == 'dropbox':
            f = open(result_path.rstrip('/') + '/output.txt', 'w')
            if complete_output is not None or complete_output is not '':
                f.write(str(complete_output))
            if result_text is not None:
                f.write(str(result_text))
            f.close()

            response, url = dbu.upload_files_to_dropbox(userid, jobid, result_path, dropbox_token)
            r.hset(jobid, 'output', str(response) + '\n' + str(url))
    except Exception as e:
        raise e

def run_matlab_code(mlab_inst, exec_path, task_args, socketid):
    customPrint = CustomPrint(socketid)
    old_stdout = sys.stdout
    sys.stdout = customPrint
    res = mlab_inst.run_func(exec_path, task_args)
    sys.stdout = old_stdout
    return str(res)

def run_executable(list, live=True, socketid=None):

    try:
        popen = subprocess.Popen(list, bufsize=1, stdin=open(os.devnull), stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        count = 0
        complete_output=''
        line = ''
        errline = ''



        while True:
            print 'inside while loop'
            if popen.poll() is not None:
                print 'exiting'
                break

            if popen.stdout:
                line = popen.stdout.readline()
                if live is True:
                    r.publish('chat', json.dumps({'error': str(line), 'socketid': socketid}))
                    print line
                popen.stdout.flush()

            if popen.stderr:
                errline = popen.stdout.readline()
                if live is True:
                    r.publish('chat', json.dumps({'error': str(errline), 'socketid': socketid}))
                    print errline
                popen.stderr.flush()

            if line:
                # print count, line, '\n'
                complete_output += str(line)
                count += 1

            if errline:
                # print count, errline, '\n'
                complete_output += str(errline)
                count += 1


        # conn.close()
        return ''
    except Exception as e:
        # conn.close()
        raise e

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


def createList(directory, parsed_dict):
    list_for_exec = list()
    try:
        if not os.path.exists(os.path.join(str(parsed_dict['result_path']), 'results')):
                os.makedirs(os.path.join(str(parsed_dict['result_path']), 'results'))
                os.chmod(os.path.join(str(parsed_dict['result_path']), 'results'), 0775)

        if parsed_dict['exec'] == 'ImageStitch':
            list_for_exec = [os.path.join(conf.EXEC_DIR,'stitch_full'), '--img',
                             os.path.join(str(parsed_dict['image_path'])), '--verbose', '1',
                             '--output', os.path.join(str(parsed_dict['result_path']),'results/')]

        elif parsed_dict['exec'] == 'VOCRelease5':
            list_for_exec = ['/var/www/html/cloudcv/voc-release5/PascalImagenetBboxPredictor/distrib/run_PascalImagenetBboxPredictor.sh',
                             '/usr/local/MATLAB/MATLAB_Compiler_Runtime/v81', str(parsed_dict['image_path']).rstrip('/'),
                             '/var/www/html/cloudcv/voc-release5/models/',
                             str(parsed_dict['result_path']).rstrip('/') + '/results/', str('6')]

            param_dict = parseParameters(parsed_dict['params'])
            list_for_exec.append(str(param_dict['Models']))

            dict_for_exec = {'input_path': str(parsed_dict['image_path']).rstrip('/'),
                             'model_dir': '/var/www/html/cloudcv/voc-release5/models/',
                             'output_path': str(parsed_dict['result_path']).rstrip('/') + '/results/',
                             'num_workers': str('6'),
                             'varargin': str(param_dict['Models'])
                             }
            return {'dict': dict_for_exec, 'flag': None}

        elif parsed_dict['exec'] == 'features':
            list_for_exec = ['/cloudcv/SUN_v2/code/scene_sun/run_extractFeat72.sh',
                             '/usr/local/MATLAB/MATLAB_Compiler_Runtime/v81',
                             str(parsed_dict['image_path']).rstrip('/'),
                             str(parsed_dict['result_path']).rstrip('/') + '/results/']
            dict_for_exec = {'imagePath': str(parsed_dict['image_path']).rstrip('/'),
                             'outputPath': str(parsed_dict['result_path']).rstrip('/') + '/results/'}
            param_dict = parseParameters(parsed_dict['params'])

            list_of_names = str(param_dict['name']).split(',')

            server = None
            if 'server' in param_dict:
                server = param_dict['server']

            flag = 0
            str_list_name = ''

            r.publish('chat', json.dumps({'error': list_of_names, 'socketid': parsed_dict['socketid']}))

            for name in list_of_names:
                if 'decaf_center' in name:
                    flag |= 2       # add decaf_center option
                    #list_of_names.remove('decaf_center')

                elif 'decaf' in name:
                    flag |= 1       # add decaf option
                    #list_of_names.remove('decaf')

                else:
                    str_list_name += str(name) + ','


            str_list_name = str_list_name.rstrip(',')

            dict_for_exec['featList'] = str_list_name

            r.set('liststr', str_list_name)
            r.set('flag', flag)
            list_for_exec.append(str_list_name)
            if 'verbose' in param_dict:
                list_for_exec.append(str(param_dict['verbose']))

            dict_for_exec['verbosity'] = str(param_dict['verbose'])


            return {'dict': dict_for_exec, 'flag': flag, 'server': server}

        r.lpush('list_for_exec', list_for_exec)
        return {'dict': list_for_exec, 'flag': None}

    except Exception as e:
        raise e


def run_classification(userid, jobid, image_path, socketid, token, source_type, result_path, db_token=None):
    # logger.write('P', 'Inside run_classification')

    message = 'Classification Complete'
    result = caffe_classify.caffe_classify(image_path)
    result = json.dumps(result)
    sendsMessageToRedis(userid, jobid, source_type, socketid, '', result_path=result_path, result_text=str(result),
                        dropbox_token=db_token)
    r.publish('chat', json.dumps({'done': str(message), 'socketid': str(socketid), 'token': token, 'jobid': jobid}))

def run_image_stitching(list, token, result_url, socketid, result_path, source_type):
   # logger.write('P', 'Inside Image Stitching')
    message = 'Image Stitching Completed'
    run_executable(list, token, result_url, socketid, message, result_path, source_type)


def run_voc_release(list, token, result_url, socketid, result_path, source_type):
    #logger.write('P', 'Inside run_voc_release')
    try:
        message = 'Bounding Box Generated'
        run_executable(list, token, result_url, socketid, message, result_path, source_type)
    except Exception as e:
        print str(e)+'\n'
       # logger.write('P', str(e))
        raise e

@celery.task
def run(parsed_dict):
    socketid = str(parsed_dict['socketid'])
    try:
        if 'dropbox_token' not in parsed_dict or parsed_dict['dropbox_token']=='None':
            parsed_dict['dropbox_token'] = None

        global jobid

        jobid = str(parsed_dict['jobid'])
        userid = str(parsed_dict['userid'])

        image_path = parsed_dict['image_path']
        result_path = str(parsed_dict['result_path'])

        list = None
        flag = None
        server = None

        dict_of_param = createList(image_path, parsed_dict)
        if 'dict' in dict_of_param:
            list = dict_of_param['dict']
        if 'flag' in dict_of_param:
            flag = dict_of_param['flag']
        if 'server' in dict_of_param:
            server = dict_of_param['server']

        log(list, "__main__")

        token = parsed_dict['token']

        result_url = os.path.join(parsed_dict['url'], 'results')
        result_path = os.path.join(result_path, 'results')
        source_type = parsed_dict['source_type']
        db_token = parsed_dict['dropbox_token']

        if parsed_dict['exec'] == 'ImageStitch':
            print "Image Stitching running"
            output = run_executable(list, True, socketid)
            sendsMessageToRedis(userid, jobid, source_type, socketid, output, result_path, result_url,
                                dropbox_token=db_token)
            r.publish('chat', json.dumps({'done': str('Image Stitching done'), 'socketid': str(socketid), 'token': token, 'jobid': jobid}))


        elif(parsed_dict['exec'] == 'VOCRelease5'):
            # output = run_executable(list)
            output = run_matlab_code(mlab_obj, '/var/www/html/cloudcv/voc-dpm-matlab-bridge/pascal_object_detection.m', list, parsed_dict['socketid'])
            sendsMessageToRedis(userid, jobid, source_type, socketid, output, result_path, result_url,
                                dropbox_token=db_token)
            r.publish('chat', json.dumps({'message': str('Bounding Boxes Generated'), 'socketid': str(socketid), 'token': token, 'jobid': jobid}))

        elif(parsed_dict['exec'] == 'classify'):
            run_classification(parsed_dict['userid'], parsed_dict['jobid'], parsed_dict['image_path'],
                               parsed_dict['socketid'], parsed_dict['token'], parsed_dict['source_type'],result_path,
                               db_token=db_token)

        elif(parsed_dict['exec'] == 'features'):
            print result_url
            tags = {}
            matlabfilepath = decaf_cal_feature.calculate_decaf(parsed_dict['image_path'], result_path,3,socketid, tags)
            sendsMessageToRedis(userid, jobid, source_type, socketid, '', result_path, result_url,
                                    dropbox_token=db_token)
            r.publish('chat', json.dumps({'done': str('Features Generated'),
                                          'socketid': str(socketid), 'token': token, 'jobid': jobid}))

    except Exception as e:
        log_and_exit(str(traceback.format_exc()), socketid)
