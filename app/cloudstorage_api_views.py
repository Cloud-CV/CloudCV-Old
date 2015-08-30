from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, load_backend
from django.shortcuts import render, HttpResponse
from django.views.decorators.csrf import csrf_exempt  
from django.views.generic import *
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import * 
from cloudcv17 import *
from app.models import *
from dropbox.client import DropboxClient
from dropbox.session import DropboxSession
from boto.s3.connection import * 
from apiclient import errors
from apiclient.http import MediaFileUpload
from cloudcv17.settings import *
from os import path

import httplib2
import json
import traceback
import glob
import os
import dropbox

def get_user_from_session(session_key):
	'''
	Method for getting user_id using the session_id
	'''
	session_engine = __import__(settings.SESSION_ENGINE, {}, {}, [''])
	session_wrapper = session_engine.SessionStore(session_key)
	session = session_wrapper.load()
	user_id = session.get(SESSION_KEY)
	backend_id = session.get(BACKEND_SESSION_KEY)
	if user_id and backend_id:
		auth_backend = load_backend(backend_id)
		user = auth_backend.get_user(user_id)
		if user:
			return user
	return AnonymousUser()


class UploadAPI(APIView):
	'''
		Uplaod API for uploading featured and classification models to 
		AWS S3 and Dropbox. 
		Convention for uploading files: 
			Example 1: s3://bucket:/path/to/files
			Example 2: dropbox://path/to/files
			Example 3: gdrive://path/to/file 
	'''
	def post(self,request):
		source_path = request.POST['source_path']
		path = request.POST['dest_path']
		session_id = request.POST['session_id']
		user_id = get_user_from_session(session_id).id
		try:
			if path.split(":")[0].lower()=="s3":
				print "[UPLOAD API FOR S3]"
				bucket = path.split(":")[1][2:]
				dest_path = str(path.split(":")[2])
				result = post_data_on_s3(request, source_path, dest_path, bucket, user_id)

			elif path.split(":")[0].lower()=="dropbox":
				print "[UPLOAD API FOR DROPBOX]"
				dest_path = path.split(":")[1]
				access_token = SocialToken.objects.get(account__user__id = user_id, app__name = "Dropbox")
				session = DropboxSession(settings.DROPBOX_APP_KEY, settings.DROPBOX_APP_SECRET)
				access_key, access_secret = access_token.token, access_token.token_secret  # Previously obtained OAuth 1 credentials
				session.set_token(access_key, access_secret)
				client = DropboxClient(session)
				token = client.create_oauth2_access_token()
				result = post_data_on_dropbox(request, source_path, dest_path, token, user_id)

			elif path.split(":")[0].lower()=="gdrive":
				print "[UPLOAD API FOR GOOGLE DRIVE]"
				storage = Storage(SocialToken, 'id', user_id, 'token')
				credential = storage.get()
				# credentials = SocialToken.objects.get(account__user__id = request.user.id, app__name = storage)
				# credentials = credentials.token
				http = credential.authorize(httplib2.Http())
				service = discovery.build('drive', 'v2', http=http)
				results = service.files().list(maxResults=10).execute()
				items = results.get('items', [])
				if not items:
					# print 'No files found.'
					pass
				else:
					# print 'Files:'
					for item in items:
						print '{0} ({1})'.format(item['title'], item['id'])
				result = put_data_on_google_drive(request,path,access_token.token)

			else:
				result = {"error":"Check if you have attached the type of cloud storage with your account or enter valid path"}
		except:
			result = {"error":"Incorrect Input"}
		return HttpResponse(json.dumps(result))

	@csrf_exempt
	def dispatch(self, *args, **kwargs):
		return super(UploadAPI, self).dispatch(*args, **kwargs)

def post_data_on_s3(request, source_path, dest_path, bucket, user_id):
	'''
		Method for Uploading data to S3 bucket using S3 boto module
	'''
	result = {}
	files = [name for name in glob.glob(os.path.join(source_path,'*.*')) if os.path.isfile(os.path.join(source_path,name))]
	result['sourcePath'] = source_path
	result['dest_path'] = dest_path
	result['bucket'] = bucket
	result['uplaodedTo']= []
	result['user_id'] = user_id
	s3_user = StorageCredentials.objects.get(user__id = user_id)
	conn = S3Connection(s3_user.aws_access_key,s3_user.aws_access_secret)
	try:
		# Use the bucket if it already exists
		b = conn.get_bucket(bucket)
	except:
		# If the bucket does not exist, then create a new bucket
		b = conn.create_bucket(bucket)
	for i in files:
		# Loop to upload the files on S3 One by one
		k = Key(b)
		k.key = dest_path+i.split("/")[-1]
		result['uplaodedTo'].append(k.key)
		k.set_contents_from_filename(i)
	return result


def post_data_on_dropbox(request, source_path, dest_path,access_token, user_id):
	'''
		Method for uploading data on Dropbox using Dropbox API
	'''
	result = {}
	client = dropbox.client.DropboxClient(access_token)
	result['dest_path'] = dest_path
	result['user_id'] = user_id
	files = [name for name in glob.glob(os.path.join(source_path,'*.*')) if os.path.isfile(os.path.join(source_path,name))]
	for i in files:
		f = open(i,'rb')
		response = client.put_file(dest_path+i.split("/")[-1], f)
	return result


class DownloadAPI(APIView):
	'''
		Download API for downloading Training Images, Validation Images 
		and Caffe models from S3 and Dropbox.  
	'''
	def post(self,request):
		try:
			result = {}
			path = request.POST['source_path']
			session_id = request.POST['session_id']
			user_id = get_user_from_session(session_id).id
			dest_path = request.POST['dest_path']
			dest_path = dest_path.split('/')
			dest_path.append(str(user_id))
			dest_path[-1],dest_path[-2] = dest_path[-2],dest_path[-1]
			dest_path = '/'.join(dest_path)
			try:
				# Increment the name of new directory by one
				directories = map(int, os.listdir(dest_path))
				dest_path+='/'+str(max(directories)+1)
			except:
				# If no directory exists then give it name 1
				dest_path+='/'+'1'

			if dest_path[-1]!="/":
				# Append forward slash to given url if not exists
				dest_path+="/"
			if not os.path.isdir(dest_path):
				os.makedirs(dest_path)

			if path.split(":")[0].lower()=="s3":
				print "[DOWNLOAD API FOR S3]"
				bucket = path.split(":")[1][2:]
				source_path = str(path.split(":")[2])
				result = get_data_from_s3(request, source_path, dest_path, bucket, user_id)

			elif path.split(":")[0].lower()=="dropbox":
				print "[DOWNLOAD API FOR DROPBOX]"
				source_path = path.split(':')[1][1:]
				access_token = SocialToken.objects.get(account__user__id = user_id, app__name = "Dropbox")
				session = DropboxSession(settings.DROPBOX_APP_KEY, settings.DROPBOX_APP_SECRET)
				access_key, access_secret = access_token.token, access_token.token_secret  # Previously obtained OAuth 1 credentials
				session.set_token(access_key, access_secret)
				client = DropboxClient(session)
				token = client.create_oauth2_access_token()
				result = get_data_from_dropbox(request, source_path, dest_path, token, user_id)
			elif path.split(":")[0].lower() =="gdrive":
				# NON FUNCTIONAL
				get_data_from_google(request,path,access_token)
			else:
				result = {"error":"Check if you have attached the type of cloud storage with your account or enter valid path"}
		except:
			result = {"error":"Invalid Input Provided"}
		return HttpResponse(json.dumps(result))


def get_data_from_s3(request,source_path, dest_path, bucket, user_id):
	'''
		Method for downloading data from S3 bucket using S3boto
	'''
	result = {}
	try:
		s3 = StorageCredentials.objects.get(user__id = user_id)
		conn = S3Connection(s3.aws_access_key,s3.aws_access_secret)
		b = conn.get_bucket(bucket)
		result['user_id'] = user_id
		result['bucket'] = bucket
		result['dest_path'] = dest_path
	except:
		result['error'] = "Check if the S3 bucket exists or not."
		return result
	bucket_entries = b.list(source_path[1:])
	for i in bucket_entries:
		file_name = str(i.key).split("/")[-1]
		i.get_contents_to_filename(dest_path + file_name)
	return result


def get_dropbox_directory_size(path,client):
	'''
		Method to download size of a Directory inside Dropbox
	'''
	return sum(
		f['bytes'] if not f['is_dir'] else size(f['path'])
		for f in client.metadata(path)['contents']
	)


def get_data_from_dropbox(request,source_path, dest_path, access_token, user_id):
	'''
		Method for downloading data from Dropbox using Dropbox API
	'''
	result = {}
	try:
		client = dropbox.client.DropboxClient(str(access_token))
		images_metadata = client.metadata(source_path)
		result['user_id'] = user_id
		result['source_path'] = source_path
		result['dest_path'] = dest_path
		for i in images_metadata['contents']:
			if not i['is_dir']:
				f, metadata = client.get_file_and_metadata(i['path'])
				out = open(dest_path + str(i['path'].split("/")[-1]), 'wb')
				out.write(f.read())
				out.close()
	except:
		result['error'] = "Check if the directory exists or not and then try again."
	return result

# BELOW METHOD NOT WORKING FOR NOW
def createDriveService():
	"""
		Builds and returns a Drive service object authorized with the
		application's service account.
		Returns:
		   Drive service object.
	"""
	from oauth2client.appengine import AppAssertionCredentials
	from apiclient.discovery import build
	credentials = AppAssertionCredentials(scope='https://www.googleapis.com/auth/drive')
	http = httplib2.Http()
	http = credentials.authorize(http)
	return build('drive', 'v2', http=http, developerKey=API_KEY)

# BELOW METHOD NOT WORKING FOR NOW
def insert_file(service, title, parent_id, filename):
  """Insert new file.
  Args:
	service: Drive API service instance.
	title: Title of the file to insert, including the extension.
	description: Description of the file to insert.
	parent_id: Parent folder's ID.
	mime_type: MIME type of the file to insert.
	filename: Filename of the file to insert.
  Returns:
	Inserted file metadata if successful, None otherwise.
  """
 #  media_body = MediaFileUpload(filename,resumable=True)
 #  body = {
	# 'title': title,
 #  }
 #  # Set the parent folder.
 #  if parent_id:
	# body['parents'] = [{'id': parent_id}]

 #  try:
	# file = service.files().insert(
	#   body=body,
	#   media_body=media_body).execute()

	# # Uncomment the following line to print the File ID
	# print 'File ID: %s' % file['id']

	# return file
 #  except errors.HttpError, error:
	# print 'An error occured: %s' % error
	# return None


up_storage_api = csrf_exempt(UploadAPI.as_view())
down_storage_api = csrf_exempt(DownloadAPI.as_view())

