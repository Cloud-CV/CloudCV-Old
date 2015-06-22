'''
Author: Deshraj
'''

from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework.test import APIRequestFactory
from rest_framework import status
from rest_framework.test import APITestCase
from app.models import *
# import unittest

def user_POST(self):
	url = '/api/users/'
	data = {
		"first_name": "test",
		"last_name": "kumar",
		"username": "tester",
		"email_id": "tester@cloudcv.org",
		"institution": "CloudCV",
		"last_login": "0001-01-01T01:01:00Z",
		"date_joined": "0001-01-01T01:01:00Z",
		"purpose": "RE"
	}
	self.client.post(url, data, format='json')

def model_POST(self):
	# POST request so as to ensure that ModelStorage instance is created 
	url = '/api/models/'
	data = {
		"file_location": "/cloudcv_deshraj/hello.py",
		"parameters": "{'hello':'world'}",
		"neural_network": "/neuralnetwork/prototxt",
		"database_used": "/database/prototxt"
	}
	self.client.post(url, data, format='json')

class SimpleTest(TestCase):
	def test_basic_addition(self):
		"""
		Tests that 1 + 1 always equals 2.
		"""
		self.assertEqual(1 + 1, 2)


class UserTest(APITestCase):
	"""
	Ensure CRUD in REST API for User Model.
	"""
	def test_GET(self):
		#GET Request for ensuring all user instances are there
		url = '/api/users/'
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_POST(self):
		# POST request so as to ensure that User instance is created 
		url = '/api/users/'
		data = {
			"first_name": "test",
			"last_name": "kumar",
			"username": "tester",
			"email_id": "tester@cloudcv.org",
			"institution": "CloudCV",
			"last_login": "0001-01-01T01:01:00Z",
			"date_joined": "0001-01-01T01:01:00Z",
			"purpose": "RE"
		}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data, data)

	def test_PUT(self):
		# PUT method so as to ensure that User instance can be updated 
		url = '/api/users/1/'
		data = {
			"first_name": "test",
			"last_name": "aggarwal",
			"username": "tester",
			"email_id": "tester@cloudcv.org",
			"institution": "CloudCV",
			"last_login": "0001-01-01T01:01:00Z",
			"date_joined": "0001-01-01T01:01:00Z",
			"purpose": "RE"
		}
		UserTest.test_POST(self)
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data, data)
		
	def test_DELETE(self):
		# DELETE method for deleting the test user instance 
		# user = User.objects.get(first_name = "test")
		url = '/api/users/1/'
		UserTest.test_POST(self)
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


# class UserTestChild(UserTest):
# 	"""
# 	To know that why this class has been created, have a look at
# 	http://stackoverflow.com/questions/1173992/what-is-a-basic-example-of-single-inheritance-using-the-super-keyword-in-pytho
# 	Actually simply using the instance of TestCase class is not a good way 
# 	of doing this since it involves the costumization of the predefined 
# 	TestCase Class.
# 	"""
# 	def test_POST(self,):
# 		print "Child"

class RequestLogTest(APITestCase):
	"""
	Ensure CRUD in REST API for RequestLog Model.
	"""
	def test_GET(self):
		#GET Request for ensuring all RequestLog instances are there
		url = '/api/requests/'
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_POST(self):
		# POST request so as to ensure that RequestLog instance is created 
		url = '/api/requests/'
		data = {
			"user": 1,
			"api_used": "PY",
			"job_id": "1",
			"processing_state": "RUN",
			"no_of_images": 1,
			"parameters": "{\"foo\":\"bar\"}",
			"duration": "0001-01-01T01:01:00Z",
			"input_source_type": "type1",
			"input_source_value": 1,
			"output_source_type": "type2",
			"output_source_value": 1
		}
		# x = UserTestChild()
		# super(UserTestChild,x).test_POST()
		# UserTest.test_POST(user)
		user_POST(self) #global funciton declared on the top of the file 
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data, data)

	def test_PUT(self):
		# PUT method so as to ensure that RequestLog instance can be updated 
		url = '/api/requests/1/'
		data = {
			"user": 1,
			"api_used": "MAT",
			"job_id": "1",
			"processing_state": "RUN",
			"no_of_images": 1,
			"parameters": "{\"foo\":\"bar\"}",
			"duration": "0001-01-01T01:01:00Z",
			"input_source_type": "type1",
			"input_source_value": 2,
			"output_source_type": "type2",
			"output_source_value": 2
		}
		RequestLogTest.test_POST(self)
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data, data)
		
	def test_DELETE(self):
		# DELETE method for deleting the test RequestLog instance 
		url = '/api/requests/1/'
		RequestLogTest.test_POST(self)
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class CurrentRequestTest(APITestCase):
	"""
	Ensure CRUD in REST API for CurrentRequest Model.
	"""
	def test_GET(self):
		#GET Request for ensuring all CurrentRequest instances are there
		url = '/api/current_requests/'
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_POST(self):
		# POST request so as to ensure that CurrentRequest instance is created 
		url = '/api/current_requests/'
		data = {
			"user": 1,
			"ram_usage": 10.0,
			"cpu_usage": 5.0,
			"disk_space_usage": 10.0,
			"no_of_jobs_running": 1
		}
		user_POST(self) #global funciton declared on the top of the file 
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data, data)

	def test_PUT(self):
		# PUT method so as to ensure that CurrentRequest instance can be updated 
		url = '/api/current_requests/1/'
		data = {
			"user": 1,
			"ram_usage": 20.0,
			"cpu_usage": 5.0,
			"disk_space_usage": 10.0,
			"no_of_jobs_running": 2
		}
		CurrentRequestTest.test_POST(self)
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data, data)
		
	def test_DELETE(self):
		# DELETE method for deleting the test CurrentRequest instance 
		url = '/api/current_requests/1/'
		CurrentRequestTest.test_POST(self)
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)



class ModelStorageTest(APITestCase):
	"""
	Ensure CRUD in REST API for ModelStorage Model.
	"""
	def test_GET(self):
		#GET Request for ensuring all ModelStorage instances are there
		url = '/api/models/'
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_POST(self):
		# POST request so as to ensure that ModelStorage instance is created 
		url = '/api/models/'
		data = {
			"file_location": "/cloudcv_deshraj/hello.py",
			"parameters": "{'hello':'world'}",
			"neural_network": "/neuralnetwork/prototxt",
			"database_used": "/database/prototxt"
		}
		# user_POST(self) #global funciton declared on the top of the file 
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data, data)

	def test_PUT(self):
		# PUT method so as to ensure that ModelStorage instance can be updated 
		url = '/api/models/1/'
		data = {
			"file_location": "/cloudcv_harsh/hello.py",
			"parameters": "{'hello':'world'}",
			"neural_network": "/neuralnetwork/prototxt",
			"database_used": "/database/prototxt"
		}
		ModelStorageTest.test_POST(self)
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data, data)
		
	def test_DELETE(self):
		# DELETE method for deleting the test ModelStorage instance 
		url = '/api/models/1/'
		ModelStorageTest.test_POST(self)
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ImagesTest(APITestCase):
	"""
	Ensure CRUD in REST API for Images Model.
	"""
	def test_GET(self):
		#GET Request for ensuring all Images instances are there
		url = '/api/images/'
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_POST(self):
		# POST request so as to ensure that Images instance is created 
		url = '/api/images/'
		data = {
		    "user": 1,
		    "category": "Train A Class",
		    "url": "http://gsoc.cloudcv.org:9000/api/image"
		}
		user_POST(self) #global funciton declared on the top of the file 
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data, data)

	def test_PUT(self):
		# PUT method so as to ensure that Images instance can be updated 
		url = '/api/images/1/'
		data = {
		    "user": 1,
		    "category": "Classification",
		    "url": "http://gsoc.cloudcv.org:9000/api/image"
		}
		ImagesTest.test_POST(self)
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data, data)
		
	def test_DELETE(self):
		# DELETE method for deleting the test Images instance 
		url = '/api/images/1/'
		ImagesTest.test_POST(self)
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class GroupTest(APITestCase):
	"""
	Ensure CRUD in REST API for Group Model.
	"""
	def test_GET(self):
		#GET Request for ensuring all Group instances are there
		url = '/api/groups/'
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_POST(self):
		# POST request so as to ensure that Group instance is created 
		url = '/api/groups/'
		data = {
		    "model": 1,
		    "group_id": 1,
		    "group_name": "Rangers",
		    "purpose": "Research",
		    "user": 1
		}
		user_POST(self) #global funciton declared on the top of the file 
		model_POST(self) #global funciton declared on the top of the file
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data, data)

	def test_PUT(self):
		# PUT method so as to ensure that Group instance can be updated 
		url = '/api/groups/1/'
		data = {
		    "model": 1,
		    "group_id": 1,
		    "group_name": "Crawlers",
		    "purpose": "Education",
		    "user": 1
		}
		GroupTest.test_POST(self)
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data, data)
		
	def test_DELETE(self):
		# DELETE method for deleting the test Group instance 
		url = '/api/groups/1/'
		GroupTest.test_POST(self)
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

