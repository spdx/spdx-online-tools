# -*- coding: utf-8 -*-

# Copyright (c) 2017 Rohit Lodha
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import unicode_literals

from django.shortcuts import render,render_to_response
from django.http import HttpResponse,HttpResponseRedirect,HttpResponseBadRequest,JsonResponse
from django.contrib.auth import authenticate,login ,logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django import forms
from django.template import RequestContext
from django.core.files.storage import FileSystemStorage

from app.models import UserID
from app.forms import UserRegisterForm,UserProfileForm

import jpype
import traceback
import os

def index(request):
    context_dict={}
    return render(request, 'app/index.html',context_dict)

def about(request):
    context_dict={}
    return render(request, 'app/about.html',context_dict)

def validate(request):
    context_dict={}
    if request.method == 'POST':
        """ If JVM already started, attach a Thread and start processing the request """
        if (jpype.isJVMStarted()):
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            mainclass = package.Main
            try :
                if request.FILES["file"]:
                    """ Saving file to the media directory """
                    myfile = request.FILES['file']
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    """ Call the java function with parameters as list"""
                    mainclass.main(["Verify",settings.APP_DIR+uploaded_file_url])
                    jpype.detachThreadFromJVM()
                    return HttpResponse("This SPDX Document is valid.")
                else :
                    return HttpResponse("File Not Uploaded")
            except jpype.JavaException :
                context_dict["error"] = jpype.JavaException.message()
                return render(request, 'app/validate.html',context_dict)
            except :
                traceback.print_exc()
                context_dict["error"] = "This SPDX Document is not valid"
                return render(request, 'app/validate.html',context_dict)
        else :
            """ If JVM not already started, start it, attach a Thread and start processing the request """
            classpath =os.path.abspath(".")+"/tool.jar"
            jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            if (jpype.isJVMStarted()):
                jpype.attachThreadToJVM()
                package = jpype.JPackage("org.spdx.tools")
                mainclass = package.Main
                try :
                    if request.FILES["file"]:
                        """ Saving file to the media directory """
                        myfile = request.FILES['file']
                        fs = FileSystemStorage()
                        filename = fs.save(myfile.name, myfile)
                        uploaded_file_url = fs.url(filename)
                        """ Call the java function with parameters as list"""
                        mainclass.main(["Verify",settings.APP_DIR+uploaded_file_url])
                        jpype.detachThreadFromJVM()
                        return HttpResponse("This SPDX Document is valid.")
                    else :
                        return HttpResponse("File Not Uploaded")
                except jpype.JavaException :
                    context_dict["error"] = jpype.JavaException.message()
                    return render(request, 'app/validate.html',context_dict)
                except :
                    traceback.print_exc()
                    context_dict["error"] = "This SPDX Document is not valid"
                    return render(request, 'app/validate.html',context_dict)
    else :
        return render(request, 'app/validate.html',context_dict)

def compare(request):
    context_dict={}
    if request.method == 'POST':
        jpype.startJVM(jpype.getDefaultJVMPath())
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
        """ If JVM already started, attach a Thread and start processing the request """
        if (jpype.isJVMStarted()):
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            mainclass = package.Main
            try :
                if request.FILES["file"]:
                    """ Saving file to the media directory """
                    myfile = request.FILES['file']
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    """ Call the java function with parameters as list"""
                    mainclass.main(["TagToRDF",settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+''.join(filename.split(".")[:-1])+"_test.rdf"])
                    jpype.detachThreadFromJVM()
                    return HttpResponseRedirect("/media/" + ''.join(filename.split(".")[:-1])+"_test.rdf")
                else :
                    return HttpResponse("File Not Uploaded")
            except jpype.JavaException :
                context_dict["error"] = jpype.JavaException.message()
                return render(request, 'app/validate.html',context_dict)
            except :
                traceback.print_exc()
                context_dict["error"] = "This SPDX Document is not valid"
                return render(request, 'app/validate.html',context_dict)
        else :
            """ If JVM not already started, start it, attach a Thread and start processing the request """
            classpath =os.path.abspath(".")+"/tool.jar"
            jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            if (jpype.isJVMStarted()):
                jpype.attachThreadToJVM()
                package = jpype.JPackage("org.spdx.tools")
                mainclass = package.Main
                try :
                    if request.FILES["file"]:
                        """ Saving file to the media directory """
                        myfile = request.FILES['file']
                        fs = FileSystemStorage()
                        filename = fs.save(myfile.name, myfile)
                        uploaded_file_url = fs.url(filename)
                        """ Call the java function with parameters as list"""
                        mainclass.main(["TagToRDF",settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+''.join(filename.split(".")[:-1])+"_test.rdf"])
                        jpype.detachThreadFromJVM()
                        return HttpResponseRedirect("/media/" + ''.join(filename.split(".")[:-1])+"_test.rdf")
                    else :
                        return HttpResponse("File Not Uploaded")
                except jpype.JavaException :
                    context_dict["error"] = jpype.JavaException.message()
                    return render(request, 'app/validate.html',context_dict)
                except :
                    traceback.print_exc()
                    context_dict["error"] = "This SPDX Document is not valid"
                    return render(request, 'app/validate.html',context_dict)
    else :
        return render(request, 'app/convert.html',context_dict)
def search(request):
    context_dict={}
    return render(request, 'app/search.html',context_dict)

def loginuser(request):
    context_dict={}
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user and user.is_staff and not user.is_superuser:
            #add status  choice here
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/app/')
            else:
                return HttpResponse("Your account is disabled.")	
        else:
            context_dict['invalid']="Invalid login details supplied."
            print "Invalid login details: {0}, {1}".format(username, password)
            return render(request, 'app/login.html',context_dict)
    else:
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

def logoutuser(request):
    logout(request)
    return HttpResponseRedirect("/app/")
