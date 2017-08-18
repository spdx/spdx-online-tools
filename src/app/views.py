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
from django.http import HttpResponse,HttpResponseRedirect,HttpResponseBadRequest,JsonResponse,HttpResponseForbidden
from django.contrib.auth import authenticate,login ,logout,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django import forms
from django.template import RequestContext
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.forms import PasswordChangeForm 
from django.contrib.auth.models import User
from django.utils.datastructures import MultiValueDictKeyError

from app.models import UserID
from app.forms import UserRegisterForm,UserProfileForm,InfoForm,OrgInfoForm

import jpype
import traceback
import os
import json
from time import time
from urlparse import urljoin

def index(request):
    context_dict={}
    return render(request, 'app/index.html',context_dict)

def about(request):
    context_dict={}
    return render(request, 'app/about.html',context_dict)

def home(request):
    context_dict={}
    return render(request, 'app/home.html',context_dict)

def validate(request):
    if request.user.is_authenticated():
        context_dict={}
        if request.method == 'POST':
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =os.path.abspath(".")+"/tool.jar"
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ If JVM started, attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            verifyclass = package.Verify
            try :
                if request.FILES["file"]:
                    """ Saving file to the media directory """
                    myfile = request.FILES['file']
                    folder = str(request.user) + "/" + str(int(time())) 
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,base_url=urljoin(settings.MEDIA_URL, folder+'/'))
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    """ Call the java function with parameters as list"""
                    retval = verifyclass.verify(str(settings.APP_DIR+uploaded_file_url))
                    """ If any error or warnings are returned"""
                    if (len(retval) > 0):
                        if (request.is_ajax()):
                            ajaxdict=dict()
                            ajaxdict["data"] = "The following error(s)/warning(s) were raised: " + str(retval)
                            response = json.dumps(ajaxdict)
                            jpype.detachThreadFromJVM()
                            return HttpResponse(response,status=400)
                        context_dict["error"] = retval
                        jpype.detachThreadFromJVM()
                        return render(request, 'app/validate.html',context_dict,status=400)
                    if (request.is_ajax()):
                        ajaxdict=dict()
                        ajaxdict["data"] = "This SPDX Document is valid."
                        response = json.dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response,status=200)
                    jpype.detachThreadFromJVM()
                    return HttpResponse("This SPDX Document is valid.",status=200)
                else :
                    if (request.is_ajax()):
                        ajaxdict=dict()
                        ajaxdict["data"] = "No file uploaded"
                        response = json.dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response,status=404)
                    context_dict["error"] = "No file uploaded"
                    jpype.detachThreadFromJVM()
                    return render(request, 'app/validate.html',context_dict,status=404)
            except jpype.JavaException,ex :
                """ Error raised by verifyclass.verify without exiting the application"""
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = jpype.JavaException.message(ex)
                    response = json.dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=400)
                context_dict["error"] = jpype.JavaException.message(ex)
                jpype.detachThreadFromJVM()
                return render(request, 'app/validate.html',context_dict,status=400)
            except MultiValueDictKeyError:
                """ If no files uploaded"""
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = "No files selected." 
                    response = json.dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=404)
                context_dict["error"] = "No files selected." 
                jpype.detachThreadFromJVM()    
                return render(request, 'app/validate.html',context_dict,status=404)
            except :
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = traceback.format_exc() 
                    response = json.dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=400)
                context_dict["error"] = traceback.format_exc() 
                jpype.detachThreadFromJVM()    
                return render(request, 'app/validate.html',context_dict,status=400)
        else :
            return render(request, 'app/validate.html',context_dict)
    else :
        return HttpResponseRedirect(settings.LOGIN_URL)

def compare(request):
    if request.user.is_authenticated():
        context_dict={}
        if request.method == 'POST':
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =os.path.abspath(".")+"/tool.jar"
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ If JVM started, attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            verifyclass = package.Verify
            compareclass = package.CompareMultpleSpdxDocs
            ajaxdict = dict()
            filelist = list()
            errorlist = list()
            if 'compare' in request.POST:
                try:
                    if request.FILES["file1"]:
                        nofile = int(request.POST["nofile"])
                        rfilename = request.POST["rfilename"]+".xlsx"
                        folder = str(request.user)+"/"+ str(int(time()))
                        callfunc = [settings.MEDIA_ROOT+"/"+folder + "/" +rfilename]
                        erroroccurred = False
                        fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,base_url=urljoin(settings.MEDIA_URL, folder+'/'))
                        for i in range(1,nofile+1):
                            """ Check if file selected or not"""
                            try:
                                a = 'file'+str(i)
                                myfile = request.FILES['file'+str(i)]
                            except MultiValueDictKeyError:
                                """ If no files uploaded""" 
                                if (request.is_ajax()):
                                    filelist.append("File " + str(i) + " not selected.")
                                    errorlist.append("Please select a file.")
                                    ajaxdict["files"] = filelist
                                    ajaxdict["errors"] = errorlist 
                                    response = json.dumps(ajaxdict)
                                    jpype.detachThreadFromJVM()
                                    return HttpResponse(response,status=404)
                                context_dict["error"] = "No files selected."
                                jpype.detachThreadFromJVM()
                                return render(request, 'app/compare.html',context_dict,status=404)
                            """ If file exist and uploaded, save it"""    
                            filename = fs.save(myfile.name, myfile)
                            uploaded_file_url = fs.url(filename)
                            callfunc.append(settings.APP_DIR+uploaded_file_url)
                            try : 
                                retval = verifyclass.verifyRDFFile(settings.APP_DIR+uploaded_file_url)
                                if (len(retval) > 0):
                                    erroroccurred = True
                                    filelist.append(myfile.name)
                                    errorlist.append(str(retval))
                                else :
                                    filelist.append(myfile.name)
                                    errorlist.append("No errors found")
                            except jpype.JavaException,ex :
                                """ Error raised by verifyclass.verify without exiting the application"""
                                erroroccurred = True
                                filelist.append(myfile.name)
                                errorlist.append(jpype.JavaException.message(ex))
                            except :
                                """ Other Exceptions"""
                                erroroccurred = True
                                filelist.append(myfile.name)
                                errorlist.append(traceback.format_exc())
                        """ If no errors in any of the file"""        
                        if (erroroccurred==False):
                            """ Call the java function with parameters as list"""
                            compareclass.onlineFunction(callfunc)
                            if (request.is_ajax()):
                                newajaxdict=dict()
                                newajaxdict["medialink"] = "/media/" + folder + "/" + rfilename
                                response = json.dumps(newajaxdict)
                                jpype.detachThreadFromJVM()
                                return HttpResponse(response)
                            context_dict['Content-Disposition'] = 'attachment; filename='+rfilename 
                            jpype.detachThreadFromJVM()   
                            return HttpResponseRedirect("/media/"+ folder + "/" +rfilename)
                        else :
                            if (request.is_ajax()):
                                ajaxdict["files"] = filelist
                                ajaxdict["errors"] = errorlist
                                response = json.dumps(ajaxdict)
                                jpype.detachThreadFromJVM()
                                return HttpResponse(response,status=400)
                            context_dict["error"]= errorlist
                            jpype.detachThreadFromJVM()
                            return render(request, 'app/compare.html',context_dict,status=400)
                    else :
                        context_dict["error"]= "File Not Uploaded"
                        jpype.detachThreadFromJVM()
                        return render(request, 'app/compare.html',context_dict,status=404)
                except MultiValueDictKeyError:
                    """ If no files uploaded""" 
                    if (request.is_ajax()):
                        filelist.append("File-1 not selected.")
                        errorlist.append("Please select a file.")
                        ajaxdict["files"] = filelist
                        ajaxdict["errors"] = errorlist 
                        response = json.dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response,status=404)
                    context_dict["error"] = "No files selected."
                    jpype.detachThreadFromJVM()
                    return render(request, 'app/compare.html',context_dict,status=404)

            elif 'compareall' in request.POST:
                try:
                    if request.FILES["files"]:
                        rfilename = request.POST["rfilename2"]+".xlsx"
                        folder = str(request.user)+"/"+ str(int(time()))
                        callfunc = [settings.MEDIA_ROOT+"/"+folder + "/" +rfilename]
                        erroroccurred = False
                        if (len(request.FILES.getlist("files"))<2):
                            context_dict["error"]= "Please select atleast 2 files"
                            jpype.detachThreadFromJVM()
                            return render(request, 'app/compare.html',context_dict)
                        # loop through the list of files
                        folder = str(request.user) + "/" + str(int(time()))
                        fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,base_url=urljoin(settings.MEDIA_URL, folder+'/')) 
                        for myfile in request.FILES.getlist("files"):
                            filename = fs.save(myfile.name, myfile)
                            uploaded_file_url = fs.url(filename)
                            callfunc.append(settings.APP_DIR+uploaded_file_url)
                            try :
                                retval = verifyclass.verifyRDFFile(settings.APP_DIR+uploaded_file_url)
                                if (len(retval) > 0):
                                    erroroccurred = True
                                    filelist.append(myfile.name)
                                    errorlist.append(str(retval))
                                else :
                                    filelist.append(myfile.name)
                                    errorlist.append("No errors found")
                            except jpype.JavaException,ex :
                                """ Error raised by verifyclass.verify without exiting the application"""
                                erroroccurred = True
                                filelist.append(myfile.name)
                                errorlist.append(jpype.JavaException.message(ex))
                            except :
                                """ Other Exceptions"""
                                erroroccurred = True
                                filelist.append(myfile.name)
                                errorlist.append(traceback.format_exc())
                        """ If no errors in any of the file"""        
                        if (erroroccurred==False):
                            """ Call the java function with parameters as list"""
                            compareclass.onlineFunction(callfunc)
                            if (request.is_ajax()):
                                newajaxdict=dict()
                                newajaxdict["medialink"] = "/media/" + folder + "/"+ rfilename
                                response = json.dumps(newajaxdict)
                                jpype.detachThreadFromJVM()
                                return HttpResponse(response)
                            context_dict['Content-Disposition'] = 'attachment; filename='+rfilename 
                            jpype.detachThreadFromJVM()
                            return HttpResponseRedirect("/media/"+ folder + "/"+rfilename)
                        else :
                            if (request.is_ajax()):
                                ajaxdict["files"] = filelist
                                ajaxdict["errors"] = errorlist
                                response = json.dumps(ajaxdict)
                                jpype.detachThreadFromJVM()
                                return HttpResponse(response,status=400)   
                            context_dict["error"] = errorlist
                            jpype.detachThreadFromJVM()
                            return render(request, 'app/compare.html',context_dict,status=400)
                    else :
                        context_dict["error"]= "File Not Uploaded"
                        jpype.detachThreadFromJVM()
                        return render(request, 'app/compare.html',context_dict,status=404)
                except MultiValueDictKeyError:
                    """ If no files uploaded""" 
                    if (request.is_ajax()):
                        filelist.append("Files not selected.")
                        errorlist.append("Please select atleast 2 files.")
                        ajaxdict["files"] = filelist
                        ajaxdict["errors"] = errorlist 
                        response = json.dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response,status=404)
                    context_dict["error"] = "Select atleast two files"
                    jpype.detachThreadFromJVM()
                    return render(request, 'app/compare.html',context_dict,status=404)
            else :
                context_dict["error"] = "Not a valid request"
                return render(request, 'app/compare.html',context_dict,status=404)
        else :
            return render(request, 'app/compare.html',context_dict)
    else :
        return HttpResponseRedirect(settings.LOGIN_URL)

def getFileFormat(to_format):
    if (to_format=="Tag"):
        return ".spdx"
    elif (to_format=="RDF"):
        return ".rdf"
    elif (to_format=="Spreadsheet"):
        return ".xlsx"
    elif (to_format=="HTML"):
        return ".html"
    else :
        return ".invalid"

def convert(request):
    if request.user.is_authenticated():
        context_dict={}
        if request.method == 'POST':
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =os.path.abspath(".")+"/tool.jar"
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ If JVM started, attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            try :
                if request.FILES["file"]:
                    """ Saving file to the media directory """
                    folder = str(request.user) + "/" + str(int(time())) 
                    myfile = request.FILES['file']
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,base_url=urljoin(settings.MEDIA_URL, folder+'/'))
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    option1 = request.POST["from_format"]
                    option2 = request.POST["to_format"]
                    functiontocall = option1 + "To" + option2
                    if "cfileformat" in request.POST :
                        cfileformat = request.POST["cfileformat"]
                    else :
                        cfileformat = getFileFormat(option2)
                    convertfile =  request.POST["cfilename"] + cfileformat
                    if (option1=="Tag"):
                        print ("Verifing for Tag/Value Document")
                        print(option2)
                        if (option2=="RDF"):
                            tagtordfclass = package.TagToRDF
                            retval = tagtordfclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+convertfile])
                            if (len(retval) > 0):
                                if (request.is_ajax()):
                                    ajaxdict=dict()
                                    ajaxdict["data"] = "The following error(s)/warning(s) were raised by "+ myfile.name + ": " + str(retval)
                                    response = json.dumps(ajaxdict)
                                    jpype.detachThreadFromJVM()
                                    return HttpResponse(response,status=404)
                                context_dict["error"] = str(retval)
                                print ("here")
                                print(retval)
                                jpype.detachThreadFromJVM()
                                return render(request, 'app/convert.html',context_dict,status=404)
                        elif (option2=="Spreadsheet"):
                            tagtosprdclass = package.TagToSpreadsheet
                            retval = tagtosprdclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                            if (len(retval) > 0):
                                if (request.is_ajax()):
                                    ajaxdict=dict()
                                    ajaxdict["data"] = "The following error(s)/warning(s) were raised by "+ myfile.name + ": " + str(retval)
                                    response = json.dumps(ajaxdict)
                                    jpype.detachThreadFromJVM()
                                    return HttpResponse(response,status=404)
                                context_dict["error"] = retval
                                jpype.detachThreadFromJVM()
                                return render(request, 'app/convert.html',context_dict,status=404)
                        else :
                            jpype.detachThreadFromJVM()
                            context_dict["error"] = "Select the available conversion types."
                            return render(request, 'app/convert.html',context_dict,status=400)
                    elif (option1=="RDF"):
                        print ("Verifing for RDF Document")
                        if (option2=="Tag"):
                            rdftotagclass = package.RdfToTag
                            retval = rdftotagclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                            if (len(retval) > 0):
                                if (request.is_ajax()):
                                    ajaxdict=dict()
                                    ajaxdict["data"] = "The following error(s)/warning(s) were raised by "+ myfile.name + ": " + str(retval)
                                    response = json.dumps(ajaxdict)
                                    jpype.detachThreadFromJVM()
                                    return HttpResponse(response,status=404)
                                context_dict["error"] = retval
                                jpype.detachThreadFromJVM()
                                return render(request, 'app/convert.html',context_dict,status=404)
                        elif (option2=="Spreadsheet"):
                            rdftosprdclass = package.RdfToSpreadsheet
                            retval = rdftosprdclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                            if (len(retval) > 0):
                                if (request.is_ajax()):
                                    ajaxdict=dict()
                                    ajaxdict["data"] = "The following error(s)/warning(s) were raised by "+ myfile.name + ": " + str(retval)
                                    response = json.dumps(ajaxdict)
                                    jpype.detachThreadFromJVM()
                                    return HttpResponse(response,status=404)
                                context_dict["error"] = retval
                                jpype.detachThreadFromJVM()
                                return render(request, 'app/convert.html',context_dict,status=404)
                        elif (option2=="HTML"):
                            rdftohtmlclass = package.RdfToHtml
                            retval = rdftohtmlclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                            if (len(retval) > 0):
                                if (request.is_ajax()):
                                    ajaxdict=dict()
                                    ajaxdict["data"] = "The following error(s)/warning(s) were raised by "+ myfile.name + ": " + str(retval)
                                    response = json.dumps(ajaxdict)
                                    jpype.detachThreadFromJVM()
                                    return HttpResponse(response,status=404)
                                context_dict["error"] = retval
                                jpype.detachThreadFromJVM()
                                return render(request, 'app/convert.html',context_dict,status=404)
                        else :
                            jpype.detachThreadFromJVM()
                            context_dict["error"] = "Select the available conversion types."
                            return render(request, 'app/convert.html',context_dict,status=400)
                    elif (option1=="Spreadsheet"):
                        print ("Verifing for Spreadsheet Document")
                        if (option2=="Tag"):
                            sprdtotagclass = package.SpreadsheetToTag
                            retval = sprdtotagclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                            if (len(retval) > 0):
                                if (request.is_ajax()):
                                    ajaxdict=dict()
                                    ajaxdict["data"] = "The following error(s)/warning(s) were raised by "+ myfile.name + ": " + str(retval)
                                    response = json.dumps(ajaxdict)
                                    jpype.detachThreadFromJVM()
                                    return HttpResponse(response,status=404)
                                context_dict["error"] = retval
                                jpype.detachThreadFromJVM()
                                return render(request, 'app/convert.html',context_dict,status=404)
                        elif (option2=="RDF"):
                            sprdtordfclass = package.SpreadsheetToRDF
                            retval = sprdtordfclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                            if (len(retval) > 0):
                                if (request.is_ajax()):
                                    ajaxdict=dict()
                                    ajaxdict["data"] = "The following error(s)/warning(s) were raised by "+ myfile.name + ": " + str(retval)
                                    response = json.dumps(ajaxdict)
                                    jpype.detachThreadFromJVM()
                                    return HttpResponse(response,status=404)
                                context_dict["error"] = retval
                                jpype.detachThreadFromJVM()
                                return render(request, 'app/convert.html',context_dict,status=404)
                        else :
                            jpype.detachThreadFromJVM()
                            context_dict["error"] = "Select the available conversion types."
                            return render(request, 'app/convert.html',context_dict,status=400)
                    if (request.is_ajax()):
                        ajaxdict=dict()
                        ajaxdict["medialink"] = "/media/" + folder + "/"+ convertfile
                        response = json.dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response)
                    context_dict['Content-Disposition'] = 'attachment; filename='+convertfile
                    jpype.detachThreadFromJVM()
                    return HttpResponseRedirect("/media/" + folder + "/" + convertfile)
                else :
                    context_dict["error"] = "No file uploaded"
                    jpype.detachThreadFromJVM()
                    return render(request, 'app/convert.html',context_dict,status=404)
            except jpype.JavaException,ex :
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = jpype.JavaException.message(ex)
                    response = json.dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=400)
                context_dict["error"] = jpype.JavaException.message(ex)
                jpype.detachThreadFromJVM()
                return render(request, 'app/convert.html',context_dict,status=400)
            except MultiValueDictKeyError:
                """ If no files uploaded"""
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = "No files selected." 
                    response = json.dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=404)
                context_dict["error"] = "No files selected." 
                jpype.detachThreadFromJVM()    
                return render(request, 'app/convert.html',context_dict,status=404)
            except :
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = traceback.format_exc()
                    response = json.dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=400)
                context_dict["error"] = traceback.format_exc()
                jpype.detachThreadFromJVM()    
                return render(request, 'app/convert.html',context_dict,status=400)
        else :
            return render(request, 'app/convert.html',context_dict)
    else :
        return HttpResponseRedirect(settings.LOGIN_URL)

def check_license(request):
    if request.user.is_authenticated():
        context_dict={}
        if request.method == 'POST':
            licensetext = request.POST.get('licensetext')
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =os.path.abspath(".")+"/tool.jar"
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ If JVM started, attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.compare")
            compareclass = package.LicenseCompareHelper
            try:
                matching_licenses = compareclass.matchingStandardLicenseIds(licensetext)
                if (matching_licenses and len(matching_licenses) > 0):
                    matching_str = "The following license ID(s) match: "
                    matching_str+= matching_licenses[0]
                    for i in range(1,len(matching_licenses)):
                        matching_str += ", "
                        matching_str += matching_licenses[i]
                    if (request.is_ajax()):
                        ajaxdict=dict()
                        ajaxdict["data"] = matching_str
                        response = json.dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(matching_str)
                else:
                    if (request.is_ajax()):
                        ajaxdict=dict()
                        ajaxdict["data"] = "There are no matching SPDX listed licenses"
                        response = json.dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response,status=404)
                    jpype.detachThreadFromJVM()
                    return HttpResponse("There are no matching SPDX listed licenses")
            except jpype.JavaException,ex :
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = jpype.JavaException.message(ex)
                    response = json.dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=404)
                context_dict["error"] = jpype.JavaException.message(ex)
                jpype.detachThreadFromJVM()
                return HttpResponse(context_dict,status=404)
            except :
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = traceback.format_exc()
                    response = json.dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=404)
                context_dict["error"] = traceback.format_exc()
                jpype.detachThreadFromJVM()    
                return HttpResponse(context_dict,status=404)
        else:
            return render(request, 'app/check_license.html',context_dict)
    else:
        return HttpResponseRedirect(settings.LOGIN_URL)

def loginuser(request):
    context_dict={}
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user and user.is_staff:
            #add status  choice here
            if user.is_active:
                login(request, user)
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = "Success"
                    ajaxdict["next"] = "/app/"
                    response = json.dumps(ajaxdict)
                    return HttpResponse(response)
                return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
            else:
                if (request.is_ajax()):
                    return HttpResponse("Your account is disabled.",status=401)
                context_dict["invalid"] = "Your account is disabled."
                return render(request,"app/login.html",context_dict,status=401)	
        else:
            if (request.is_ajax()):
                return HttpResponse("Invalid login details supplied.",status=403)
            context_dict['invalid']="Invalid login details supplied."
            return render(request, 'app/login.html',context_dict,status=403)
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
            return HttpResponseRedirect(settings.REGISTER_REDIRECT_UTL)
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
    return HttpResponseRedirect("/app/login/")

def profile(request):
    if request.user.is_authenticated():
        context_dict={}
        profile = UserID.objects.get(user=request.user)
        info_form = InfoForm(instance=request.user)
        orginfo_form = OrgInfoForm(instance=profile)
        form = PasswordChangeForm(request.user)
        context_dict["form"] = form
        context_dict["info_form"] = info_form
        context_dict["orginfo_form"] = orginfo_form
        if request.method == 'POST':
            if "saveinfo" in request.POST :
                info_form = InfoForm(request.POST,instance=request.user)
                orginfo_form = OrgInfoForm(request.POST,instance=profile)
                if info_form.is_valid() and orginfo_form.is_valid():
                    form1 = info_form.save()
                    form2 = orginfo_form.save()
                    context_dict["success"] = "Details Successfully Updated"
                    return render(request,'app/profile.html',context_dict)
                else :
                    context_dict["error"] = "Error changing details " + str(info_form.errors) + str(orginfo_form.errors)
                    return render(request,'app/profile.html',context_dict)
            if "changepwd" in request.POST:
                form = PasswordChangeForm(request.user, request.POST)
                if form.is_valid():
                    user = form.save()
                    update_session_auth_hash(request, user)  # Important!
                    context_dict["success"] = 'Your password was successfully updated!'
                    return render(request,'app/profile.html',context_dict)
                else:
                    context_dict["error"] = form.errors
                    return render(request,'app/profile.html',context_dict)
        else:
            return render(request,'app/profile.html',context_dict)
    else:
        return HttpResponseRedirect(settings.LOGIN_URL)

def password_reset(request):
    context_dict={}
    return render(request,'app/password_reset.html',context_dict)

def checkusername(request):
    if 'username' in request.POST:
        users = User.objects.filter(username=request.POST["username"])
        if (len(users)>0):
            return HttpResponse(json.dumps({"data": "Already Exist."}),status=404)
        else :
            return HttpResponse(json.dumps({"data": "Success"})) 
    else :
        return HttpResponse(json.dumps({"data": "No username entered"}))


def handler400(request):
    return render_to_response('app/400.html',
        context_instance = RequestContext(request)
    )

def handler403(request):
    return render_to_response('app/403.html',
        context_instance = RequestContext(request)
    )

def handler404(request):
    return render_to_response('app/404.html',
        context_instance = RequestContext(request)
    )
    
def handler500(request):
    return render_to_response('app/500.html',
        context_instance = RequestContext(request)
    )
