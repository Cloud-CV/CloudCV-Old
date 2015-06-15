#!/usr/bin/python\
# -*- coding: utf-8 -*-\
\
from caffe_classify import caffe_classify
import sys
print "Started test script"

#initialize the variables
ImagePath = "/cloudcv/Imagenet/Imagenet2013/trainImages/n02486410/n02486410_4168.JPEG"

#ImagePath= '/var/www/html/cloudcv/fileupload/media/pictures/67d4ce7c-7c44-11e3-bedb-00259059abc7/4/000084.jpg'
#Perform createDB
results=caffe_classify(ImagePath)
print results
