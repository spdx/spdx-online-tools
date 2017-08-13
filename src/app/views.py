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
from django.contrib.auth import authenticate,login ,logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django import forms
from django.template import RequestContext
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

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

def validate(request):
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
                print (uploaded_file_url)
                """ Call the java function with parameters as list"""
                retval = verifyclass.verify(settings.APP_DIR+uploaded_file_url)
                """ If any error or warnings are returned"""
                if (len(retval) > 0):
                    if (request.is_ajax()):
                        ajaxdict=dict()
                        ajaxdict["data"] = "The following error(s)/warning(s) were raised: " + str(retval)
                        response = json.dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response,status=400)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(retval)
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = "This SPDX Document is valid."
                    response = json.dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response)
                jpype.detachThreadFromJVM()
                return HttpResponse("This SPDX Document is valid.")
            else :
                jpype.detachThreadFromJVM()
                return HttpResponse("File Not Uploaded")
        except jpype.JavaException,ex :
            """ Error raised by verifyclass.verify without exiting the application"""
            context_dict["error"] = jpype.JavaException.message(ex) # "This SPDX Document is not a valid RDF/XML or tag/value format"
            if (request.is_ajax()):
                ajaxdict=dict()
                ajaxdict["data"] = jpype.JavaException.message(ex)
                response = json.dumps(ajaxdict)
                jpype.detachThreadFromJVM()
                return HttpResponse(response,status=400)
            jpype.detachThreadFromJVM()
            return render(request, 'app/validate.html',context_dict)
        except :
            traceback.print_exc()
            context_dict["error"] = "Other Exception Raised." 
            if (request.is_ajax()):
                ajaxdict=dict()
                ajaxdict["data"] = "Other Exception Raised." 
                response = json.dumps(ajaxdict)
                jpype.detachThreadFromJVM()
                return HttpResponse("Other Exception Raised.",status=400)
            jpype.detachThreadFromJVM()    
            return render(request, 'app/validate.html',context_dict)
    else :
        return render(request, 'app/validate.html',context_dict)

def compare(request):
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
        if 'compare' in request.POST:
            if request.FILES["file1"]:
                nofile = int(request.POST["nofile"])
                rfilename = request.POST["rfilename"]+".xlsx"
                folder = str(request.user)+"/"+ str(int(time()))
                callfunc = [settings.MEDIA_ROOT+"/"+folder + "/" +rfilename]
                ajaxdict = dict()
                filelist = list()
                errorlist = list()
                erroroccurred = False
                fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,base_url=urljoin(settings.MEDIA_URL, folder+'/'))
                for i in range(1,nofile+1):
                    """ Saving file to the media directory """
                    try:
                        a = 'file'+str(i)
                        myfile = request.FILES['file'+str(i)]
                    except:
                        traceback.print_exc()
                        return HttpResponse("File does not exist",status=404)
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
                        traceback.print_exc()
                        erroroccurred = True
                        filelist.append(myfile.name)
                        errorlist.append("Other Excpetion Raised")
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
                    jpype.detachThreadFromJVM()
                    context_dict['Content-Disposition'] = 'attachment; filename='+rfilename    
                    return HttpResponseRedirect("/media/"+ folder + "/" +rfilename)
                else :
                    if (request.is_ajax()):
                        ajaxdict["files"] = filelist
                        ajaxdict["errors"] = errorlist
                        response = json.dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response,status=404)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(errorlist)
            else :
                jpype.detachThreadFromJVM()
                return HttpResponse("File Not Uploaded",status=404)
        elif 'compareall' in request.POST:
            if request.FILES["files"]:
                rfilename = request.POST["rfilename2"]+".xlsx"
                folder = str(request.user)+"/"+ str(int(time()))
                callfunc = [settings.MEDIA_ROOT+"/"+folder + "/" +rfilename]
                ajaxdict = dict()
                filelist = list()
                errorlist = list()
                erroroccurred = False
                if (len(request.FILES.getlist("files"))<2):
                    jpype.detachThreadFromJVM()    
                    context_dict["error"]= "Please select atleast 2 files"
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
                        traceback.print_exc()
                        erroroccurred = True
                        filelist.append(myfile.name)
                        errorlist.append("Other Exception Raised")
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
                        return HttpResponse(response,status=404)   
                    jpype.detachThreadFromJVM()
                return HttpResponse(errorlist)
            else :
                jpype.detachThreadFromJVM()
                return HttpResponse("File Not Uploaded",status=404)
    else :
        return render(request, 'app/compare.html',context_dict)

def convert(request):
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
                convertfile =  request.POST["cfilename"]+request.POST["cfileformat"]
                option1 = request.POST["from_format"]
                option2 = request.POST["to_format"]
                functiontocall = option1 + "To" + option2
                if (option1=="Tag"):
                    print ("Verifing for Tag/Value Document")
                    if (option2=="RDF"):
                        tagtordfclass = package.TagToRDF
                        retval = tagtordfclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+convertfile])
                        if (len(retval) > 0):
                            if (request.is_ajax()):
                                ajaxdict=dict()
                                ajaxdict["data"] = "The following error(s)/warning(s) were raised by "+ myfile.name + ": " + str(retval)
                                response = json.dumps(ajaxdict)
                                jpype.detachThreadFromJVM()
                                return HttpResponse(response,status=400)
                            jpype.detachThreadFromJVM()
                            return HttpResponse(retval)
                    elif (option2=="Spreadsheet"):
                        tagtosprdclass = package.TagToSpreadsheet
                        retval = tagtosprdclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                        if (len(retval) > 0):
                            if (request.is_ajax()):
                                ajaxdict=dict()
                                ajaxdict["data"] = "The following error(s)/warning(s) were raised by "+ myfile.name + ": " + str(retval)
                                response = json.dumps(ajaxdict)
                                jpype.detachThreadFromJVM()
                                return HttpResponse(response,status=400)
                            jpype.detachThreadFromJVM()
                            return HttpResponse(retval)
                    else :
                        return HttpResponse("Select the available conversion types.")
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
                                return HttpResponse(response,status=400)
                            jpype.detachThreadFromJVM()
                            return HttpResponse(retval)
                    elif (option2=="Spreadsheet"):
                        rdftosprdclass = package.RdfToSpreadsheet
                        retval = rdftosprdclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                        if (len(retval) > 0):
                            if (request.is_ajax()):
                                ajaxdict=dict()
                                ajaxdict["data"] = "The following error(s)/warning(s) were raised by "+ myfile.name + ": " + str(retval)
                                response = json.dumps(ajaxdict)
                                jpype.detachThreadFromJVM()
                                return HttpResponse(response,status=400)
                            jpype.detachThreadFromJVM()
                            return HttpResponse(retval)
                    elif (option2=="HTML"):
                        rdftohtmlclass = package.RdfToHtml
                        retval = rdftohtmlclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                        if (len(retval) > 0):
                            if (request.is_ajax()):
                                ajaxdict=dict()
                                ajaxdict["data"] = "The following error(s)/warning(s) were raised by "+ myfile.name + ": " + str(retval)
                                response = json.dumps(ajaxdict)
                                jpype.detachThreadFromJVM()
                                return HttpResponse(response,status=400)
                            jpype.detachThreadFromJVM()
                            return HttpResponse(retval)
                    else :
                        return HttpResponse("Select the available conversion types.")
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
                                return HttpResponse(response,status=400)
                            jpype.detachThreadFromJVM()
                            return HttpResponse(retval)
                    elif (option2=="RDF"):
                        sprdtordfclass = package.SpreadsheetToRDF
                        retval = sprdtordfclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                        if (len(retval) > 0):
                            if (request.is_ajax()):
                                ajaxdict=dict()
                                ajaxdict["data"] = "The following error(s)/warning(s) were raised by "+ myfile.name + ": " + str(retval)
                                response = json.dumps(ajaxdict)
                                jpype.detachThreadFromJVM()
                                return HttpResponse(response,status=400)
                            jpype.detachThreadFromJVM()
                            return HttpResponse(retval)
                    else :
                        return HttpResponse("Select the available conversion types.")
                """ Call the java function with parameters as list"""
                context_dict['Content-Disposition'] = 'attachment; filename='+convertfile
                if (request.is_ajax()):
                        ajaxdict=dict()
                        ajaxdict["medialink"] = "/media/" + folder + "/"+ convertfile
                        response = json.dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response)
                jpype.detachThreadFromJVM()
                return HttpResponseRedirect("/media/" + folder + "/" + convertfile)
            else :
                jpype.detachThreadFromJVM()
                return HttpResponse("File Not Uploaded",status=404)
        except jpype.JavaException,ex :
            context_dict["error"] = jpype.JavaException.message(ex)
            if (request.is_ajax()):
                ajaxdict=dict()
                ajaxdict["data"] = jpype.JavaException.message(ex)
                response = json.dumps(ajaxdict)
                jpype.detachThreadFromJVM()
                return HttpResponse(response,status=400)
            jpype.detachThreadFromJVM()
            return render(request, 'app/convert.html',context_dict)
        except :
            traceback.print_exc()
            context_dict["error"] = "Other Exception Raised."
            if (request.is_ajax()):
                ajaxdict=dict()
                ajaxdict["data"] = "Other Exception Raised."
                response = json.dumps(ajaxdict)
                jpype.detachThreadFromJVM()
                return HttpResponse(response,status=400)
            jpype.detachThreadFromJVM()    
            return render(request, 'app/convert.html',context_dict)
    else :
        return render(request, 'app/convert.html',context_dict)

def check_license(request):
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
                jpype.detachThreadFromJVM()
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = "There are no matching SPDX listed licenses"
                    response = json.dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=400)
                return HttpResponse("There are no matching SPDX listed licenses")
        except jpype.JavaException,ex :
            context_dict["error"] = jpype.JavaException.message(ex)
            if (request.is_ajax()):
                ajaxdict=dict()
                ajaxdict["data"] = jpype.JavaException.message(ex)
                response = json.dumps(ajaxdict)
                jpype.detachThreadFromJVM()
                return HttpResponse(response,status=400)
            jpype.detachThreadFromJVM()
            return render(request, 'app/check_license.html',context_dict)
        except :
            traceback.print_exc()
            context_dict["error"] = "Other Exception Raised."
            if (request.is_ajax()):
                ajaxdict=dict()
                ajaxdict["data"] = "Other Exception Raised."
                response = json.dumps(ajaxdict)
                jpype.detachThreadFromJVM()
                return HttpResponse(response,status=400)
            jpype.detachThreadFromJVM()    
            return render(request, 'app/check_license.html',context_dict)
    else:
        return render(request, 'app/check_license.html',context_dict)

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
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = "Success"
                    ajaxdict["next"] = "/app/"
                    response = json.dumps(ajaxdict)
                    return HttpResponse(response)
                return HttpResponseRedirect('/app/')
            else:
                if (request.is_ajax()):
                    return HttpResponseForbidden("Your account is disabled.")
                return HttpResponse("Your account is disabled.")	
        else:
            if (request.is_ajax()):
                return HttpResponseForbidden("Invalid login details supplied.")
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
    return HttpResponseRedirect("/app/login/")

def profile(request):
    context_dict={}
    profile = UserID.objects.get(user=request.user)
    if request.method == 'POST':
        if "saveinfo" in request.POST :
            info_form = InfoForm(request.POST,instance=request.user)
            orginfo_form = OrgInfoForm(request.POST,instance=profile)
            if info_form.is_valid() and orginfo_form.is_valid():
                form1 = info_form.save()
                form2 = orginfo_form.save()
                context_dict["success"] = "Details Successfully Updated"
                info_form = InfoForm(instance=request.user)
                orginfo_form = OrgInfoForm(instance=profile)
                form = PasswordChangeForm(request.user)
                context_dict["form"] = form
                context_dict["info_form"] = info_form
                context_dict["orginfo_form"] = orginfo_form
                return render(request,'app/profile.html',context_dict)
            else :
                context_dict["error"] = "Error changing details" + str(info_form.errors) + str(orginfo_form.errors)
                return render(request,'app/profile.html',context_dict)
        if "changepwd" in request.POST:
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Important!
                context_dict["success"] = 'Your password was successfully updated!'
                context_dict["form"] = form
            else:
                context_dict["error"] = form.errors
                context_dict["form"] = form
    else:
        info_form = InfoForm(instance=request.user)
        orginfo_form = OrgInfoForm(instance=profile)
        form = PasswordChangeForm(request.user)
        context_dict["form"] = form
        context_dict["info_form"] = info_form
        context_dict["orginfo_form"] = orginfo_form
    return render(request,'app/profile.html',context_dict)
