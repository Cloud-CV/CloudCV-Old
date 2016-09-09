from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
# from django.conf.urls.static import static

import app.urls
from django.contrib.staticfiles import views
admin.autodiscover()

urlpatterns = [
    url(r'^', include(app.urls)),
]

# urlpatterns += [
#     static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
#     static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# ]

urlpatterns += [
    url(r'^media/(.*)$', views.serve,
        {'document_root': settings.MEDIA_ROOT}),
    url(r'^static/(.*)$', views.serve,
        {'document_root': settings.STATIC_ROOT}),
]
