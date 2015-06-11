from django.forms import widgets
from rest_framework import serializers
from app.models import *

class UserSerializer(serializers.ModelSerializer):
	'''
	Serializer Class for User Model
	'''
	class Meta:
		model = User
		fields = ('first_name','last_name','username','email_id','institution','last_login','date_joined','purpose')

	def create(self, validated_data):
		"""
		Create and return a new `User` instance, given the validated data.
		"""
		return User.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.first_name = validated_data.get('first_name',instance.first_name)
		instance.last_name = validated_data.get('last_name',instance.last_name)
		instance.username = validated_data.get('username',instance.username)
		instance.email_id = validated_data.get('email_id',instance.email_id)
		instance.institution = validated_data.get('institution',instance.institution)
		instance.last_login = validated_data.get('last_login',instance.last_login)
		instance.date_joined = validated_data.get('date_joined',instance.date_joined)
		instance.purpose = validated_data.get('purpose',instance.purpose)
		instance.save()
		return instance

class RequestLogSerializer(serializers.ModelSerializer):
	'''
	Serializer Class for RequestLog Model
	'''
	user_entries = UserSerializer(many=True)
	class Meta:
		model = RequestLog
		fields = ('api_used','job_id','processing_state','no_of_images','parameters','duration','input_source_type','input_source_value','output_source_type','output_source_value')

	def create(self, validated_data):
		"""
		Create and return a new `RequestLog` instance, given the validated data.
		"""
		return RequestLog.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.cloudcvid = validated_data.get('cloudcvid',instance.cloudcvid)
		instance.jobid = validated_data.get('jobid',instance.jobid)
		instance.noOfImg = validated_data.get('noOfImg',instance.noOfImg)
		instance.dateTime = validated_data.get('dateTime',instance.dateTime)
		instance.isDropbox = validated_data.get('isDropbox',instance.isDropbox)
		instance.apiName = validated_data.get('apiName',instance.apiName)
		instance.save()
		return instance


class GroupSerializer(serializers.ModelSerializer):
	'''
	Serializer Class for Group Model
	'''
	user_entries = UserSerializer(many=True)
	class Meta:
		fields = ('group_id','group_name','purpose','user')

	def create(self, validated_data):
		"""
		Create and return a new `Group` instance, given the validated data.
		"""
		return Group.objects.create(**validated_data)

	def update(seld, instance, validated_data):
		instance.group_id = validated_data.get('group_id',instance.group_id)
		instance.group_name = validated_data.get('group_name',instance.group_name)
		instance.purpose = validated_data.get('purpose',instance.purpose)
		# instance.user = validated_data.get('user',instance.user)
		instance.save()
		return instance

class CurrentRequestSerializer(serializers.ModelSerializer):
	'''
	Serializer Class for CurrentRequest Model
	'''
	user_entries = UserSerializer(many=True)
	class Meta:
		fields = ('ram_usage','cpu_usage','disk_space_usage','no_of_jobs_running')

	def create(self, validated_data):
		"""
		Create and return a new `CurrentRequest` instance, given the validated data.
		"""
		return CurrentRequest.objects.create(**validated_data)

	def update(seld, instance, validated_data):
		instance.ram_usage = validated_data.get('ram_usage',instance.ram_usage)
		instance.cpu_usage = validated_data.get('cpu_usage',instance.cpu_usage)
		instance.disk_space_usage = validated_data.get('disk_space_usage',instance.disk_space_usage)
		instance.no_of_jobs_running = validated_data.get('no_of_jobs_running',instance.no_of_jobs_running)
		# instance.user = validated_data.get('user',instance.user)
		instance.save()
		return instance

class ImagesSerializer(serializers.ModelSerializer):
	'''
	Serializer Class for Images Model
	'''
	user_entries = UserSerializer(many=True)
	class Meta:
		fields = ('category','url')

	def create(self,validated_data):
		"""
		Create and return a new `Images` instance, given the validated data.
		"""
		return Images.objects.create(**validated_data)

	def update(seld, instance, validated_data):
		instance.category = validated_data.get('category',instance.category)
		instance.url = validated_data.get('url',instance.url)
		# instance.user = validated_data.get('user',instance.user)
		instance.save()
		return instance

