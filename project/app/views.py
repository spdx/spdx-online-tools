from django.shortcuts import render,render_to_response
from django.http import HttpResponse,HttpResponseRedirect,HttpResponseBadRequest,JsonResponse
from django.contrib.auth import authenticate,login ,logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django import forms
from django.template import RequestContext
# Create your views here.

from app.models import UserID
from app.forms import UserRegisterForm,UserProfileForm


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
	
	
def register(request):
	context_dict={}
	if request.method == 'POST':
		user_form = UserRegisterForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)
		if user_form.is_valid() and profile_form.is_valid():
			user = user_form.save(commit=False)
			user.set_password(user.password)
			user.is_staff=True
			profile = profile_form.save(commit=False)
			user.save()
			profile.user = user
			profile.save()
			registered = True
			return HttpResponseRedirect('/app/login/')
		else:
			print user_form.errors
			print profile_form.errors
	else:
		user_form = UserRegisterForm()
		profile_form = UserProfileForm()
		context_dict["user_form"]=user_form
		context_dict["profile_form"]=profile_form
	return render(request,'app/register.html',context_dict)
