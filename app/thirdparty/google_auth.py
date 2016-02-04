from django.db import IntegrityError

from app.models import CloudCV_Users, GoogleAccountInfo
from cloudcv17 import config
import app.conf as conf

from oauth2client.client import OAuth2WebServerFlow

import requests
import json
import uuid
import os
import traceback

flow = OAuth2WebServerFlow(client_id=config.GOOGLE_CLIENT_ID,
                           client_secret=config.GOOGLE_CLIENT_SECRET,
                           scope='profile email',
                           redirect_uri='http://localhost:8000/callback/google')


def create_folder(user_uuid):
    # parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    image_dir = os.path.join(conf.PIC_DIR, user_uuid)
    if os.path.exists(image_dir) is False:
        os.makedirs(image_dir, 0775)
    return image_dir.encode('utf-8')


def saveIntoDatabase(gaccountinfo, credentials):
    user_uuid = str(uuid.uuid1())
    user_fname = gaccountinfo['name']['givenName'].encode('utf-8')
    user_lname = gaccountinfo['name']['familyName'].encode('utf-8')
    user_emailid = gaccountinfo['emails'][0]['value'].encode('utf-8')
    response_dict = {'id': user_uuid, 'email': user_emailid}

    try:
        user = CloudCV_Users(first_name=user_fname, last_name=user_lname,
                             userid=user_uuid, emailid=user_emailid, is_active=True)
        user.save()
        create_folder(user_uuid)
        response_dict['user_table_message'] = 'Successfully Registered User\n'
    except IntegrityError:
        user = CloudCV_Users.objects.get(emailid=user_emailid)
        user_uuid = user.userid
        response_dict['id'] = user_uuid
        response_dict['user_table_message'] = 'Email ID already existing in the database, returning corresponding userid\n'
        response_dict['folder'] = create_folder(user_uuid)
    except:
        response_dict['error'] = traceback.format_exc().encode('utf-8')
        return json.dumps(response_dict)

    try:
        googleuser = GoogleAccountInfo(cloudcvid=user, credential=credentials, flow=flow)
        googleuser.save()
        response_dict['gaccount_table_message'] = 'Successfully created entry for the google account\n'
    except IntegrityError:
        googleuser = GoogleAccountInfo.objects.get(cloudcvid=user)
        googleuser.credential = credentials
        googleuser.flow = flow
        googleuser.save()
        response_dict['gaccount_table_message'] = 'Already existing user entry, updated the entries\n'
    return json.dumps(response_dict)


def handleCallback(code, request):
    credentials = flow.step2_exchange(request.REQUEST)
    cred_json = json.loads(credentials.to_json())

    result = requests.get('https://www.googleapis.com/plus/v1/people/me',
                          headers={'Authorization': 'Bearer ' + str(cred_json['access_token'])})
    gaccountinfo = json.loads(result.text.encode('utf-8'))

    json_response = saveIntoDatabase(gaccountinfo, credentials)
    # response contains  a JSON object containing unique id and email id.
    return json_response


def handleAuth(request, is_API, contains_UUID):
    # if the call comes from Matlab or Python API
    if is_API:
        # contains uuid
        if contains_UUID:
            request_userid = request.GET['userid']
            try:
                user = CloudCV_Users.objects.get(userid=request_userid)
                # google_account = GoogleAccountInfo.objects.get(cloudcvid=user)
                # cred_json = google_account.credential.to_json()
                create_folder(request_userid)
                return json.dumps({'isValid': 'True', 'first_name': user.first_name})
            except:
                return json.dumps({'error': traceback.format_exc()})
        # doesnt contain uuid
        else:
            flow.params['state'] = request.GET['state']
            authorize_url = flow.step1_get_authorize_url()
            return json.dumps({'redirect': 'True', 'url': authorize_url.encode('utf-8')})
    # else if it comes from browser
    else:
        flow.params['state'] = request.GET['state']
        authorize_url = flow.step1_get_authorize_url()
        return authorize_url
