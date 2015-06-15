import subprocess
import json
import sqlite3
import re
import traceback
import os
import os.path
from pymatbridge import Matlab
import redis

from app.log import log
from app.log import Logger
from app.executable import caffe_classify
from app.thirdparty import dropbox_upload as dbu
import time

'''
path = '/var/www/html/cloudcv/fileupload'
if path not in sys.path:
    sys.path.append(path)
'''

os.environ['OMP_NUM_THREADS'] = '4'
'''
#------------------------------Initial Setup :- Argument Parser--------------------------
parser = argparse.ArgumentParser()
parser.add_argument("userid", type=str, help="UserID of the user")
parser.add_argument("jobid", type=str, help="JobID of the user")
parser.add_argument("image_path", type=str, help="ImagePath of the user")
parser.add_argument("result_path", type=str, help="ImagePath of the user")
parser.add_argument("-d", "--dir", type=str, help="Directory of Image Source")
parser.add_argument("-u", "--url", type=str, help="URL to Images")
parser.add_argument("-e", "--executable", type=str, help="Executable Name: \n1.) ImageStitch or \n 2.)VOCRelease5")
parser.add_argument("-c", "--count", type=str, help="Count")
parser.add_argument("-s", "--socketid", type=str, help="SocketId")
parser.add_argument("-t", "--token", type=str, help="Token")
parser.add_argument("-p", "--params", type=str, help="Parameters")
parser.add_argument("--source_type", type=str, help="Source Type")
parser.add_argument("--dropbox_token", type=str, help="Source Type")

args = parser.parse_args()
#----------------xxx-------------Argument Parser Code Ends---------------------xxx----------------------
'''
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
                        r.lpush(str(jobid) + '_resultdir', result_url + str(file_name))
            elif result_text is not None:
                r.hset(jobid, 'output', result_text)

        elif source_type == 'dropbox':
            f = open(result_path.rstrip('/') + '/output.txt', 'w')
            if complete_output is not None:
                f.write(str(complete_output))
            if result_text is not None:
                f.write(str(result_text))
            f.close()

            response, url = dbu.upload_files_to_dropbox(userid, jobid, result_path, dropbox_token)
            r.hset(jobid, 'output', str(response) + '\n' + str(url))
    except Exception as e:
        r.publish('chat', json.dumps({'error': str(traceback.format_exc()), 'socketid': str(socketid)}))
        raise e

def run_matlab_code(mlab_inst, exec_path, task_args, socketid):
    customPrint = CustomPrint(socketid)
    old_stdout = sys.stdout
    sys.stdout = customPrint
    res = mlab_inst.run_func(exec_path, task_args)
    sys.stdout = old_stdout
    return str(res)

def run_executable(list, live=None, socketid=None):
    #logger = Logger()
    #logger.open('P')[
    #logger.write('P','Starting Execution')
    #logger.close('P')
    conn = sqlite3.connect('/var/www/html/cloudcv/db/message.db')
    c = conn.cursor()

    try:
        popen = subprocess.Popen(list, bufsize=1, stdin=open(os.devnull), stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

        count = 0
        complete_output=''
        line = ''
        errline = ''

        r.publish('chat', json.dumps({'error': str(popen.pid), 'socketid': socketid}))
        #popen.communicate()
        #p = Popen(cmd, bufsize=1, stdin=open(os.devnull), stdout=PIPE, stderr=STDOUT)
        lines = []

        while True:
            if popen.stdout:
                line = popen.stdout.readlines(10)
                if live is True:
                    r.publish('chat', json.dumps({'error': str(line), 'socketid': socketid}))
                popen.stdout.flush()

            if popen.stderr:
                errline = popen.stdout.readlines(10)
                if live is True:
                    r.publish('chat', json.dumps({'error': str(errline), 'socketid': socketid}))
                popen.stderr.flush()

            if line:
                #print count, line, '\n'
                complete_output += str(line)
                count += 1

            if errline:
                #print count, errline, '\n'
                complete_output += str(errline)
                count += 1
            if popen.poll() is not None:
                break
            else:
                r.publish('chat', json.dumps({'error': str(popen.poll()), 'socketid': socketid}))

        return complete_output
    except Exception as e:
        raise e

    conn.close()

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
        if not os.path.exists(str(parsed_dict['result_path']).rstrip('/') + '/results'):
                os.makedirs(str(parsed_dict['result_path']).rstrip('/') + '/results')
                os.chmod(str(parsed_dict['result_path']).rstrip('/') + '/results', 0776)

        if parsed_dict['exec'] == 'ImageStitch':
            list_for_exec = ['/var/www/html/cloudcv/fileupload/executable/stitch_full', '--img',
                             str(parsed_dict['image_path']).rstrip('/') + '/', '--verbose', '1',
                             '--output', str(parsed_dict['result_path']).rstrip('/') + '/results/',
                             '--ncpus', str(min(parsed_dict['count'], 20)), '--warp']

            param_dict = parseParameters(parsed_dict['params'])
            list_for_exec.append(str(param_dict['warp']))

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
            list_for_exec.append(str(param_dict['verbose']))

            dict_for_exec['verbosity'] = str(param_dict['verbose'])


            return {'dict': dict_for_exec, 'flag': flag, 'server': server}

        r.lpush('list_for_exec', list_for_exec)
        return {'dict': list_for_exec, 'flag': None}

    except Exception as e:
        r.lpush('list_for_exec', str(e))
        raise e


def run_classification(userid, jobid, image_path, socketid, token, source_type, result_path, db_token=None):
    #logger.write('P', 'Inside run_classification')
    message = 'Classification Complete'
    result = caffe_classify.caffe_classify(image_path)
    result = json.dumps(result)
    sendsMessageToRedis(userid, jobid, source_type, socketid, message, result_path=result_path, result_text=str(result), dropbox_token=db_token)
    r.publish('chat', json.dumps({'message': str(message), 'socketid': str(socketid), 'token': token, 'jobid': jobid}))


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
'''
def parseArguments(a):
    i = 0
    parsed_dict = {}
    parsed_dict['userid'] = a['userid']
    parsed_dict['jobid'] = a['jobid']
    parsed_dict['image_path'] = a['image_path']
    parsed_dict['result_path'] = a['result_path']

    if 'dir' in a:
        parsed_dict['dir'] = a['dir']
    if 'url' in a:
        parsed_dict['url'] = a['url']
    if 'executable' in a:
        parsed_dict['exec'] = a['executable']
    if 'count' in a:
        parsed_dict['count'] = a['count']
    if 'socketid' in a:
        parsed_dict['socketid'] = a['socketid']
    if 'token' in a:
        parsed_dict['token'] = a['token']
    if 'params' in a:
        parsed_dict['params'] = a['params']
    if 'source_type' in a:
        parsed_dict['source_type'] = a['source_type']
    if 'dropbox_token' in a and a['dropbox_token'] != 'None':
        parsed_dict['dropbox_token'] = a['dropbox_token']
    else:
        parsed_dict['dropbox_token'] = None
    return parsed_dict
'''

'''
 Experimental. Use with Utmost Caution.
'''

def run(parsed_dict, mlab_obj):

    try:
        if 'dropbox_token' not in parsed_dict or parsed_dict['dropbox_token']=='None':
            parsed_dict['dropbox_token'] = None

        global jobid

        jobid = str(parsed_dict['jobid'])
        userid = str(parsed_dict['userid'])
        socketid = str(parsed_dict['socketid'])
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
        result_url = parsed_dict['url'] + '/results/'
        result_path += '/results'
        source_type = parsed_dict['source_type']
        db_token = parsed_dict['dropbox_token']

        r.publish('chat', json.dumps({'error': str(parsed_dict), 'socketid': parsed_dict['socketid']}))

        if parsed_dict['exec'] == 'ImageStitch':
            output = run_executable(list)
            sendsMessageToRedis(userid, jobid, source_type, socketid, output, result_path, result_url,
                                dropbox_token=db_token)
            r.publish('chat', json.dumps({'message': str('Image Stitching done'), 'socketid': str(socketid), 'token': token, 'jobid': jobid}))


        elif(parsed_dict['exec'] == 'VOCRelease5'):
            #output = run_executable(list)
            output = run_matlab_code(mlab_obj, '/var/www/html/cloudcv/voc-dpm-matlab-bridge/pascal_object_detection.m', list, parsed_dict['socketid'])
            sendsMessageToRedis(userid, jobid, source_type, socketid, output, result_path, result_url,
                                dropbox_token=db_token)
            r.publish('chat', json.dumps({'message': str('Bounding Boxes Generated'), 'socketid': str(socketid), 'token': token, 'jobid': jobid}))

        elif(parsed_dict['exec'] == 'classify'):
            run_classification(parsed_dict['userid'], parsed_dict['jobid'], parsed_dict['image_path'],
                               parsed_dict['socketid'], parsed_dict['token'], parsed_dict['source_type'],result_path,
                               db_token=db_token)

        elif(parsed_dict['exec'] == 'features'):
            if server == 'decaf_server':
                r.publish('chat', json.dumps({'error': str('Starting Feature Generation'), 'socketid': str(socketid)}))
                r.publish('decaf_server_queue', json.dumps({'dir': parsed_dict['image_path'], 'flag': flag, 'socketid': parsed_dict['socketid'], 'jobid': str(jobid)}))

                while(True):
                    if r.hget(jobid, 'status') == 'done':
                        r.publish('chat', json.dumps({'error': str('Status: Done'), 'socketid': str(socketid)}))
                        sendsMessageToRedis(userid, jobid, source_type, socketid, '', result_path, result_url,
                                    dropbox_token=db_token)
                        r.publish('chat', json.dumps({'message': str('Features Generated'), 'socketid': str(socketid), 'token': token, 'jobid': jobid}))
                        break
                    else:
                        r.publish('chat', json.dumps({'error': str('Status: Still Running'), 'socketid': str(socketid)}))
                        print "Status not yet set"
                        log('Status not yet set', '__main__')
                        time.sleep(2)

            else:
                r.publish('chat', json.dumps({'error': str('Not decaf_server'), 'socketid': str(socketid)}))
                output = ''
                if(list['featList'] != ''):
                    #output += run_executable(list) + '\n'
                    output += run_matlab_code(mlab_obj, '/cloudcv/SUN_py/code/scene_sun/extractFeatPy.m', list, parsed_dict['socketid'])
                list_decaf = ['python', '/var/www/html/cloudcv/fileupload/executable/decaf_cal_feature.py', image_path, result_path, str(flag), parsed_dict['socketid']]
                output += run_executable(list_decaf, live=False, socketid=parsed_dict['socketid'])
                sendsMessageToRedis(userid, jobid, source_type, socketid, output, result_path, result_url,
                                    dropbox_token=db_token)
                r.publish('chat', json.dumps({'message': str('Features Generated'), 'socketid': str(socketid), 'token': token, 'jobid': jobid}))

    except Exception as e:
        print str(e)
        log(e, '__main__')
        r.publish('chat', json.dumps({'error': str(traceback.format_exc()), 'socketid': parsed_dict['socketid']}))



'''Experimental Section Ends'''

'''
def parseCommandLineArgs():
    i = 0
    parsed_dict = {}
    parsed_dict['userid'] = args.userid
    parsed_dict['jobid'] = args.jobid
    parsed_dict['image_path'] = args.image_path
    parsed_dict['result_path'] = args.result_path

    if args.dir:
        parsed_dict['dir'] = args.dir
    if args.url:
        parsed_dict['url'] = args.url
    if args.executable:
        parsed_dict['exec'] = args.executable
    if args.count:
        parsed_dict['count'] = args.count
    if args.socketid:
        parsed_dict['socketid'] = args.socketid
    if args.token:
        parsed_dict['token'] = args.token
    if args.params:
        parsed_dict['params'] = args.params
    if args.source_type:
        parsed_dict['source_type'] = args.source_type
    if args.dropbox_token and args.dropbox_token != 'None':
        parsed_dict['dropbox_token'] = args.dropbox_token
    else:
        parsed_dict['dropbox_token'] = None
    return parsed_dict

if __name__ == "__main__":
    logger.write('P', 'in run_executable.py')

    try:
        parsed_dict = parseCommandLineArgs()
        global jobid

        jobid = str(parsed_dict['jobid'])
        userid = str(parsed_dict['userid'])
        socketid = str(parsed_dict['socketid'])
        image_path = parsed_dict['image_path']
        result_path = str(parsed_dict['result_path'])

        list, flag = createList(image_path, parsed_dict)

        log(list, "__main__")
        logger.write('P', str(list))
        logger.write('P', str(parsed_dict))

        token = parsed_dict['token']
        result_url = parsed_dict['url'] + '/results/'
        result_path += '/results'
        source_type = parsed_dict['source_type']
        db_token = parsed_dict['dropbox_token']

        r.publish('chat', json.dumps({'error': str(parsed_dict), 'socketid': parsed_dict['socketid']}))

        if parsed_dict['exec'] == 'ImageStitch':
            output = run_executable(list)
            sendsMessageToRedis(userid, jobid, source_type, socketid, output, result_path, result_url,
                                dropbox_token=db_token)
            r.publish('chat', json.dumps({'message': str('Image Stitching done'), 'socketid': str(socketid), 'token': token, 'jobid': jobid}))


        elif(parsed_dict['exec'] == 'VOCRelease5'):
            output = run_executable(list)
            sendsMessageToRedis(userid, jobid, source_type, socketid, output, result_path, result_url,
                                dropbox_token=db_token)
            r.publish('chat', json.dumps({'message': str('Bounding Boxes Generated'), 'socketid': str(socketid), 'token': token, 'jobid': jobid}))

        elif(parsed_dict['exec'] == 'classify'):
            run_classification(parsed_dict['userid'], parsed_dict['jobid'], parsed_dict['image_path'],
                               parsed_dict['socketid'], parsed_dict['token'], parsed_dict['source_type'],result_path,
                               db_token=db_token)

        elif(parsed_dict['exec'] == 'features'):
            output = ''
            if(list[-2] != ''):
                output += run_executable(list) + '\n'
            list_decaf = ['python', '/var/www/html/cloudcv/fileupload/executable/decaf_cal_feature.py', image_path, result_path, str(flag), parsed_dict['socketid']]
            output += run_executable(list_decaf, live=False, socketid=parsed_dict['socketid'])
            sendsMessageToRedis(userid, jobid, source_type, socketid, output, result_path, result_url,
                                dropbox_token=db_token)
            r.publish('chat', json.dumps({'message': str('Features Generated'), 'socketid': str(socketid), 'token': token, 'jobid': jobid}))



    except Exception as e:
        print e
        log(e, '__main__')
        logger = Logger()
        logger.open('E')
        logger.write('E', str(traceback.format_exc()))
        logger.close('E')
        r.publish('chat', json.dumps({'error': str(traceback.format_exc()), 'socketid': parsed_dict['socketid']}))

    logger.close('P')
'''

