__author__ = 'dexter'

import dropbox
import os
import sys

path = os.environ.get('CLOUDCVPATH')
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


def upload_files_to_dropbox(userid, jobid, result_path, dropbox_token=None):
    try:
        response = ''
        if dropbox_token is not None:
            client = dropbox.client.DropboxClient(dropbox_token)
            try:
                client.file_create_folder('/jobs')
            except:
                print 'Error Response'

            client.file_create_folder('/jobs/' + str(jobid))
            for file_name in os.listdir(result_path):
                if os.path.isfile(os.path.join(result_path, file_name)):
                    response += os.path.join(result_path, file_name)
                    response += '\n'
                    f = open(os.path.join(result_path, file_name), 'rb')
                    client.put_file('/jobs/' + str(jobid) + '/' + file_name, f)
                    f.close()

            response += 'Output have been stored in your dropbox folder.'
            url = 'http://www.dropbox.com/home/Apps/CloudCV/jobs/' + str(jobid)
            return response, url
        else:
            return 'dropbox token not mentioned'
    except Exception as e:
        raise e
