from django.forms import widgets
from rest_framework import serializers
from app.models import *

class UserSerializer(serializers.ModelSerializer):
	'''
	Serializer Class for User Model
	'''
	class Meta:
		model = UserDetails
		fields = ('institution','purpose')

	def create(self, validated_data):
		"""
		Create and return a new `UserDetails` instance, given the validated data.
		"""
		return UserDetails.objects.create(**validated_data)

	def update(self, instance, validated_data):
		# instance.last_name = validated_data.get('last_name',instance.last_name)
		# instance.username = validated_data.get('username',instance.username)
		# instance.email_id = validated_data.get('email_id',instance.email_id)
		# instance.last_login = validated_data.get('last_login',instance.last_login)
		# instance.date_joined = validated_data.get('date_joined',instance.date_joined)
		# instance.user = validated_data.get('user',instance.user)
		instance.institution = validated_data.get('institution',instance.institution)
		instance.purpose = validated_data.get('purpose',instance.purpose)
		instance.save()
		return instance

class RequestLogSerializer(serializers.ModelSerializer):
	'''
	Serializer Class for RequestLog Model
	'''
	# user_fields = UserSerializer(source = "user")
	class Meta:
		model = RequestLog
		fields = ('user','api_used','job_id','processing_state','no_of_images','parameters','duration','input_source_type','input_source_value','output_source_type','output_source_value')

	def create(self, validated_data):
		"""
		Create and return a new `RequestLog` instance, given the validated data.
		"""
		return RequestLog.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.api_used = validated_data.get('api_used',instance.api_used)
		instance.job_id = validated_data.get('job_id',instance.job_id)
		instance.processing_state = validated_data.get('processing_state',instance.processing_state)
		instance.no_of_images = validated_data.get('no_of_images',instance.no_of_images)
		instance.parameters = validated_data.get('parameters',instance.parameters)
		instance.duration = validated_data.get('duration',instance.duration)
		instance.input_source_type = validated_data.get('input_source_type',instance.input_source_type)
		instance.input_source_value = validated_data.get('input_source_value',instance.input_source_value)
		instance.output_source_type = validated_data.get('output_source_type',instance.output_source_type)
		instance.output_source_value = validated_data.get('output_source_value',instance.output_source_value)
		instance.save()
		return instance



class CurrentRequestSerializer(serializers.ModelSerializer):
	'''
	Serializer Class for CurrentRequest Model
	'''
	# user_fields = UserSerializer(source = "user")
	class Meta:
		model = CurrentRequest
		fields = ('user','ram_usage','cpu_usage','disk_space_usage','no_of_jobs_running')

	def create(self, validated_data):
		"""
		Create and return a new `CurrentRequest` instance, given the validated data.
		"""
		return CurrentRequest.objects.create(**validated_data)

	def update(self, instance, validated_data):
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
	# user_fields = UserSerializer(source = "user")
	class Meta:
		model = Images
		fields = ('user','category','url')

	def create(self,validated_data):
		"""
		Create and return a new `Images` instance, given the validated data.
		"""
		return Images.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.category = validated_data.get('category',instance.category)
		instance.url = validated_data.get('url',instance.url)
		# instance.user = validated_data.get('user',instance.user)
		instance.save()
		return instance

class ModelStorageSerializer(serializers.ModelSerializer):
	'''
	Serializer Class for ModelStorage Model
	'''
	class Meta:
		model = ModelStorage
		fields = ('file_location','parameters', 'neural_network','database_used')

	def create(self,validated_data):
		"""
		Create and return a new `ModelStorage` instance, given the validated data.
		"""
		return ModelStorage.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.file_location = validated_data.get('file_location',instance.file_location)
		instance.parameters = validated_data.get('parameters',instance.parameters)
		instance.neural_network = validated_data.get('neural_network',instance.neural_network)
		instance.database_used = validated_data.get('database_used',instance.database_used)
		
		instance.save()
		return instance
		
class GroupSerializer(serializers.ModelSerializer):
	'''
	Serializer Class for Group Model
	'''
	class Meta:
		model = Group
		fields = ('model','group_id','group_name','purpose','user')

	def create(self, validated_data):
		"""
		Create and return a new `Group` instance, given the validated data.
		"""
		return Group.objects.create(**validated_data)

	def update(self, instance, validated_data):
		instance.group_id = validated_data.get('group_id',instance.group_id)
		instance.group_name = validated_data.get('group_name',instance.group_name)
		instance.purpose = validated_data.get('purpose',instance.purpose)
		# instance.user = validated_data.get('user',instance.user)
		instance.save()
		return instance

