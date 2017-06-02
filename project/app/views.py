from django.shortcuts import render,render_to_response
from django.http import HttpResponse,HttpResponseRedirect,HttpResponseBadRequest,JsonResponse
from django.contrib.auth import authenticate,login ,logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django import forms
from django.template import RequestContext
# Create your views here.


def index(request):
	context_dict={}
	return render(request, 'app/index.html',context_dict)
