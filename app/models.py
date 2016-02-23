# encoding: utf-8
from django.db import models

from oauth2client.django_orm import CredentialsField
from oauth2client.django_orm import FlowField


class Picture(models.Model):
    """This is a small demo using just two fields. The slug field is really not
    necessary, but makes the code simpler. ImageField depends on PIL or
    pillow (where Pillow is easily installable in a virtualenv. If you have
    problems installing pillow, use a more generic FileField instead.

    """
    file = models.ImageField(upload_to="pictures")
    slug = models.SlugField(max_length=50, blank=True)

    def __unicode__(self):
        return self.file.name

    @models.permalink
    def get_absolute_url(self):
        return ('image-stitching', )

    def save(self, *args, **kwargs):
        self.slug = self.file.name
        super(Picture, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """delete -- Remove to leave file."""
        self.file.delete(False)
        super(Picture, self).delete(*args, **kwargs)


class Decaf(models.Model):

    # This is a small demo using just two fields. The slug field is really not
    # necessary, but makes the code simpler. ImageField depends on PIL or
    # pillow (where Pillow is easily installable in a virtualenv. If you have
    # problems installing pillow, use a more generic FileField instead.

    # file = models.FileField(upload_to="pictures")
    file = models.ImageField(upload_to="pictures")
    slug = models.SlugField(max_length=50, blank=True)

    def __unicode__(self):
        return self.file.name

    @models.permalink
    def get_absolute_url(self):
        return ('decaf', )

    def save(self, *args, **kwargs):
        self.slug = self.file.name
        super(Decaf, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.file.delete(False)
        super(Decaf, self).delete(*args, **kwargs)


class Decafmodel(models.Model):

    # This is a small demo using just two fields. The slug field is really not
    # necessary, but makes the code simpler. ImageField depends on PIL or
    # pillow (where Pillow is easily installable in a virtualenv. If you have
    # problems installing pillow, use a more generic FileField instead.

    # file = models.FileField(upload_to="pictures")
    file = models.ImageField(upload_to="pictures")
    slug = models.SlugField(max_length=50, blank=True)

    def __unicode__(self):
        return self.file.name

    @models.permalink
    def get_absolute_url(self):
        return ('decaf', )

    def save(self, *args, **kwargs):
        self.slug = self.file.name
        super(Decafmodel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.file.delete(False)
        super(Decafmodel, self).delete(*args, **kwargs)


class Trainaclass(models.Model):

    # This is a small demo using just two fields. The slug field is really not
    # necessary, but makes the code simpler. ImageField depends on PIL or
    # pillow (where Pillow is easily installable in a virtualenv. If you have
    # problems installing pillow, use a more generic FileField instead.

    # file = models.FileField(upload_to="pictures")
    file = models.ImageField(upload_to="pictures")
    slug = models.SlugField(max_length=50, blank=True)

    def __unicode__(self):
        return self.file.name

    @models.permalink
    def get_absolute_url(self):
        return ('trainaclass', )

    def save(self, *args, **kwargs):
        self.slug = self.file.name
        super(Trainaclass, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.file.delete(False)
        super(Trainaclass, self).delete(*args, **kwargs)


class Classify(models.Model):

    # This is a small demo using just two fields. The slug field is really not
    # necessary, but makes the code simpler. ImageField depends on PIL or
    # pillow (where Pillow is easily installable in a virtualenv. If you have
    # problems installing pillow, use a more generic FileField instead.

    # file = models.FileField(upload_to="pictures")
    file = models.ImageField(upload_to="pictures")
    slug = models.SlugField(max_length=50, blank=True)

    def __unicode__(self):
        return self.file.name

    @models.permalink
    def get_absolute_url(self):
        return ('classify', )

    def save(self, *args, **kwargs):
        self.slug = self.file.name
        super(Classify, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.file.delete(False)
        super(Classify, self).delete(*args, **kwargs)


class Poi(models.Model):

    # This is a small demo using just two fields. The slug field is really not
    # necessary, but makes the code simpler. ImageField depends on PIL or
    # pillow (where Pillow is easily installable in a virtualenv. If you have
    # problems installing pillow, use a more generic FileField instead.

    # file = models.FileField(upload_to="pictures")
    file = models.ImageField(upload_to="pictures")
    slug = models.SlugField(max_length=50, blank=True)

    def __unicode__(self):
        return self.file.name

    @models.permalink
    def get_absolute_url(self):
        return ('poi', )

    def save(self, *args, **kwargs):
        self.slug = self.file.name
        super(Poi, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.file.delete(False)
        super(Poi, self).delete(*args, **kwargs)


class CloudCV_Users(models.Model):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    userid = models.CharField(max_length=100, primary_key=True)
    emailid = models.EmailField(max_length=254, unique=True)
    is_active = models.BooleanField(default=False)


class GoogleAccountInfo(models.Model):
    cloudcvid = models.ForeignKey(CloudCV_Users, unique=True)
    credential = CredentialsField()
    flow = FlowField()


class DropboxAccount(models.Model):
    cloudcvid = models.ForeignKey(CloudCV_Users, unique=True)
    access_token = models.CharField(max_length=100, null=False)


class RequestLog(models.Model):
    cloudcvid = models.CharField(max_length=100, null=False)
    jobid = models.CharField(max_length=100)
    noOfImg = models.IntegerField()
    function = models.CharField(max_length=50)
    dateTime = models.DateTimeField()
    isDropbox = models.BooleanField(default=False)
    apiName = models.CharField(max_length=20, null=True)
