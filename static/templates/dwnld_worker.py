#!/usr/bin/python

import threading
import dropbox
import redis
import time
from PIL import Image
from StringIO import StringIO
import ntpath
import os, subprocess
import traceback
import json


prefix_path = '/home/azureuser/cloudcv/jobs/'
'''
def post_to_twitter():
    #redis_obj = redis.StrictRedis(host = '0.0.0.0', port=6379, db=0)
    #twt_count = int(redis_obj.get("twitter_count"))
    #twt_count += 1
    consumer_key = '6cWYSdMzaKZ2J3VuFKU9X4OMF'
    consumer_secret = 'W9dOx543yjIMHSCtlr1dvlocRP1Lx1hkzQ2jJ6rW0u4g2kGhkX'
    user_token = '1837282207-9xLaKjnwcvyH76zddoU6h3icthCL1ZsaDEQlAEM'
    user_secret = 'VFDSfbCIvhTYVaQdroRuhR9vK3uhvIZxb8iu1iTZdfT5t'
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(user_token, user_secret)
    api = tweepy.API(auth)
    public_tweets = api.home_timeline()
    for tweet in public_tweets:
        print tweet.text
'''
class Dwnld_Worker(threading.Thread):
    token = ''
    path = ''
    uuid = ''

    def __init__(self, id):
        threading.Thread.__init__(self)
        self.id = id
        self.olduuid = ''

        while(True):
            try:
                self.redis_obj = redis.StrictRedis(host = 'mlpmasternode.cloudapp.net', port=6379, db=0)
                break
            except Exception as e:
                print "Error in Connection. "
        print "Thread Created", id

    def run_executable(self, path, output_path):
        list_for_exec = ['/opt/software/voc-release5/PascalImagenetBboxPredictor/distrib/run_PascalImagenetBboxPredictor.sh',
                         '/usr/local/MATLAB/MATLAB_Compiler_Runtime/v81',
                         path,
                         '/opt/software/voc-release5/models/',
                         output_path,
                         '4',
                         'PAS_aeroplane']
        popen = subprocess.Popen(list_for_exec, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        count = 0

        complete_output=''
        line = ''
        errline = ''

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

        print 'Done Running the exectuable'

    def uploadToDB(self, token, result_path, file_name, subdir):
        print "Uploading to Dropbox"
        client = dropbox.client.DropboxClient(token)
        try:
            client.file_create_folder('/' + str('Azure_Results'))
        except Exception as e:
            print 'Folder Already Made'
        try:
            client.file_create_folder('/' + str('Azure_results') + '/' + subdir)
        except Exception as e:
            print 'Folder Already Made'

        #for file_name in os.listdir(result_path):
        #    if os.path.isfile(os.path.join(result_path, file_name)):
        print os.path.join(result_path, file_name + '.mat')
        f = open(os.path.join(result_path, file_name + '.mat'), 'rb')
        client.put_file('/' + str('Azure_results') + '/' + subdir + '/' + file_name +'.mat', f)
        f.close()

    def run(self):
        while(True):
            try:
                popstr = self.redis_obj.rpop("image_path")
                if popstr is None:

                    continue
                json_dict = json.loads(popstr)
                print json_dict


                self.path = json_dict['path']
                self.token = json_dict['token']
                self.uuid = json_dict['uuid']

                if self.path is not None and self.token is not None and self.uuid is not None:
                    client = dropbox.client.DropboxClient(self.token)
                    file, file_metadata = client.get_file_and_metadata(self.path)
                    img = Image.open(StringIO(file.read()))

                    if not os.path.exists(prefix_path + str(self.uuid)):
                        os.makedirs(prefix_path + str(self.uuid))
                        os.chmod(prefix_path + str(self.uuid), 0776)
                        os.makedirs(prefix_path + str(self.uuid) + '/input')
                        os.chmod(prefix_path + str(self.uuid) + '/input', 0776)
                        os.makedirs(prefix_path + str(self.uuid) + '/output')
                        os.chmod(prefix_path + str(self.uuid) + '/output', 0776)

                    input_path = prefix_path + str(self.uuid) + '/input'
                    output_path = prefix_path + str(self.uuid) + '/output'
                    file_name = ntpath.basename(self.path)

                    img.save(prefix_path + str(self.uuid) + '/input/' + file_name, file_metadata['mime_type'].split('/')[1])


                    print str(self.id) + ": Image Saved. Executable Started"

                    self.run_executable(input_path, output_path + '/')
                    self.uploadToDB(self.token, output_path, file_name, str(self.uuid))
                    print str(self.id) + ": Uploaded to Dropbox"
                else:
                    time.sleep(10)
                    print "Sleeping for 10 seconds"
            except Exception as e:
                print str(e)
                print traceback.format_exc()


worker = Dwnld_Worker('1')
worker.start()

'''
post_to_twitter()
'''