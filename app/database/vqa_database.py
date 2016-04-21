from peewee import *
import datetime

from playhouse.pool import PooledPostgresqlExtDatabase

psql_db = PooledPostgresqlExtDatabase(
    'cloudcv',
    max_connections=8,
    stale_timeout=1800,
    user='ubuntu')
class BaseModel(Model):
    """A base model that will use our Postgresql database"""
    class Meta:
        database = psql_db

class VQA_Question(BaseModel):
    socketid = CharField(unique=True)
    created_data = DateTimeField(default=datetime.datetime.now)
    questionText = TextField()
    imageName = CharField()
    imagePath = CharField()	

class VQA_CorrectAnswer(BaseModel):
	question = ForeignKeyField(VQA_Question)
	socketid = CharField(unique=True)
	imageName = CharField()
	answer = TextField()