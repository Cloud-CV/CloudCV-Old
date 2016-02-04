__author__ = 'dexter'
from app.log import log, log_to_terminal, log_and_exit
from app.core.job import Job
from app.core import execute as core_execute

from PIL import Image
from StringIO import StringIO

import dropbox
import traceback
import ntpath
import sys
import os

path = '/home/ubuntu/cloudcv/cloudcv17'
sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloudcv17.settings")


def downloadFiles(job_dict):

    log_to_terminal('Dropbox Queue Handler: Downloading images', job_dict['socketid'])

    client = dropbox.client.DropboxClient(job_dict['dropbox_token'])
    try:
        folder_metadata = client.metadata(job_dict['dropbox_path'])
    except:
        log_and_exit('Path: ' + job_dict['dropbox_path'] + ' not found', job_dict['socketid'])
        return

    log(job_dict['dropbox_path'], downloadFiles.__name__)
    log(job_dict['dropbox_token'], downloadFiles.__name__)

    for content in folder_metadata['contents']:
        if content['is_dir'] is False and 'image' in str(content['mime_type']):
            file, file_metadata = client.get_file_and_metadata(content['path'])

            rel_path = ntpath.dirname(str(content['path'])).lstrip('/')
            log_to_terminal(os.path.join(job_dict['storage_path'], rel_path, ntpath.basename(content['path'])),
                            job_dict['socketid'])

            if not os.path.exists(os.path.join(job_dict['storage_path'], rel_path)):
                os.makedirs(os.path.join(job_dict['storage_path'], rel_path))
                os.chmod(os.path.join(job_dict['storage_path'], rel_path), 0775)

            img = Image.open(StringIO(file.read()))
            img.save(os.path.join(job_dict['storage_path'], rel_path,
                                  ntpath.basename(content['path'])),
                     file_metadata['mime_type'].split('/')[1])
    try:
        job_obj = Job()
        for k, v in job_dict.iteritems():
            setattr(job_obj, k, v)

        log(str(job_dict['storage_path'] + job_dict['dropbox_path'].strip('/')), 'directory')

        if job_obj.count is None or int(job_obj.count) <= 0:
            count = 0
            for name in os.listdir(os.path.join(job_dict['storage_path'], job_dict['dropbox_path'].strip('/'))):
                log(str(name), 'name')
                if os.path.isfile(os.path.join(job_dict['storage_path'], job_dict['dropbox_path'].strip('/'), name)):
                    count += 1
                    log(str(name), 'name')
            job_obj.count = count

        # log_to_terminal('JobID: ' + str(job_obj.jobid), job_obj.socketid)
        # log_to_terminal('Count: ' + str(job_obj.count), job_obj.socketid)

        core_execute.execute(job_obj, os.path.join(
            job_dict['storage_path'], job_dict['dropbox_path'].strip('/')), 'dropbox')
    except:
        print str(traceback.format_exc())
        log_and_exit(str(traceback.format_exc()), job_dict['socketid'])
