from django.conf.urls import url

from app import views, decaf_views, classify_views, poi_views, trainaclass_views

from app.decaf_views import DecafCreateView, DecafModelCreateView
from app.classify_views import ClassifyCreateView
from app.poi_views import PoiCreateView
from app.trainaclass_views import TrainaclassCreateView


urlpatterns = [
    url(r'^decaf-server/$', DecafCreateView.as_view(), {}, 'decaf'),
    url(r'^decaf-server-new/$', DecafModelCreateView.as_view(), {}, 'decaf'),
    url(r'^classify/$', ClassifyCreateView.as_view(), {}, 'classify'),
    url(r'^vip/$', PoiCreateView.as_view(), {}, 'poi'),
    url(r'^trainaclass/$', TrainaclassCreateView.as_view(), {}, 'trainaclass'),
]


urlpatterns += [
    url(r'^$', views.homepage, name="home"),
    url(r'^demoupload/(?P<executable>\w+)/$', views.demoUpload, name='demoUpload'),
    url(r'^matlab/$', views.matlabReadRequest, name='matlabReadRequest'),
    # url(r'^auth/(?P<auth_name>\w+)/$', views.authenticate, name='authenticate'),
    # url(r'^callback/(?P<auth_name>\w+)/$', views.callback, name='callback'),
    # url(r'^api/$', views.matlabReadRequest, name='apiRequest'),
    # url(r'^pass/$', views.pass1, name='pass1'),
]

urlpatterns += [
    url(r'^decaf_dropbox/$', decaf_views.decafDropbox, name="decafDropbox"),
    url(r'^decaf_train/$', decaf_views.decaf_train, name="decaf_train"),
    url(r'^demo_decaf/$', decaf_views.demoDecaf, name="demoDecaf"),
]

urlpatterns += [
    url(r'^demo_classify/$', classify_views.demoClassify, name="demoClassify"),
]

urlpatterns += [
    url(r'^demo_poi/$', poi_views.demoPoi, name="demoPoi"),
]

urlpatterns += [
    url(r'^trainmodel/$', trainaclass_views.trainamodel, name="trainamodel"),
    url(r'^testmodel/$', trainaclass_views.testmodel, name="testmodel"),
]
