__author__ = 'parallels'
import os

import sys
path = '/home/ubuntu/cloudcv/cloudcv_gsoc'
sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloudcv17.settings")

from django.conf import settings

# user
USER = 'ubuntu'
# directory where all pictures reside
PIC_DIR = os.path.join(settings.MEDIA_ROOT, 'pictures', 'cloudcv')


# directory for classification job related stuff.
LOCAL_CLASSIFY_JOB_DIR = os.path.join(settings.MEDIA_ROOT, 'pictures', 'classify')
if not os.path.exists(LOCAL_CLASSIFY_JOB_DIR):
    os.makedirs(LOCAL_CLASSIFY_JOB_DIR)

# directory for classification demo images
LOCAL_DEMO_PIC_DIR = os.path.join(settings.MEDIA_ROOT,'pictures', 'demo')

# directory for classification demo images
LOCAL_DEMO_POI_PIC_DIR = os.path.join(settings.MEDIA_ROOT,'pictures', 'poiDemo')

# directory for imagestitch demo images
LOCAL_DEMO1_PIC_DIR = os.path.join(settings.MEDIA_ROOT,'pictures', 'demo1')

# directory where all the executables reside
EXEC_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'executable')

# PIC_URL
PIC_URL = '/media/pictures/cloudcv/'

# CAFFE DIRECTORY
CAFFE_DIR = '/home'+'/ubuntu/' + 'caffe'
LOG_DIR = os.path.join(settings.BASE_ABS_DIR, 'logs')
