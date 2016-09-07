from django.conf import settings

import boto3
import botocore
import os

s3 = boto3.resource('s3')
bucket = s3.Bucket('VqaImages')
exists = True

try:
    s3.meta.client.head_bucket(Bucket='VqaImages')
except botocore.exceptions.ClientError as e:
    error_code = int(e.response['Error']['Code'])
    if error_code == 404:
        s3.create_bucket(Bucket='VqaImages')
        s3.create_bucket(Bucket='VqaImages', CreateBucketConfiguration={'LocationConstraint': 'us-west-1'})

dir_name = os.path.join(settings.MEDIA_ROOT, 'pictures')
media_images = os.listdir(dir_name)

for image in media_images:
    try:
        abs_image_path = os.path.join(dir_name, image)
        image_name = str(image).split("/")[-1]
        s3.Object('VqaImages', image_name).put(Body=open(str(abs_image_path), 'rb'))
        os.remove(abs_image_path)        
        print "File %s pushed successfully on S3" %(image_name, )
    except Exception as e:
        print str(e)
