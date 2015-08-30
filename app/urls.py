# encoding: utf-8
from django.conf.urls import patterns, url
from django.contrib import admin

from app.views import (
        PictureCreateView,BasicPlusVersionCreateView
        )
from app.decaf_views import DecafCreateView, decafDropbox, DecafModelCreateView
from app.classify_views import ClassifyCreateView
from app.poi_views import PoiCreateView
from app.trainaclass_views import TrainaclassCreateView
from app import views

# the below module import is used for importing the foramt type in which we the data like json or xml
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns('',
    url(r'^image-stitch/$', PictureCreateView.as_view(), name='upload-new'),
    url(r'^basicplus/$', BasicPlusVersionCreateView.as_view(), name='upload-basic-plus'),
    (r'^decaf-server/$', DecafCreateView.as_view(), {}, 'decaf'),
    (r'^decaf-server-new/$', DecafModelCreateView.as_view(), {}, 'decaf'),
    (r'^classify/$', ClassifyCreateView.as_view(), {}, 'classify'),
    (r'^vip/$', PoiCreateView.as_view(), {}, 'poi'),
    (r'^trainaclass/$', TrainaclassCreateView.as_view(), {}, 'trainaclass'),
)

urlpatterns += patterns('app.views',
    url(r'^$', 'homepage', name="home"),
    url(r'^demoupload/(?P<executable>\w+)/$','demoUpload', name='demoUpload'),
    url(r'^auth/(?P<auth_name>\w+)/$','authenticate', name='authenticate'),
    url(r'^callback/(?P<auth_name>\w+)/$', 'callback', name='callback'),
    url(r'^matlab/$','matlabReadRequest', name='matlabReadRequest'),
    url(r'^api/$','matlabReadRequest', name='apiRequest'),
    url(r'^ec2/$','ec2', name='ec2'),
)

urlpatterns += patterns('app.decaf_views',
    url(r'^decaf_dropbox/$', 'decafDropbox', name="decafDropbox"),
    url(r'^decaf_train/$', 'decaf_train', name="decaf_train"),
     url(r'^demo_decaf/$', 'demoDecaf', name="demoDecaf"),
)

urlpatterns += patterns('app.classify_views',
    url(r'^demo_classify/$', 'demoClassify', name="demoClassify"),
)
urlpatterns += patterns('app.poi_views',
    url(r'^demo_poi/$', 'demoPoi', name="demoPoi"),
)

urlpatterns += patterns('app.trainaclass_views',
    url(r'^trainmodel/$', 'trainamodel', name="trainamodel"),
    url(r'^testmodel/$', 'testmodel', name="testmodel"),
)

urlpatterns += patterns('app.cloudstorage_api_views',
    url(r'api/upload', 'up_storage_api', name='api_upload'),
    url(r'api/download', 'down_storage_api', name='api_download'),
)

urlpatterns += patterns('app.serializers',
    url(r'^api/users/$', views.UserList.as_view()),
    url(r'^api/users/(?P<pk>[0-9]+)/$', views.UserDetail.as_view()),
    url(r'^api/requests/$', views.RequestLogList.as_view()),
    url(r'^api/requests/(?P<pk>[0-9]+)/$', views.RequestLogDetail.as_view()),
    url(r'^api/groups/$', views.GroupList.as_view()),
    url(r'^api/groups/(?P<pk>[0-9]+)/$', views.GroupDetail.as_view()),
    url(r'^api/current_requests/$', views.CurrentRequestList.as_view()),
    url(r'^api/current_requests/(?P<pk>[0-9]+)/$', views.CurrentRequestDetail.as_view()),
    url(r'^api/images/$', views.ImagesList.as_view()),
    url(r'^api/images/(?P<pk>[0-9]+)/$', views.ImagesDetail.as_view()),
    url(r'^api/models/$', views.ModelStorageList.as_view()),
    url(r'^api/models/(?P<pk>[0-9]+)/$', views.ModelStorageDetail.as_view()),
)

urlpatterns = format_suffix_patterns(urlpatterns)
