from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from app.models import CloudCV_Users, GoogleAccountInfo, DropboxAccount
from cloudcv17 import config

import urllib
import urlparse
import requests
import base64
import os
import json
import dropbox


def handleAuth(request, is_API, contains_UUID):
    APP_KEY = config.DROPBOX_APP_KEY
    APP_SECRET = config.DROPBOX_APP_SECRET
    redirect_url = 'http://localhost:8000/dropbox_callback'

    if is_API:
        #contains uuid
        if contains_UUID:
            request_userid = request.GET['userid']
            user = CloudCV_Users.objects.get(userid=request_userid)
            try:
                dropbox_account = DropboxAccount.objects.get(cloudcvid=user)
                if dropbox_account:
                    return json.dumps({'isValid': 'True', 'token': str(dropbox_account.access_token)})
            except ObjectDoesNotExist:
                authorize_url = 'https://www.dropbox.com/1/oauth2/authorize?client_id='+ APP_KEY+ '&response_type=code' \
                                                                                                  '&redirect_uri='+redirect_url+'&state='+str(request.GET['state'])
                return json.dumps({'redirect': 'True', 'url': str(authorize_url)})
        else:
            return json.dumps({'isLoggedIn': 'False'})
    else:
        authorize_url = 'https://www.dropbox.com/1/oauth2/authorize?client_id=' + APP_KEY + '&response_type=code' \
                        '&redirect_uri=' + redirect_url + '&state=' + str(request.GET['state'])
        return authorize_url


def handleCallback(user_id, code, request):
    APP_KEY = '3bh4nkyaszl2nhd'
    APP_SECRET = 'en8d42vv2xej8ox'
    redirect_url = 'http://localhost:8000/dropbox_callback'

    data = requests.post('https://api.dropbox.com/1/oauth2/token',
                data={
                        'code': code,
                        'grant_type': 'authorization_code',
                        'redirect_uri': redirect_url
                },
                auth=(APP_KEY, APP_SECRET)).json()
    token = data['access_token']
    dbuserid = data['uid']

    try:
        user = CloudCV_Users.objects.get(userid=user_id)
        dropboxuser = DropboxAccount(cloudcvid=user, access_token=token)
        dropboxuser.save()
    except IntegrityError:
        dropboxuser = DropboxAccount.objects.get(cloudcvid=user)
        dropboxuser.access_token = token
        dropboxuser.save()

    response_dict = {'uid': dbuserid, 'token': token}
    return json.dumps(response_dict)
