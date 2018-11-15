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
from django.http import JsonResponse

import jpype
import requests
from lxml import etree
import re
import os
import logging
import json
from traceback import format_exc
from json import dumps, loads
from time import time
from urlparse import urljoin
import xml.etree.cElementTree as ET
import datetime
from wsgiref.util import FileWrapper
import os
from requests import post

from social_django.models import UserSocialAuth
from app.models import UserID, LicenseNames
from app.forms import UserRegisterForm,UserProfileForm,InfoForm,OrgInfoForm
import app.utils as utils


logging.basicConfig(filename="error.log", format="%(levelname)s : %(asctime)s : %(message)s")
logger = logging.getLogger()
from .forms import LicenseRequestForm
from .models import LicenseRequest

from app.github_utils import getGithubToken
import cgi

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

def submitNewLicense(request):
    """ View for submit new licenses
    returns submit_new_license.html template
    """
    context_dict = {}
    ajaxdict = {}
    if request.method=="POST":
        if not request.user.is_authenticated():
            return HttpResponseRedirect(settings.LOGIN_URL)        
        try:
            user = request.user
            try:
                """ Getting user info for submitting github issue """
                github_login = user.social_auth.get(provider='github')
                token = github_login.extra_data["access_token"]
                username = github_login.extra_data["login"]
                form = LicenseRequestForm(request.POST, auto_id='%s')
                if form.is_valid() and request.is_ajax():
                    licenseName = form.cleaned_data['fullname']
                    licenseIdentifier = form.cleaned_data['shortIdentifier']
                    licenseOsi = form.cleaned_data['osiApproved']
                    licenseSourceUrls = [form.cleaned_data['sourceUrl']]
                    licenseHeader = form.cleaned_data['licenseHeader']
                    licenseNotes = form.cleaned_data['notes']
                    licenseText = form.cleaned_data['text']
                    userEmail = form.cleaned_data['userEmail']
                    xml = generateLicenseXml(licenseOsi, licenseIdentifier, licenseName,
                        licenseSourceUrls, licenseHeader, licenseNotes, licenseText)
                    now = datetime.datetime.now()
                    licenseRequest = LicenseRequest(fullname=licenseName,shortIdentifier=licenseIdentifier,
                        submissionDatetime=now, userEmail=userEmail, xml=xml)
                    licenseRequest.save()
                    statusCode = createIssue(licenseName, licenseIdentifier, licenseSourceUrls, licenseOsi, token)
                    data = {'statusCode' : str(statusCode)}
                    return JsonResponse(data)
            except UserSocialAuth.DoesNotExist:
                """ User not authenticated with GitHub """
                if (request.is_ajax()):
                    ajaxdict["type"] = "auth_error"
                    ajaxdict["data"] = "Please login using GitHub to use this feature."
                    response = dumps(ajaxdict)
                    return HttpResponse(response,status=401)
                return HttpResponse("Please login using GitHub to use this feature.",status=401)
        except:
            """ Other errors raised """
            logger.error(str(format_exc()))
            if (request.is_ajax()):
                ajaxdict["type"] = "error"
                ajaxdict["data"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                response = dumps(ajaxdict)
                return HttpResponse(response,status=500)
            return HttpResponse("Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc(), status=500)
    else:
        form = LicenseRequestForm(auto_id='%s')
        context_dict['form'] = form
    return render(request, 
        'app/submit_new_license.html', context_dict
        )


def generateLicenseXml(licenseOsi, licenseIdentifier, licenseName, licenseSourceUrls, licenseHeader, licenseNotes, licenseText):
    """ View for generating a spdx license xml
    returns the license xml as a string
    """
    root = ET.Element("SPDXLicenseCollection", xmlns="http://www.spdx.org/license")
    license = ET.SubElement(root, "license", isOsiApproved=licenseOsi, licenseId=licenseIdentifier, name=licenseName)
    crossRefs = ET.SubElement(license, "crossRefs")
    for sourceUrl in licenseSourceUrls:
        ET.SubElement(crossRefs, "crossRef").text = sourceUrl
    ET.SubElement(license, "standardLicenseHeader").text = licenseHeader
    ET.SubElement(license, "notes").text = licenseNotes
    licenseTextElement = ET.SubElement(license, "text")
    licenseLines = licenseText.replace('\r','').split('\n')
    for licenseLine in licenseLines:
        ET.SubElement(licenseTextElement, "p").text = licenseLine
    xmlString = ET.tostring(root, encoding='utf8', method='xml').replace('>','>\n')
    return xmlString

def createIssue(licenseName, licenseIdentifier, licenseSourceUrls, licenseOsi, token):
    """ View for creating an GitbHub issue
    when submitting a new license request
    """
    body = '**1.** License Name: ' + licenseName + '\n**2.** Short identifier: ' + licenseIdentifier + '\n**3.** URL: '
    for url in licenseSourceUrls:
        body += url
        body += '\n'
    body += '**4.** OSI Approval: ' + licenseOsi
    title = 'New license request: ' + licenseIdentifier + ' [SPDX-Online-Tools]'
    payload = {'title' : title, 'body': body, 'labels': ['new license/exception request']}
    headers = {'Authorization': 'token ' + myToken}
    url = 'https://api.github.com/repos/spdx/license-list-XML/issues'
    r = post(url, data=dumps(payload), headers=headers)
    return r.status_code


def licenseRequests(request):
    """ View for license requests
    returns license_requests.html template
    """
    licenserequests = LicenseRequest.objects.all()
    context_dict={'licenseRequests': licenserequests}
    return render(request, 
        'app/license_requests.html',context_dict
        )

def licenseInformation(request, licenseId):
    """ View for license request information
    returns license_information.html template
    """
    licenseRequest = LicenseRequest.objects.get(id=licenseId)
    context_dict = {}
    licenseInformation = {}
    licenseInformation['fullname'] = licenseRequest.fullname
    licenseInformation['shortIdentifier'] = licenseRequest.shortIdentifier
    licenseInformation['submissionDatetime'] = licenseRequest.submissionDatetime
    licenseInformation['userEmail'] = licenseRequest.userEmail
    xmlString = licenseRequest.xml
    data = parseXmlString(xmlString)
    licenseInformation['osiApproved'] = data['osiApproved']
    licenseInformation['crossRefs'] = data['crossRefs']
    licenseInformation['notes'] = data['notes']
    licenseInformation['standardLicenseHeader'] = data['standardLicenseHeader']
    licenseInformation['text'] = data['text']
    context_dict ={'licenseInformation': licenseInformation}
    if request.method == 'POST':
        tempFilename = 'output.xml'
        xmlFile = open(tempFilename, 'w')
        xmlFile.write(xmlString)
        xmlFile.close()
        xmlFile = open(tempFilename, 'r')
        myfile = FileWrapper(xmlFile)
        response = HttpResponse(myfile, content_type='application/xml')
        response['Content-Disposition'] = 'attachment; filename=' + licenseRequest.shortIdentifier + '.xml'
        xmlFile.close()
        os.remove(tempFilename)
        return response

    return render(request, 
        'app/license_information.html',context_dict
        )

def parseXmlString(xmlString):
    """ View for generating a spdx license xml
    returns a dictionary with the xmlString license fields values
    """
    data = {}
    tree = ET.ElementTree(ET.fromstring(xmlString))
    try:
        root = tree.getroot()
    except Exception as e:
        return
    try:
        if(len(root) > 0 and 'isOsiApproved' in root[0].attrib):
            data['osiApproved'] = root[0].attrib['isOsiApproved']
        else:
            data['osiApproved'] = '-'
    except Exception as e:
        data['osiApproved'] = '-'
    data['crossRefs'] = []
    try:
        if(len(('{http://www.spdx.org/license}license/{http://www.spdx.org/license}crossRefs')) > 0):
            crossRefs = tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}crossRefs')[0]
            for crossRef in crossRefs:
                data['crossRefs'].append(crossRef.text)
    except Exception as e:
        data['crossRefs'] = []
    try:
        if(len(tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}notes')) > 0):
            data['notes'] = tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}notes')[0].text
        else:
            data['notes'] = ''
    except Exception as e:
        data['notes'] = ''
    try:
        if(len(tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}standardLicenseHeader')) > 0):
            data['standardLicenseHeader'] = tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}standardLicenseHeader')[0].text
        else:
            data['standardLicenseHeader'] = ''
    except Exception as e:
        data['standardLicenseHeader'] = ''
    try:
        if(len(tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}text')) > 0):
            textElem = tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}text')[0]
            ET.register_namespace('', "http://www.spdx.org/license")
            textStr = ET.tostring(textElem).strip()
            if(len(textStr) >= 49 and textStr[:42] == '<text xmlns="http://www.spdx.org/license">' and textStr[-7:] == '</text>'):
                textStr = textStr[42:]
                textStr = textStr[:-7].strip().replace('&lt;', '<').replace('&gt;', '>').strip()
            data['text'] = textStr.strip()
        else:
            data['text'] = ''
    except Exception as e:
        data['text'] = ''
    return data

def get_xml():
    my_xml = ET.Element('foo', attrib={'bar': 'bla'})
    my_str = ET.tostring(my_xml, 'utf-8', short_empty_elements=False)
    enc = '<?xml version="1.0" encoding="utf-8"?>'
    enc = enc + my_str.decode('utf-8')
    return enc

def download_xml_file(request, licenseId):
    #licenseRequest = LicenseRequest.objects.get(id=licenseId)
    response = HttpResponse(get_xml(), content_type="application/xml")
    response['Content-Disposition'] = 'inline; filename=myfile.xml'
    return response

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

def validate_xml(request):
    """ View to validate xml text against SPDX License XML Schema,
         used in the xml editor """
    if request.user.is_authenticated() or settings.ANONYMOUS_LOGIN_ENABLED:
        context_dict={}
        if request.method == 'POST':
            ajaxdict=dict()
            try :
                if "xmlText" in request.POST:
                    """ Saving file to the media directory """
                    xmlText = request.POST['xmlText']
                    xmlText = xmlText.encode('utf-8')
                    folder = str(request.user) + "/" + str(int(time()))
                    if not os.path.isdir(str(settings.MEDIA_ROOT +"/"+ folder)):
                        os.makedirs(str(settings.MEDIA_ROOT +"/"+ folder))
                    uploaded_file_url = settings.MEDIA_ROOT + '/' + folder + '/' + 'xmlFile.xml'
                    with open(uploaded_file_url,'w') as f:
                        f.write(xmlText)
                    """ Get schema text from GitHub,
                    if it fails use the file in examples folder """
                    try:
                        schema_url = 'https://raw.githubusercontent.com/spdx/license-list-XML/master/schema/ListedLicense.xsd'
                        schema_text = requests.get(schema_url, timeout=5).text
                        xmlschema_doc = etree.fromstring(schema_text)
                    except:
                        schema_url = settings.BASE_DIR + "/examples/xml-schema.xsd"
                        with open(schema_url) as f:
                            xmlschema_doc = etree.parse(f)
                    """ Using the lxml etree functions """
                    xmlschema = etree.XMLSchema(xmlschema_doc)
                    with open(uploaded_file_url) as f:
                        xml_input = etree.parse(f)

                    try:
                        xmlschema.assertValid(xml_input)
                        """ If the xml is valid """
                        if (request.is_ajax()):
                            ajaxdict["type"] = "valid"
                            ajaxdict["data"] = "This XML is valid against SPDX License Schema."
                            response = dumps(ajaxdict)
                            return HttpResponse(response,status=200)
                        return HttpResponse("This XML is valid against SPDX License Schema.",status=200)
                    except Exception as e:
                        if (request.is_ajax()):
                            ajaxdict["type"] = "invalid"
                            ajaxdict["data"] = "This XML is not valid against SPDX License Schema.\n"+str(e)
                            response = dumps(ajaxdict)
                            return HttpResponse(response,status=200)
                        return HttpResponse("This XML is not valid against SPDX License Schema.\n"+str(e),status=200)
                else :
                    """ If no xml text is given."""
                    if (request.is_ajax()):
                        ajaxdict["type"] = "error"
                        ajaxdict["data"] = "No XML text given."
                        response = dumps(ajaxdict)
                        return HttpResponse(response,status=400)
                    return HttpResponse("No XML text given.", status=400)
            except etree.XMLSyntaxError as e:
                """ XML not valid """
                if (request.is_ajax()):
                    ajaxdict["type"] = "error"
                    ajaxdict["data"] = "XML Parsing Error.\n The XML is not valid. Please correct the XML text and try again." 
                    response = dumps(ajaxdict)
                    return HttpResponse(response,status=400)
                return HttpResponse("XML Parsing Error.\n The XML is not valid. Please correct the XML text and try again.", status=400)
            except :
                """ Other error raised """
                logger.error(str(format_exc()))
                if (request.is_ajax()):
                    ajaxdict["type"] = "error"
                    ajaxdict["data"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                    response = dumps(ajaxdict)
                    return HttpResponse(response,status=500)
                return HttpResponse("Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc(), status=500)
        else :
            """ GET,HEAD """
            return HttpResponseRedirect(settings.HOME_URL)
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
            try:
                if "xmlTextButton" in request.POST:
                    """ If user provides XML text using textarea """
                    if len(request.POST["xmltext"])>0 :
                        page_id = request.POST['page_id']
                        request.session[page_id] = [request.POST["xmltext"], ""]
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

                elif "licenseNameButton" in request.POST:
                    """ If license name is provided by the user """
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

                    url = utils.check_license_name(name)
                    if url[0] is False:
                        if (request.is_ajax()):
                            ajaxdict["type"] = "error"
                            ajaxdict["data"] = "License or Exception name does not exist. Please provide a valid SPDX license or exception name to edit."
                            response = dumps(ajaxdict)
                            return HttpResponse(response,status=404)
                        context_dict["error"] = "License or Exception name does not exist. Please provide a valid SPDX license or exception name to edit."
                        return render(request, 
                            'app/xml_upload.html',context_dict,status=404
                            )
                    url[0] += ".xml"
                    response = requests.get(url[0])
                    if(response.status_code == 200):
                        page_id = request.POST['page_id']
                        request.session[page_id] = [response.text, url[1]]
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

                elif "uploadButton" in request.POST:
                    """ If user uploads the XML file """
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
                        with open(str(fs.location+'/'+filename), 'r') as f:
                            request.session[page_id] = [f.read(), ""]
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

                elif "newButton" in request.POST:
                    """ If the user starts with new XML """
                    xml_text = """<?xml version="1.0" encoding="UTF-8"?>\n<SPDXLicenseCollection xmlns="http://www.spdx.org/license">\n<license></license>\n</SPDXLicenseCollection>"""
                    page_id = request.POST['page_id']
                    request.session[page_id] = [xml_text, ""]
                    ajaxdict["redirect_url"] = '/app/edit/'+page_id+'/'
                    response = dumps(ajaxdict)
                    return HttpResponse(response, status=200)

                else:
                    ajaxdict["type"] = "error"
                    ajaxdict["data"] = "Bad Request." 
                    response = dumps(ajaxdict)
                    return HttpResponse(response, status=400)
            except:
                logger.error(str(format_exc()))
                if (request.is_ajax()):
                    ajaxdict["type"] = "error"
                    ajaxdict["data"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                    response = dumps(ajaxdict)
                    return HttpResponse(response, status=500)
                context_dict["error"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                return render(request, 
                    'app/xml_upload.html',context_dict,status=500
                    )
        else :
            """ GET,HEAD Request """
            return render(request, 'app/xml_upload.html', {})
    else:
        return HttpResponseRedirect(settings.LOGIN_URL)

def autocompleteModel(request):
    if 'term' in request.GET:
        result = LicenseNames.objects.filter(name__icontains=request.GET['term']).values_list('name',flat=True)
        return HttpResponse( json.dumps( [ name for name in result ] ) )
    return HttpResponse()

def xml_edit(request, page_id):
    """View for editing the XML file
    returns editor.html """
    context_dict = {}
    if (page_id in request.session):
        if request.user.is_authenticated():
            user = request.user
            try:
                github_login = user.social_auth.get(provider='github')
            except UserSocialAuth.DoesNotExist:
                github_login = None
            context_dict["github_login"] = github_login
        context_dict["xml_text"] = request.session[page_id][0]
        context_dict["license_name"] = request.session[page_id][1]
        return render(request, 
            'app/editor.html',context_dict,status=200
            )
    else:
        return HttpResponseRedirect('/app/xml_upload')

def update_session_variables(request):
    """ View for updating the XML text in the session variable """
    if request.method == "POST" and request.is_ajax():
        page_id = request.POST["page_id"]
        request.session[page_id] = [request.POST["xml_text"], request.POST["license_name"]]
        ajaxdict={}
        ajaxdict["type"] = "success"
        response = dumps(ajaxdict)
        return HttpResponse(response, status=200)
    else:
        ajaxdict={}
        ajaxdict["type"] = "error"
        response = dumps(ajaxdict)
        return HttpResponse(response, status=400)
    return HttpResponse("Bad Request", status=400)

def pull_request(request):
    """ View that handles pull request """
    if request.user.is_authenticated():
        if request.method=="POST":
            context_dict = {}
            ajaxdict = {}
            try:
                if request.user.is_authenticated():
                    user = request.user
                try:
                    """ Getting user info and calling the makePullRequest function """
                    github_login = user.social_auth.get(provider='github')
                    token = github_login.extra_data["access_token"]
                    username = github_login.extra_data["login"]
                    response = utils.makePullRequest(username, token, request.POST["branchName"], request.POST["updateUpstream"], request.POST["fileName"], request.POST["commitMessage"], request.POST["prTitle"], request.POST["prBody"], request.POST["xmlText"])
                    if(response["type"]=="success"):
                        """ PR made successfully """
                        if (request.is_ajax()):
                            ajaxdict["type"] = "success"
                            ajaxdict["data"] = response["pr_url"]
                            response = dumps(ajaxdict)
                            return HttpResponse(response,status=200)
                        return HttpResponse(response["pr_url"],status=200)
                    else:
                        """ Error while making PR """
                        if (request.is_ajax()):
                            ajaxdict["type"] = "pr_error"
                            ajaxdict["data"] = response["message"]
                            response = dumps(ajaxdict)
                            return HttpResponse(response,status=500)
                        return HttpResponse(response["message"],status=500)
                except UserSocialAuth.DoesNotExist:
                    """ User not authenticated with GitHub """
                    if (request.is_ajax()):
                        ajaxdict["type"] = "auth_error"
                        ajaxdict["data"] = "Please login using GitHub to use this feature."
                        response = dumps(ajaxdict)
                        return HttpResponse(response,status=401)
                    return HttpResponse("Please login using GitHub to use this feature.",status=401)
            except:
                """ Other errors raised """
                logger.error(str(format_exc()))
                if (request.is_ajax()):
                    ajaxdict["type"] = "error"
                    ajaxdict["data"] = "Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc()
                    response = dumps(ajaxdict)
                    return HttpResponse(response,status=500)
                return HttpResponse("Unexpected error, please email the SPDX technical workgroup that the following error has occurred: " + format_exc(), status=500)
        else:
            return HttpResponseRedirect(settings.HOME_URL)
    else:
        return HttpResponseRedirect(settings.LOGIN_URL)

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
