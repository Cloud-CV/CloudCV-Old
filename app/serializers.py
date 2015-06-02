from django.forms import widgets
from rest_framework import serializers
from app.models import *


# class PictureSerializer(serializers.ModelSerializer):
# 	class Meta:
# 		model = Picture
# 		fields = ('file','slug')

# 	def create(self, validated_data):
# 		"""
# 		Create and return a new `Picture` instance, given the validated data.
# 		"""
# 		return Picture.objects.create(**validated_data)

# 	def update(seld, instance, validated_data):
# 		instance.file = validated_data.get('file',instance.file)
# 		instance.slug = validated_data.get('slug',instance.slug)
# 		instance.save()
# 		return instance


class CloudCV_UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = CloudCV_User
		fields = ('first_name','last_name','userid','emailid','is_active')

	def create(self, validated_data):
		"""
		Create and return a new `CloudCV_User` instance, given the validated data.
		"""
		return CloudCV_User.objects.create(**validated_data)

	def update(seld, instance, validated_data):
		instance.first_name = validated_data.get('first_name',instance.first_name)
		instance.last_name = validated_data.get('last_name',instance.last_name)
		instance.userid = validated_data.get('userid',instance.userid)
		instance.emailid = validated_data.get('emailid',instance.emailid)
		instance.is_active = validated_data.get('is_active',instance.is_active)
		instance.save()
		return instance

class RequestLogSerializer(serializers.ModelSerializer):
	class Meta:
		model = RequestLog
		fields = ('cloudcvid','jobid','noOfImg','function','dateTime','isDropbox','apiName')

	def create(self, validated_data):
		"""
		Create and return a new `CloudCV_User` instance, given the validated data.
		"""
		return RequestLog.objects.create(**validated_data)

	def update(seld, instance, validated_data):
		instance.cloudcvid = validated_data.get('cloudcvid',instance.cloudcvid)
		instance.jobid = validated_data.get('jobid',instance.jobid)
		instance.noOfImg = validated_data.get('noOfImg',instance.noOfImg)
		instance.dateTime = validated_data.get('dateTime',instance.dateTime)
		instance.isDropbox = validated_data.get('isDropbox',instance.isDropbox)
		instance.apiName = validated_data.get('apiName',instance.apiName)
		instance.save()
		return instance
