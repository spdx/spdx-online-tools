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
	
def about(request):
	context_dict={}
	return render(request, 'app/about.html',context_dict)
	
def validate(request):
	context_dict={}
	if request.method == 'POST':
		try :
			if request.FILES["file"]:
				return HttpResponse("File Uploaded Successfully")
			else :
				return HttpResponse("File Not Uploaded")
		except:
			return HttpResponse("Error")
	return render(request, 'app/validate.html',context_dict)

def compare(request):
	context_dict={}
	if request.method == 'POST':
		try :
			if request.FILES["file"]:
				return HttpResponse("File Uploaded Successfully")
			else :
				return HttpResponse("File Not Uploaded")
		except:
			return HttpResponse("Error")
	return render(request, 'app/compare.html',context_dict)
	
def convert(request):
	context_dict={}
	if request.method == 'POST':
		try :
			if request.FILES["file"]:
				return HttpResponse("File Uploaded Successfully")
			else :
				return HttpResponse("File Not Uploaded")
		except:
			return HttpResponse("Error")
	return render(request, 'app/convert.html',context_dict)
	
def search(request):
	context_dict={}
	return render(request, 'app/search.html',context_dict)
	
def login(request):
	context_dict={}
	return render(request, 'app/login.html',context_dict)
