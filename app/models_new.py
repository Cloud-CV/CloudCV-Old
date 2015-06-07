# encoding: utf-8
from django.db import models
from oauth2client.django_orm import CredentialsField
from oauth2client.django_orm import FlowField


class CloudCV_User(models.Model):
    # For more refrence, you can check the link https://docs.djangoproject.com/en/1.8/ref/contrib/auth/#django.contrib.auth.models.User
    first_name = models.CharField(max_length = 20)
    last_name = models.CharField(max_length = 20)
    username = models.CharField(max_length = 100, primary_key=True)
    email = models.EmailField(max_length = 254, unique=True)
    is_active = models.BooleanField()
    password = models.CharField(max_length = 100)
    last_login = models.DateTimeField()
    date_joined = models.DateTimeField()
    is_superuser = models.BooleanField()


class RequestLog(models.Model):
    cloudcv_user = models.ForeignKey(CloudCV_User) 
    jobid = models.CharField(max_length=100)
    noOfImg = models.IntegerField()
    function = models.CharField(max_length=50)
    dateTime = models.DateTimeField()
    isDropbox = models.BooleanField()
    apiName =models.CharField(max_length=20, null=True)


class Picture(models.Model):
    cloudcv_user = models.ForeignKey(CloudCV_User) 
    file = models.ImageField(upload_to="pictures")
    slug = models.SlugField(max_length=50, blank=True)
    dateTime = models.DateTimeField()


class Decaf(models.Model):
    cloudcv_user = models.ForeignKey(CloudCV_User) 
    file = models.ImageField(upload_to="pictures")
    slug = models.SlugField(max_length=50, blank=True)
    dateTime = models.DateTimeField()


class Decafmodel(models.Model):
    cloudcv_user = models.ForeignKey(CloudCV_User) 
    file = models.ImageField(upload_to="pictures")
    slug = models.SlugField(max_length=50, blank=True)
    dateTime = models.DateTimeField()
    status = models.BooleanField()
    

class Trainaclass(models.Model):
    cloudcv_user = models.ForeignKey(CloudCV_User) 
    file = models.ImageField(upload_to="pictures")
    slug = models.SlugField(max_length=50, blank=True)
    dateTime = models.DateTimeField()
    status = models.BooleanField()


class Classify(models.Model):
    cloudcv_user = models.ForeignKey(CloudCV_User) 
    file = models.ImageField(upload_to="pictures")
    slug = models.SlugField(max_length=50, blank=True)
    dateTime = models.DateTimeField()
    status = models.BooleanField()

class Poi(models.Model):
    cloudcv_user = models.ForeignKey(CloudCV_User) 
    file = models.ImageField(upload_to="pictures")
    slug = models.SlugField(max_length=50, blank=True)
    dateTime = models.DateTimeField()


# class CloudCV_Users(models.Model):
#     first_name = models.CharField(max_length = 20)
#     last_name = models.CharField(max_length = 20)
#     userid = models.CharField(max_length = 100, primary_key=True)
#     emailid = models.EmailField(max_length = 254, unique=True)
#     is_active = models.BooleanField()

# class GoogleAccountInfo(models.Model):
#     """
#     Should be replaced with models of Python-social auth

#     """
#     cloudcvid = models.ForeignKey(CloudCV_Users, unique = True)
#     credential = CredentialsField()
#     flow = FlowField()

# class DropboxAccount(models.Model):
#     """
#     Should be replaced with models of Python-social auth
    
#     """
#     cloudcvid = models.ForeignKey(CloudCV_Users, unique = True)
#     access_token = models.CharField(max_length=100, null=False)





    # def __unicode__(self):
    #     return self.file.name

    # @models.permalink
    # def get_absolute_url(self):
    #     return ('decaf', )

    # def save(self, *args, **kwargs):
    #     self.slug = self.file.name
    #     super(Decafmodel, self).save(*args, **kwargs)

    # def delete(self, *args, **kwargs):
    #     self.file.delete(False)
    #     super(Decafmodel, self).delete(*args, **kwargs)