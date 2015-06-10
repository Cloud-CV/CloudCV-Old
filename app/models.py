# encoding: utf-8
from django.db import models
from django.core.validators import URLValidator

class User(models.Model):
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
    email_id = models.EmailField(max_length = 254, unique = True)
    first_name = models.CharField(max_length =100)
    last_name = models.CharField(max_length = 100)
    username = models.Charfield(, max_length = 50, unique = True)
    # The Next field represents the institution/company where the user belongs to.
    institution = models.Charfield(max_length = 500)
    last_login = models.DateTimeField()
    date_joined = models.DateTimeField()
    purpose = models.CharField(max_length = 2,
        choices = PURPOSE,
        default = EDUCATION)

    def __str__(self):
        return "%s %s %s %s %s" % (self.first_name, self.last_name, self.username, self.institution, self.purpose)

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
        (SUCESS, 'Successful')
        )
    user = models.ForeignKey(User)
    # The next field describes which of the two api (Python API or Matlab API) was used in the request.
    api_used = models.CharField(max_length = 3, 
        choices = API)
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
    parameters = models.ForeignKey(DictModel)
    duration = models.DateTimeField()
    #####################################################
    # ASK AHMED OR HARSH FOR THE NEXT FOUR FIELDS CLARIFICATIONS #
    #####################################################
    input_source_type = models.CharField()
    input_source_value = models.PositiveIntegerField()
    output_source_type = models.CharField()
    output_source_value = models.PositiveIntegerField()

class DictModel(models.Model):
    '''
    This model is used by the parameters column that acts as a container 
    and is used to easily store and process json data in django model.

    '''
    name = models.CharField(max_length=100)

class Group(models.Model):
    '''
    This table stores the information about the group of people who 
    are doing research/work using cloudcv and is used to monitor that 
    which group is researching over what.
    '''
    group_id = models.PositiveIntegerField()
    group_name = models.CharField(max_length = 100)
    purpose = models.Charfield()
    user = models.ForeignKey(User)

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
    This table is used to store the images on which different operations 
    are performed. 
    '''
    user = models.ForeignKey(User)
    category = models.CharField(max_length = 100)
    url = models.TextField(validators=[URLValidator()])
    