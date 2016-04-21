from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

import app.conf as conf


def superuser_permission_check(user):
    return user.is_superuser


@user_passes_test(superuser_permission_check, login_url='/admin/login/')
def cloudcv_admin_config(request):
    if request.user.is_authenticated() and request.user.is_superuser:
        if request.method=="GET":
            return render(request, 'cloudcv_admin/configs.html', {'show_sample_demo_images': conf.SHOW_KNOWN_DEMO_IMAGES})

        elif request.method=="POST":
            show_known_demo_images = request.POST.get('show_known_demo_images', 'off')
            checkobx_dict = {'on':True, 'off': False}
            conf.SHOW_KNOWN_DEMO_IMAGES = checkobx_dict[show_known_demo_images]
            return HttpResponseRedirect(reverse_lazy("cloudcv-admin"))

        else:
            return HttpResponseNotFound('<h1>Page not found</h1>')
    else:
        return HttpResponseNotFound('<h1>Page not found</h1>')
