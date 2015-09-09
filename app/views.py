# coding: utf-8
from django.shortcuts import render
from django.http import HttpResponse

from phone.models import *

# Create your views here.

import functools
import sys

def login(request):
    return render(request, 'app/login.html')

def project(request):
    project = Project.objects.get(pk=1)
    active = sys._getframe().f_code.co_name
    context = {'project': project}
    return render(request, 'app/project.html', context)

def news(request, name):
    return render(request, 'app/news/%s' % name)