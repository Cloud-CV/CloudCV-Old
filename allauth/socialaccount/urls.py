from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url('^login/cancelled/$', views.login_cancelled, 
        name='socialaccount_login_cancelled'),
    url('^login/error/$', views.login_error, name='socialaccount_login_error'),
    url('^social_signup/$', views.signup, name='socialaccount_signup'),
    url('^cloudstorage/$', views.connections, name='socialaccount_connections'))
