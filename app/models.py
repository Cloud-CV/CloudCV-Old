# encoding: utf-8
'''
Author: Deshraj
'''
from django.db import models
from django.core.validators import URLValidator
from jsonfield import JSONField
from django.contrib.auth.models import User
from organizations.models import Organization

class UserDetails(models.Model):
    '''
    It stores the information about the cloudcv users who sign up on CloudCV.
    '''
    # The next four variables represents the choices for the Purpose field
    EDUCATION = 'ED'
    RESERACH = 'RE'
    BUSINESS = 'BU'
    OTHERS = 'OT'
    PURPOSE = (
        (EDUCATION, 'Education'),
        (RESERACH,'Research'),
        (BUSINESS,'Business'),
        (OTHERS,'Others'),
        )
    user = models.OneToOneField(User)
    institution = models.CharField(max_length = 500)
    purpose = models.CharField(max_length = 2,
        choices = PURPOSE,
        default = EDUCATION)

    def __str__(self):
        return "%s %s" % ( self.institution, self.purpose)

class ModelStorage(models.Model):
    """
    To store the Models that are being used by the different User Groups. 
    """
    file_location = models.CharField(max_length = 1000)   # next field defines the parameters that are used
    parameters = JSONField()                   # the parameters can be many. So, they are stored in the json format 
    neural_network = models.CharField(max_length = 1000)  # it defines the location of the .prototxt file for the particular model.
    database_used = models.CharField(max_length = 1000)   # it defines the location of the .prototxt file for the particular database.

class RequestLog(models.Model):
    '''
    It stores information about the number of job submissions on CloudCV. 
    '''
    PYTHON = 'PY'
    MATLAB = 'MAT'
    API = (
        (PYTHON, 'Python'),
        (MATLAB, 'Matlab'),
        )
    # The next four fields are choices for the processing state column 
    START = 'STR'
    RUNNING = 'RUN'
    ERROR = 'ERR'
    SUCCESS  = 'SUC'
    PROCESSING_STATE= (
        (START, 'Starting State'),
        (RUNNING, 'In Progress'),
        (ERROR, 'Error State'),
        (SUCCESS, 'Successful')
        )
    user = models.ForeignKey(User)
    api_used = models.CharField(max_length = 3, 
        choices = API)  # describes which of the two api (Python API or Matlab API) was used in the request.
    processing_state = models.CharField(max_length = 3,
        choices = PROCESSING_STATE,
        default = START)
    job_id = models.CharField(max_length = 100)
    no_of_images = models.PositiveIntegerField()
   '''
    for the next field, the data comes in the form on json data. So, 
    DictModel is used for storing the json data. 
    See the link : http://stackoverflow.com/questions/402217/how-to-store-a-dictionary-on-a-django-model
    for more clarification 
    '''
    parameters = JSONField()
    duration = models.DateTimeField()
    input_source_type = models.CharField(max_length = 100)
    input_source_value = models.PositiveIntegerField()
    output_source_type = models.CharField(max_length = 100)
    output_source_value = models.PositiveIntegerField()

# class Group(models.Model):
#     '''
#     This table stores the information about the group of people who 
#     are doing research/work using cloudcv and is used to monitor that 
#     which group is researching over what.
#     '''
#     model = models.ForeignKey(ModelStorage)
#     group_id = models.PositiveIntegerField()
#     group_name = models.CharField(max_length = 100)
#     purpose = models.CharField(max_length = 100)
#     user = models.ForeignKey(User)

class CurrentRequest(models.Model):
    '''
    To track the realtime RAM usage, Memory usage, CPU usage etc for 
    the current running jobs.
    '''
    user = models.ForeignKey(User)
    ram_usage = models.FloatField()
    cpu_usage = models.FloatField()
    disk_space_usage = models.FloatField()
    no_of_jobs_running = models.PositiveIntegerField()

class Images(models.Model):
    '''
    To store the images on which different operations 
    are performed. 
    '''
    user = models.ForeignKey(User)
    category = models.CharField(max_length = 100)
    url = models.TextField(validators=[URLValidator()])

class StorageCredentials(models.Model):
    user  = models.ForeignKey(User)
    aws_access_key = models.CharField(max_length = 100)
    aws_access_secret = models.CharField(max_length = 100)

class Job(models.Model):
    job_id = models.CharField(max_length = 100)
    workspace = models.ForeignKey(Organization)

class Classify(models.Model):

    # This is a small demo using just two fields. The slug field is really not
    # necessary, but makes the code simpler. ImageField depends on PIL or
    # pillow (where Pillow is easily installable in a virtualenv. If you have
    # problems installing pillow, use a more generic FileField instead.

    #file = models.FileField(upload_to="pictures")
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

    #file = models.FileField(upload_to="pictures")
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
        return ('upload-new', )

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

    #file = models.FileField(upload_to="pictures")
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

    #file = models.FileField(upload_to="pictures")
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

    #file = models.FileField(upload_to="pictures")
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
