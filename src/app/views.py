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
from django.http import HttpResponse,HttpResponseRedirect
from django.contrib.auth import authenticate,login ,logout,update_session_auth_hash
from django.conf import settings
from django import forms
from django.template import RequestContext
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.forms import PasswordChangeForm 
from django.contrib.auth.models import User
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.decorators import login_required

import jpype
import requests
import re
import logging
from traceback import format_exc
from json import dumps, loads
from time import time
from urlparse import urljoin

from app.models import UserID
from app.forms import UserRegisterForm,UserProfileForm,InfoForm,OrgInfoForm

logging.basicConfig(filename="error.log", format="%(levelname)s : %(asctime)s : %(message)s")
logger = logging.getLogger()

def index(request):
    """ View for index
    returns index.html template
    """
    context_dict={}
    return render(request, 
        'app/index.html',context_dict
        )

def about(request):
    """ View for about
    returns about.html template
    """
    context_dict={}
    return render(request, 
        'app/about.html',context_dict
        )

def validate(request):
    """ View for validate tool
    returns validate.html template
    """
    if request.user.is_authenticated() or settings.ANONYMOUS_LOGIN_ENABLED:
        context_dict={}
        if request.method == 'POST':
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it."""
                classpath = settings.JAR_ABSOLUTE_PATH
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ Attach a Thread and start processing the request. """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            verifyclass = package.Verify
            ajaxdict=dict()
            try :
                if request.FILES["file"]:
                    """ Saving file to the media directory """
                    myfile = request.FILES['file']
                    folder = str(request.user) + "/" + str(int(time())) 
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,
                        base_url=urljoin(settings.MEDIA_URL, folder+'/')
                        )
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    """ Call the java function with parameters """
                    retval = verifyclass.verify(str(settings.APP_DIR+uploaded_file_url))
                    if (len(retval) > 0):
                        """ If any warnings are returned """
                        if (request.is_ajax()):
                            ajaxdict["type"] = "warning"
                            ajaxdict["data"] = "The following warning(s) were raised: " + str(retval)
                            response = dumps(ajaxdict)
                            jpype.detachThreadFromJVM()
                            return HttpResponse(response,status=400)
                        context_dict["error"] = retval
                        jpype.detachThreadFromJVM()
                        return render(request, 
                            'app/validate.html',context_dict,status=400
                            )
                    if (request.is_ajax()):
                        """ Valid SPDX Document """
                        ajaxdict["data"] = "This SPDX Document is valid."
                        response = dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response,status=200)
                    jpype.detachThreadFromJVM()
                    return HttpResponse("This SPDX Document is valid.",status=200)
                else :
                    """ If no file uploaded."""
                    if (request.is_ajax()):
                        ajaxdict=dict()
                        ajaxdict["type"] = "error"
                        ajaxdict["data"] = "No file uploaded"
                        response = dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response,status=404)
                    context_dict["error"] = "No file uploaded"
                    jpype.detachThreadFromJVM()
                    return render(request, 
                        'app/validate.html',context_dict,status=404
                        )
            except jpype.JavaException,ex :
                """ Error raised by verifyclass.verify without exiting the application"""
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["type"] = "error"
                    ajaxdict["data"] = jpype.JavaException.message(ex)
                    response = dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=400)
                context_dict["error"] = jpype.JavaException.message(ex)
                jpype.detachThreadFromJVM()
                return render(request, 
                    'app/validate.html',context_dict,status=400
                    )
            except MultiValueDictKeyError:
                """ If no files selected"""
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["type"] = "error"
                    ajaxdict["data"] = "No files selected." 
                    response = dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=404)
                context_dict["error"] = "No files selected." 
                jpype.detachThreadFromJVM()    
                return render(request,
                 'app/validate.html',context_dict,status=404
                 )
            except :
                """ Other error raised """
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["type"] = "error"
                    ajaxdict["data"] = format_exc() 
                    response = dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=400)
                context_dict["error"] = format_exc() 
                jpype.detachThreadFromJVM()    
                return render(request, 
                    'app/validate.html',context_dict,status=400
                    )
        else :
            """ GET,HEAD """
            return render(request,
             'app/validate.html',context_dict
             )
    else :
        return HttpResponseRedirect(settings.LOGIN_URL)

def compare(request):
    """ View for compare tool
    returns compare.html template
    """
    if request.user.is_authenticated() or settings.ANONYMOUS_LOGIN_ENABLED:
        context_dict={}
        if request.method == 'POST':
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =settings.JAR_ABSOLUTE_PATH
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ Attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            verifyclass = package.Verify
            compareclass = package.CompareMultpleSpdxDocs
            ajaxdict = dict()
            filelist = list()
            errorlist = list()
            try:
                if request.FILES["files"]:
                    rfilename = request.POST["rfilename"]+".xlsx"
                    folder = str(request.user)+"/"+ str(int(time()))
                    callfunc = [settings.MEDIA_ROOT+"/"+folder + "/" +rfilename]
                    erroroccurred = False
                    warningoccurred = False
                    if (len(request.FILES.getlist("files"))<2):
                        context_dict["error"]= "Please select atleast 2 files"
                        jpype.detachThreadFromJVM()
                        return render(request, 
                            'app/compare.html',context_dict, status=404
                            )
                    """Loop through the list of files"""
                    folder = str(request.user) + "/" + str(int(time()))
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,
                        base_url=urljoin(settings.MEDIA_URL, folder+'/')
                        ) 
                    for myfile in request.FILES.getlist("files"):
                        filename = fs.save(myfile.name, myfile)
                        uploaded_file_url = fs.url(filename)
                        callfunc.append(settings.APP_DIR+uploaded_file_url)
                        try :
                            """Call the java function to verify for valid RDF Files."""
                            retval = verifyclass.verifyRDFFile(settings.APP_DIR+uploaded_file_url)
                            if (len(retval) > 0):
                                """If warnings raised"""
                                warningoccurred = True
                                filelist.append(myfile.name)
                                errorlist.append(str(retval))
                            else :
                                filelist.append(myfile.name)
                                errorlist.append("No errors found")
                        except jpype.JavaException,ex :
                            """ Error raised by verifyclass.verifyRDFFile without exiting the application"""
                            erroroccurred = True
                            filelist.append(myfile.name)
                            errorlist.append(jpype.JavaException.message(ex))
                        except :
                            """ Other Exceptions"""
                            erroroccurred = True
                            filelist.append(myfile.name)
                            errorlist.append(format_exc())
    
                    if (erroroccurred==False):
                        """ If no errors in any of the file,call the java function with parameters as list"""
                        try :
                            compareclass.onlineFunction(callfunc)
                        except :
                            """Error raised by onlineFunction"""
                            if (request.is_ajax()):
                                ajaxdict["type"] = "warning2"
                                ajaxdict["files"] = filelist
                                ajaxdict["errors"] = errorlist
                                ajaxdict["toolerror"] = format_exc()
                                response = dumps(ajaxdict)
                                jpype.detachThreadFromJVM()
                                return HttpResponse(response,status=400)
                            context_dict["type"] = "warning2"
                            context_dict["error"]= errorlist
                            jpype.detachThreadFromJVM()
                            return render(request, 
                                'app/compare.html',context_dict,status=400
                                )
                        if (warningoccurred==False):
                            """If no warning raised """
                            if (request.is_ajax()):
                                ajaxdict["medialink"] = settings.MEDIA_URL + folder + "/"+ rfilename
                                response = dumps(ajaxdict)
                                jpype.detachThreadFromJVM()
                                return HttpResponse(response)
                            context_dict["Content-Type"] = "application/vnd.ms-excel"
                            context_dict['Content-Disposition'] = 'attachment; filename="{}"'.format(rfilename)
                            context_dict["medialink"] = settings.MEDIA_URL + folder + "/" + rfilename
                            jpype.detachThreadFromJVM()
                            return render(request, 
                                'app/compare.html',context_dict,status=200
                                )
                            #return HttpResponseRedirect(settings.MEDIA_URL+ folder + "/"+rfilename)
                        else :
                            if (request.is_ajax()):
                                ajaxdict["type"] = "warning"
                                ajaxdict["files"] = filelist
                                ajaxdict["errors"] = errorlist
                                ajaxdict["medialink"] = settings.MEDIA_URL + folder + "/" + rfilename
                                response = dumps(ajaxdict)
                                jpype.detachThreadFromJVM()
                                return HttpResponse(response,status=406)
                            context_dict["Content-Type"] = "application/vnd.ms-excel"
                            context_dict['Content-Disposition'] = 'attachment; filename="{}"'.format(rfilename)
                            context_dict["type"] = "warning"
                            context_dict["medialink"] = settings.MEDIA_URL + folder + "/" + rfilename
                            jpype.detachThreadFromJVM()   
                            return render(request, 
                                'app/compare.html',context_dict,status=406
                                )
                    else :
                        if (request.is_ajax()):
                            ajaxdict["files"] = filelist
                            ajaxdict["type"] = "error"
                            ajaxdict["errors"] = errorlist
                            response = dumps(ajaxdict)
                            jpype.detachThreadFromJVM()
                            return HttpResponse(response,status=400)   
                        context_dict["type"] = "error"
                        context_dict["error"] = errorlist
                        jpype.detachThreadFromJVM()
                        return render(request, 
                            'app/compare.html',context_dict,status=400
                            )
                else :
                    context_dict["error"]= "File Not Uploaded"
                    context_dict["type"] = "error"
                    jpype.detachThreadFromJVM()
                    return render(request, 
                        'app/compare.html',context_dict,status=404
                        )

            except MultiValueDictKeyError:
                """ If no files uploaded""" 
                if (request.is_ajax()):
                    filelist.append("Files not selected.")
                    errorlist.append("Please select atleast 2 files.")
                    ajaxdict["files"] = filelist
                    ajaxdict["type"] = "error"
                    ajaxdict["errors"] = errorlist 
                    response = dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=404)
                context_dict["error"] = "Select atleast two files"
                context_dict["type"] = "error"
                jpype.detachThreadFromJVM()
                return render(request, 
                    'app/compare.html',context_dict,status=404
                    )
        else :
            """GET,HEAD"""
            return render(request, 
                'app/compare.html',context_dict
                )
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
    """ View for convert tool
    returns convert.html template
    """
    if request.user.is_authenticated() or settings.ANONYMOUS_LOGIN_ENABLED:
        context_dict={}
        if request.method == 'POST':
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =settings.JAR_ABSOLUTE_PATH
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ Attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            ajaxdict=dict()
            try :
                if request.FILES["file"]:
                    """ Saving file to media directory """
                    folder = str(request.user) + "/" + str(int(time())) 
                    myfile = request.FILES['file']
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,base_url=urljoin(settings.MEDIA_URL, folder+'/'))
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    option1 = request.POST["from_format"]
                    option2 = request.POST["to_format"]
                    functiontocall = option1 + "To" + option2
                    warningoccurred = False
                    content_type =""
                    if "cfileformat" in request.POST :
                        cfileformat = request.POST["cfileformat"]
                    else :
                        cfileformat = getFileFormat(option2)
                    convertfile =  request.POST["cfilename"] + cfileformat
                    """ Call the java function with parameters as list """
                    if (option1=="Tag"):
                        print ("Verifing for Tag/Value Document")
                        if (option2=="RDF"):
                            option3 = request.POST["tagToRdfFormat"]
                            content_type = "application/rdf+xml"
                            tagtordfclass = package.TagToRDF
                            retval = tagtordfclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+convertfile, option3])
                            if (len(retval) > 0):
                                warningoccurred = True
                        elif (option2=="Spreadsheet"):
                            content_type = "application/vnd.ms-excel"
                            tagtosprdclass = package.TagToSpreadsheet
                            retval = tagtosprdclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                            if (len(retval) > 0):
                                warningoccurred = True
                        else :
                            jpype.detachThreadFromJVM()
                            context_dict["error"] = "Select the available conversion types."
                            return render(request, 
                                'app/convert.html',context_dict,status=400
                                )
                    elif (option1=="RDF"):
                        print ("Verifing for RDF Document")
                        if (option2=="Tag"):
                            content_type = "text/tag-value"
                            rdftotagclass = package.RdfToTag
                            retval = rdftotagclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                            if (len(retval) > 0):
                                warningoccurred = True
                        elif (option2=="Spreadsheet"):
                            content_type = "application/vnd.ms-excel"
                            rdftosprdclass = package.RdfToSpreadsheet
                            retval = rdftosprdclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                            if (len(retval) > 0):
                                warningoccurred = True
                        elif (option2=="HTML"):
                            content_type = "text/html"
                            rdftohtmlclass = package.RdfToHtml
                            retval = rdftohtmlclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                            if (len(retval) > 0):
                                warningoccurred = True
                        else :
                            jpype.detachThreadFromJVM()
                            context_dict["error"] = "Select the available conversion types."
                            return render(request, 
                                'app/convert.html',context_dict,status=400
                                )
                    elif (option1=="Spreadsheet"):
                        print ("Verifing for Spreadsheet Document")
                        if (option2=="Tag"):
                            content_type = "text/tag-value"
                            sprdtotagclass = package.SpreadsheetToTag
                            retval = sprdtotagclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                            if (len(retval) > 0):
                                warningoccurred = True
                        elif (option2=="RDF"):
                            content_type = "application/rdf+xml"
                            sprdtordfclass = package.SpreadsheetToRDF
                            retval = sprdtordfclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile])
                            if (len(retval) > 0):
                                warningoccurred = True
                        else :
                            jpype.detachThreadFromJVM()
                            context_dict["error"] = "Select the available conversion types."
                            return render(request, 
                                'app/convert.html',context_dict,status=400
                                )
                    if (warningoccurred==False) :
                        """ If no warnings raised """
                        if (request.is_ajax()):
                            ajaxdict["medialink"] = settings.MEDIA_URL + folder + "/"+ convertfile
                            response = dumps(ajaxdict)
                            jpype.detachThreadFromJVM()
                            return HttpResponse(response)
                        context_dict['Content-Disposition'] = 'attachment; filename="{}"'.format(convertfile)
                        context_dict["medialink"] = settings.MEDIA_URL + folder + "/"+ convertfile
                        context_dict["Content-Type"] = content_type
                        jpype.detachThreadFromJVM()
                        return render(request, 
                            'app/convert.html',context_dict,status=200
                            )
                        #return HttpResponseRedirect(settings.MEDIA_URL + folder + "/" + convertfile)
                    else :
                        if (request.is_ajax()):
                            ajaxdict["type"] = "warning"
                            ajaxdict["data"] = "The following warning(s) were raised by "+ myfile.name + ": " + str(retval)
                            ajaxdict["medialink"] = settings.MEDIA_URL + folder + "/"+ convertfile
                            response = dumps(ajaxdict)
                            jpype.detachThreadFromJVM()
                            return HttpResponse(response,status=406)
                        context_dict["error"] = str(retval)
                        context_dict["type"] = "warning"
                        context_dict['Content-Disposition'] = 'attachment; filename="{}"'.format(convertfile)
                        context_dict["Content-Type"] = content_type
                        context_dict["medialink"] = settings.MEDIA_URL + folder + "/"+ convertfile
                        jpype.detachThreadFromJVM()
                        return render(request, 
                            'app/convert.html',context_dict,status=406
                            )
                else :
                    context_dict["error"] = "No file uploaded"
                    context_dict["type"] = "error"
                    jpype.detachThreadFromJVM()
                    return render(request, 
                        'app/convert.html',context_dict,status=404
                        )
            except jpype.JavaException,ex :
                """ Java exception raised without exiting the application"""
                if (request.is_ajax()):
                    ajaxdict["type"] = "error"
                    ajaxdict["data"] = jpype.JavaException.message(ex)
                    response = dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=400)
                context_dict["type"] = "error"
                context_dict["error"] = jpype.JavaException.message(ex)
                jpype.detachThreadFromJVM()
                return render(request, 
                    'app/convert.html',context_dict,status=400
                    )
            except MultiValueDictKeyError:
                """ If no files uploaded"""
                if (request.is_ajax()):
                    ajaxdict["type"] = "error"
                    ajaxdict["data"] = "No files selected." 
                    response = dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=404)
                context_dict["type"] = "error"
                context_dict["error"] = "No files selected." 
                jpype.detachThreadFromJVM()    
                return render(request, 
                    'app/convert.html',context_dict,status=404
                    )
            except :
                """ Other error raised """
                if (request.is_ajax()):
                    ajaxdict["type"] = "error"
                    ajaxdict["data"] = format_exc()
                    response = dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=400)
                context_dict["type"] = "error"
                context_dict["error"] = format_exc()
                jpype.detachThreadFromJVM()    
                return render(request, 
                    'app/convert.html',context_dict,status=400
                    )
        else :
            return render(request, 
                'app/convert.html',context_dict
                )
    else :
        return HttpResponseRedirect(settings.LOGIN_URL)

def check_license(request):
    """ View for check license tool
    returns check_license.html template
    """
    if request.user.is_authenticated() or settings.ANONYMOUS_LOGIN_ENABLED:
        context_dict={}
        if request.method == 'POST':
            licensetext = request.POST.get('licensetext')
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =settings.JAR_ABSOLUTE_PATH
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ Attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.compare")
            compareclass = package.LicenseCompareHelper
            try:
                """Call the java function with parameter"""
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
                        response = dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response)
                    context_dict["success"] = str(matching_str)
                    jpype.detachThreadFromJVM()
                    return render(request, 
                        'app/check_license.html',context_dict,status=200
                        )
                else:
                    if (request.is_ajax()):
                        ajaxdict=dict()
                        ajaxdict["data"] = "There are no matching SPDX listed licenses"
                        response = dumps(ajaxdict)
                        jpype.detachThreadFromJVM()
                        return HttpResponse(response,status=404)
                    context_dict["error"] = "There are no matching SPDX listed licenses"
                    jpype.detachThreadFromJVM()
                    return render(request, 
                        'app/check_license.html',context_dict,status=404
                        )
            except jpype.JavaException,ex :
                """ Java exception raised without exiting the application """
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = jpype.JavaException.message(ex)
                    response = dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=404)
                context_dict["error"] = jpype.JavaException.message(ex)
                jpype.detachThreadFromJVM()
                return render(request, 
                    'app/check_license.html',context_dict,status=404
                    )
            except :
                """ Other exception raised """
                if (request.is_ajax()):
                    ajaxdict=dict()
                    ajaxdict["data"] = format_exc()
                    response = dumps(ajaxdict)
                    jpype.detachThreadFromJVM()
                    return HttpResponse(response,status=404)
                context_dict["error"] = format_exc()
                jpype.detachThreadFromJVM()    
                return render(request, 
                    'app/check_license.html',context_dict,status=404
                    )
        else:
            """GET,HEAD"""
            return render(request, 
                'app/check_license.html',context_dict
                )
    else:
        return HttpResponseRedirect(settings.LOGIN_URL)

def xml_upload(request):
    """ View for uploading XML file
    returns xml_upload.html
    """
    if request.user.is_authenticated() or settings.ANONYMOUS_LOGIN_ENABLED:
        context_dict={}
        ajaxdict = {}
        if request.method == 'POST':
            if "xmlTextButton" in request.POST:
                """ If user provides XML text using textarea """
                try:
                    if len(request.POST["xmltext"])>0 :
                        page_id = request.POST['page_id']
                        request.session[page_id] = request.POST["xmltext"]
                        if(request.is_ajax()):
                            ajaxdict["redirect_url"] = '/app/edit/'+page_id+'/'
                            response = dumps(ajaxdict)
                            return HttpResponse(response, status=200)
                        return render(request, 
                            'app/editor.html',context_dict,status=200
                            )
                    else:
                        if (request.is_ajax()):
                            ajaxdict["type"] = "error"
                            ajaxdict["data"] = "No license XML text provided. Please input some license XML text to edit."
                            response = dumps(ajaxdict)
                            return HttpResponse(response,status=404)
                        context_dict["error"] = "No license XML text provided. Please input some license XML text to edit."
                        return render(request, 
                            'app/xml_upload.html',context_dict,status=404
                            )
                except:
                    if (request.is_ajax()):
                        ajaxdict["type"] = "error"
                        ajaxdict["data"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                        logger.error(str(format_exc()))
                        response = dumps(ajaxdict)
                        return HttpResponse(response,status=500)
                    logger.error(str(format_exc()))    
                    context_dict["error"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                    return render(request, 
                        'app/xml_upload.html',context_dict,status=500
                        )

            elif "licenseNameButton" in request.POST:
                """ If license name is provided by the user """
                try:
                    name = request.POST["licenseName"]
                    if len(name) <= 0:
                        if (request.is_ajax()):
                            ajaxdict["type"] = "error"
                            ajaxdict["data"] = "No license name given. Please provide a SPDX license or exception name to edit."
                            response = dumps(ajaxdict)
                            return HttpResponse(response,status=400)
                        context_dict["error"] = "No license name given. Please provide a SPDX license or exception name to edit."
                        return render(request, 
                            'app/xml_upload.html',context_dict,status=400
                                )                        
                    url = "https://raw.githubusercontent.com/spdx/license-list-XML/master/src/"
                    license_json = "https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json"
                    exceptions_json = "https://raw.githubusercontent.com/spdx/license-list-data/master/json/exceptions.json"
                    """ If it is exception name """
                    if re.search('exception', name, re.IGNORECASE):
                        data = requests.get(exceptions_json).text
                        data = loads(data)
                        """ Extracting exception identifier """
                        found = 0
                        for exception in data["exceptions"]:
                            if(exception["licenseExceptionId"] == name):
                                url+= "exceptions/" + name
                                found = 1
                                break
                            elif(exception["name"] == name):
                                url+= "exceptions/" + exception["licenseExceptionId"]
                                name = exception["licenseExceptionId"]
                                found = 1
                                break
                        if not found:
                            if (request.is_ajax()):
                                ajaxdict["type"] = "error"
                                ajaxdict["data"] = "License or Exception name does not exist. Please provide a valid SPDX license or exception name to edit."
                                response = dumps(ajaxdict)
                                return HttpResponse(response,status=404)
                            context_dict["error"] = "License or Exception name does not exist. Please provide a valid SPDX license or exception name to edit."
                            return render(request, 
                                'app/xml_upload.html',context_dict,status=404
                                )
                    else:
                        """ If it is license name """
                        data = requests.get(license_json).text
                        data = loads(data)
                        """ Extracting license identifier """
                        found = 0
                        for license in data["licenses"]:
                            if(license["licenseId"] == name):
                                url+= name
                                found = 1
                                break
                            elif(license["name"] == name):
                                url+= license["licenseId"]
                                name = license["licenseId"]
                                found = 1
                                break
                        else:
                            if (request.is_ajax()):
                                ajaxdict["type"] = "error"
                                ajaxdict["data"] = "License or Exception name does not exist. Please provide a valid SPDX license or exception name to edit."
                                response = dumps(ajaxdict)
                                return HttpResponse(response,status=404)
                            context_dict["error"] = "License or Exception name does not exist. Please provide a valid SPDX license or exception name to edit."
                            return render(request, 
                                'app/xml_upload.html',context_dict,status=404
                                )
                    url += ".xml"
                    response = requests.get(url)
                    if(response.status_code == 200):
                        page_id = request.POST['page_id']
                        request.session[page_id] = [response.text, name]
                        if (request.is_ajax()):
                            ajaxdict["redirect_url"] = '/app/edit/'+page_id+'/'
                            response = dumps(ajaxdict)
                            return HttpResponse(response, status=200)
                        return render(request, 
                                'app/editor.html',context_dict,status=200
                                )
                    else:
                        if (request.is_ajax()):
                            ajaxdict["type"] = "error"
                            ajaxdict["data"] = "The application could not be connected. Please try again."
                            response = dumps(ajaxdict)
                            return HttpResponse(response,status=500)
                        context_dict["error"] = "The application could not be connected. Please try again."
                        return render(request, 
                            'app/xml_upload.html',context_dict,status=500
                            )
                except:
                    if (request.is_ajax()):
                        ajaxdict["data"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                        logger.error(str(format_exc()))
                        response = dumps(ajaxdict)
                        return HttpResponse(response,status=500)
                    logger.error(str(format_exc()))
                    context_dict["error"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                    return render(request, 
                        'app/xml_upload.html',context_dict,status=500
                        )

            elif "uploadButton" in request.POST:
                """ If user uploads the XML file """
                try:
                    if "file" in request.FILES and len(request.FILES["file"])>0:
                        """ Saving XML file to the media directory """
                        xml_file = request.FILES['file']
                        if not xml_file.name.endswith(".xml"):
                            if (request.is_ajax()):
                                ajaxdict["type"] = "error"
                                ajaxdict["data"] = "Please select a SPDX license XML file."
                                response = dumps(ajaxdict)
                                return HttpResponse(response,status=400)
                            context_dict["error"] = "Please select a SPDX license XML file."
                            return render(request, 
                                'app/xml_upload.html',context_dict,status=400
                                )
                        folder = str(request.user) + "/" + str(int(time())) 
                        fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,
                            base_url=urljoin(settings.MEDIA_URL, folder+'/')
                            )
                        filename = fs.save(xml_file.name, xml_file)
                        uploaded_file_url = fs.url(filename)
                        page_id = request.POST['page_id']
                        with open(str(settings.APP_DIR+uploaded_file_url), 'r') as f:
                            request.session[page_id] = f.read()
                        if (request.is_ajax()):
                            ajaxdict["redirect_url"] = '/app/edit/'+page_id+'/'
                            response = dumps(ajaxdict)
                            return HttpResponse(response, status=200)
                        return render(request, 
                            'app/xml_upload.html',context_dict,status=200
                            )
                    else :
                        """ If no file is uploaded """
                        if (request.is_ajax()):
                            ajaxdict["type"] = "error"
                            ajaxdict["data"] = "No file uploaded. Please upload a SPDX license XML file to edit."
                            response = dumps(ajaxdict)
                            return HttpResponse(response,status=400)
                        context_dict["error"] = "No file uploaded. Please upload a SPDX license XML file to edit."
                        return render(request, 
                            'app/xml_upload.html',context_dict,status=400
                            )
                except:
                    if (request.is_ajax()):
                        ajaxdict["type"] = "error"
                        ajaxdict["data"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                        logger.error(str(format_exc()))
                        response = dumps(ajaxdict)
                        return HttpResponse(response, status=500)
                    logger.error(str(format_exc()))
                    context_dict["error"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                    return render(request, 
                        'app/xml_upload.html',context_dict,status=500
                        )

            elif "newButton" in request.POST:
                """ If the user starts with new XML """
                try:
                    xml_text = """<?xml version="1.0" encoding="UTF-8"?>\n<SPDXLicenseCollection xmlns="http://www.spdx.org/license">\n<license></license>\n</SPDXLicenseCollection>"""
                    page_id = request.POST['page_id']
                    request.session[page_id] = xml_text
                    ajaxdict["redirect_url"] = '/app/edit/'+page_id+'/'
                    response = dumps(ajaxdict)
                    return HttpResponse(response, status=200)
                except:
                    if (request.is_ajax()):
                        ajaxdict["type"] = "error"
                        ajaxdict["data"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                        logger.error(str(format_exc()))
                        response = dumps(ajaxdict)
                        return HttpResponse(response, status=500)
                    logger.error(str(format_exc()))
                    context_dict["error"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                    return render(request, 
                        'app/xml_upload.html',context_dict,status=500
                        )
            else:
                ajaxdict["type"] = "error"
                ajaxdict["data"] = "Bad Request." 
                response = dumps(ajaxdict)
                return HttpResponse(response, status=400)
        else :
            """ GET,HEAD Request """
            return render(request, 'app/xml_upload.html', {})
    else:
        return HttpResponseRedirect(settings.LOGIN_URL)

def xml_edit(request, page_id):
    """View for editing the XML file
    returns editor.html
    """
    context_dict = {}
    if (page_id in request.session):
        if type(request.session[page_id]) == list:
            """ XML input using license name"""
            context_dict["xml_text"] = request.session[page_id][0]    
            context_dict["license_name"] = request.session[page_id][1]
        else:
            """ Other XML input methods """
            context_dict["xml_text"] = request.session[page_id]
        return render(request, 
            'app/editor.html',context_dict,status=200
            )
    else:
        return HttpResponseRedirect('/app/xml_upload')
    
def loginuser(request):
    """ View for Login
    returns login.html template
    """
    if not request.user.is_authenticated():
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
                        response = dumps(ajaxdict)
                        return HttpResponse(response)
                    return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
                else:
                    if (request.is_ajax()):
                        return HttpResponse("Your account is disabled.",status=401)
                    context_dict["invalid"] = "Your account is disabled."
                    return render(request,
                        "app/login.html",context_dict,status=401
                        )	
            else:
                if (request.is_ajax()):
                    return HttpResponse("Invalid login details supplied.",status=403)
                context_dict['invalid']="Invalid login details supplied."
                return render(request, 
                    'app/login.html',context_dict,status=403
                    )
        else:
            return render(request, 
                'app/login.html',context_dict
                )
    else :
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

def register(request):
    """ View for register
    returns register.html template
    """
    if not request.user.is_authenticated():
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
                context_dict["error1"] = user_form.errors
                context_dict["error2"] = user_form.errors
        else:
            user_form = UserRegisterForm()
            profile_form = UserProfileForm()
            context_dict["user_form"]=user_form
            context_dict["profile_form"]=profile_form
        return render(request,
            'app/register.html',context_dict
            )
    else :
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

@login_required
def logoutuser(request):
    """Flush session and logout user """
    request.session.flush()
    logout(request)
    return HttpResponseRedirect(settings.LOGIN_URL)

def profile(request):
    """ View for profile
    returns profile.html template
    """
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
                    return render(request,
                        'app/profile.html',context_dict
                        )
                else :
                    context_dict["error"] = "Error changing details " + str(info_form.errors) + str(orginfo_form.errors)
                    return render(request,
                        'app/profile.html',context_dict,status=400
                        )
            if "changepwd" in request.POST:
                form = PasswordChangeForm(request.user, request.POST)
                if form.is_valid():
                    user = form.save()
                    update_session_auth_hash(request, user)  # Important!
                    context_dict["success"] = 'Your password was successfully updated!'
                    return render(request,
                        'app/profile.html',context_dict
                        )
                else:
                    context_dict["error"] = form.errors
                    return render(request,
                        'app/profile.html',context_dict,status=400
                        )
            else :
                context_dict["error"] = "Invalid request."
                return render(request,
                    'app/profile.html',context_dict,status=404
                    )
        else:
            return render(request,
                'app/profile.html',context_dict
                )
    else:
        return HttpResponseRedirect(settings.LOGIN_URL)


def checkusername(request):
    """Returns whether username already taken or not"""
    if 'username' in request.POST:
        users = User.objects.filter(username=request.POST["username"])
        if (len(users)>0):
            return HttpResponse(dumps({"data": "Already Exist."}),status=404)
        else :
            return HttpResponse(dumps({"data": "Success"}),status=200) 
    else :
        return HttpResponse(dumps({"data": "No username entered"}),status=400)


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
        context_instance = RequestContext(request),
        status=404
    )
    
def handler500(request):
    return render_to_response('app/500.html',
        context_instance = RequestContext(request)
    )
