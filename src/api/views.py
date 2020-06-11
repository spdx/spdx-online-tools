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

from rest_framework.parsers import FileUploadParser,FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from api.models import ValidateFileUpload,ConvertFileUpload,CompareFileUpload,CheckLicenseFileUpload,SubmitLicenseModel
from api.serializers import ValidateSerializer,ConvertSerializer,CompareSerializer,CheckLicenseSerializer,SubmitLicenseSerializer,ValidateSerializerReturn,ConvertSerializerReturn,CompareSerializerReturn,CheckLicenseSerializerReturn,SubmitLicenseSerializerReturn
from api.oauth import generate_github_access_token,convert_to_auth_token,get_user_from_token
from app.models import LicenseRequest
from rest_framework import status
from rest_framework.decorators import api_view,renderer_classes,permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.renderers import BrowsableAPIRenderer,JSONRenderer

from django.core.files.storage import FileSystemStorage
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User

import jpype
import re
import datetime
import xml.etree.cElementTree as ET

from traceback import format_exc
from os.path import abspath, join
from time import time
from requests import post
from json import dumps, loads

NORMAL = "normal"
TESTS = "tests"

TYPE_TO_URL = {
NORMAL:  settings.REPO_URL,
TESTS: settings.DEV_REPO_URL,
}


class ValidateViewSet(ModelViewSet):
    """ Returns all validate api request """
    queryset = ValidateFileUpload.objects.all()
    serializer_class = ValidateSerializerReturn
    parser_classes = (MultiPartParser, FormParser,)

class ConvertViewSet(ModelViewSet):
    """ Returns all convert api request """
    queryset = ConvertFileUpload.objects.all()
    serializer_class = ConvertSerializerReturn
    parser_classes = (MultiPartParser, FormParser,)

class CompareViewSet(ModelViewSet):
    """ Returns all compare api request """
    queryset = CompareFileUpload.objects.all()
    serializer_class = CompareSerializerReturn
    parser_classes = (MultiPartParser, FormParser,)

@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def validate(request):
    """ Handle Validate api request """
    if request.method == 'GET':
        """ Return all validate api request """
        query = ValidateFileUpload.objects.all()
        serializer = ValidateSerializer(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        """ Return validate tool result on the post file"""
        serializer = ValidateSerializer(data=request.data)
        if serializer.is_valid():
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =settings.JAR_ABSOLUTE_PATH
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """Attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            verifyclass = package.Verify
            query = ValidateFileUpload.objects.create(
                owner=request.user,
                file=request.data.get('file')
            )
            uploaded_file = str(query.file)
            uploaded_file_path = str(query.file.path)
            try :
                if request.FILES["file"]:
                    """ Call the java function with parameter"""
                    retval = verifyclass.verify(uploaded_file_path)
                    if (len(retval) > 0):
                        result = "The following error(s)/warning(s) were raised: " + str(retval)
                        returnstatus = status.HTTP_400_BAD_REQUEST
                        httpstatus = 400
                        jpype.detachThreadFromJVM()
                    else :
                        result = "This SPDX Document is valid."
                        returnstatus = status.HTTP_201_CREATED
                        httpstatus = 201
                        jpype.detachThreadFromJVM()
                else :
                    result = "File Not Uploaded"
                    returnstatus = status.HTTP_400_BAD_REQUEST
                    httpstatus = 400
                    jpype.detachThreadFromJVM()
            except jpype.JavaException as ex :
                """ Error raised by verifyclass.verify without exiting the application"""
                result = jpype.JavaException.message(ex) #+ "This SPDX Document is not a valid RDF/XML or tag/value format"
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM()
            except :
                """ Other errors raised"""
                result = format_exc()
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM()
            query.result=result
            query.status=httpstatus
            ValidateFileUpload.objects.filter(file=uploaded_file).update(result=result,status=httpstatus)
            serial = ValidateSerializerReturn(instance=query)
            return Response(
                serial.data, status=returnstatus
                )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

def extensionGiven(filename):
    if (filename.find(".")!=-1):
        return True
    else:
        return False

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

@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def convert(request):
    """ Handle Convert api request """
    if request.method == 'GET':
        """ Return all convert api request """
        query = ConvertFileUpload.objects.all()
        serializer = ConvertSerializer(query, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        """ Return convert tool result on the post file"""
        serializer = ConvertSerializer(data=request.data)
        if serializer.is_valid():
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =settings.JAR_ABSOLUTE_PATH
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ Attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            result = ""
            tagToRdfFormat = None
            message = "Success"
            query = ConvertFileUpload.objects.create(
                owner=request.user,
                file=request.data.get('file'),
                from_format=request.POST["from_format"],
                to_format=request.POST["to_format"],
                cfilename=request.POST["cfilename"],
            )
            uploaded_file = str(query.file)
            uploaded_file_path = str(query.file.path)
            try :
                if request.FILES["file"]:
                    folder = "/".join(uploaded_file_path.split('/')[:-1])
                    option1 = request.POST["from_format"]
                    option2 = request.POST["to_format"]
                    convertfile =  request.POST["cfilename"]
                    warningoccurred = False
                    if (extensionGiven(convertfile)==False):
                        extension = getFileFormat(option2)
                        convertfile = convertfile + extension
                    """ Call the java function with parameters as list"""
                    if (option1=="Tag"):
                        print ("Verifing for Tag/Value Document")
                        if (option2=="RDF"):
                            try:
                                tagToRdfFormat = request.POST["tagToRdfFormat"]
                            except:
                                tagToRdfFormat = 'RDF/XML-ABBREV'
                            option3 = tagToRdfFormat
                            if option3 not in ['RDF/XML-ABBREV','RDF/XML','N-TRIPLET','TURTLE']:
                                message, returnstatus, httpstatus = convertError('400')
                            tagtordfclass = package.TagToRDF
                            retval = tagtordfclass.onlineFunction([
                                uploaded_file_path,
                                folder+"/"+convertfile,
                                option3
                            ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        elif (option2=="Spreadsheet"):
                            tagtosprdclass = package.TagToSpreadsheet
                            retval = tagtosprdclass.onlineFunction([
                                uploaded_file_path,
                                folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        else :
                            message, returnstatus, httpstatus = convertError('400')
                    elif (option1=="RDF"):
                        print ("Verifing for RDF Document")
                        if (option2=="Tag"):
                            rdftotagclass = package.RdfToTag
                            retval = rdftotagclass.onlineFunction([
                                uploaded_file_path,
                                folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        elif (option2=="Spreadsheet"):
                            rdftosprdclass = package.RdfToSpreadsheet
                            retval = rdftosprdclass.onlineFunction([
                                uploaded_file_path,
                                folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        elif (option2=="HTML"):
                            rdftohtmlclass = package.RdfToHtml
                            retval = rdftohtmlclass.onlineFunction([
                                uploaded_file_path,
                                folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        else :
                            message, returnstatus, httpstatus = convertError('400')
                    elif (option1=="Spreadsheet"):
                        print ("Verifing for Spreadsheet Document")
                        if (option2=="Tag"):
                            sprdtotagclass = package.SpreadsheetToTag
                            retval = sprdtotagclass.onlineFunction([
                                uploaded_file_path,
                                folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        elif (option2=="RDF"):
                            sprdtordfclass = package.SpreadsheetToRDF
                            retval = sprdtordfclass.onlineFunction([
                                uploaded_file_path,
                                folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        else :
                            message, returnstatus, httpstatus = convertError('400')
                    if (warningoccurred == True ):
                        message = "The following error(s)/warning(s) were raised: " + str(retval)
                        index = folder.split("/").index('media')
                        result = "/"+"/".join(folder.split("/")[index:])+'/'+convertfile
                        returnstatus = status.HTTP_406_NOT_ACCEPTABLE
                        httpstatus = 406
                        jpype.detachThreadFromJVM()
                    else :
                        """return only the path starting with MEDIA_URL"""
                        index = folder.split("/").index('media')
                        result = "/"+("/".join(folder.split("/")[index:]))+'/'+convertfile
                        returnstatus = status.HTTP_201_CREATED
                        httpstatus = 201
                        jpype.detachThreadFromJVM()
                else :
                    message, returnstatus, httpstatus = convertError('404')
            except jpype.JavaException as ex :
                message = jpype.JavaException.message(ex)
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM() 
            except :
                message = format_exc()
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM() 
            query.tagToRdfFormat=tagToRdfFormat
            query.message=message
            query.status = httpstatus
            query.result = result
            ConvertFileUpload.objects.filter(file=uploaded_file).update(tagToRdfFormat=tagToRdfFormat,message=message, status=httpstatus, result=result)
            serial = ConvertSerializerReturn(instance=query)
            return Response(
                serial.data,status=returnstatus
                )
        else:
            return Response(
                serializer.errors,status=status.HTTP_400_BAD_REQUEST
                )


def convertError(status):
    print("Error while converting file")
    if status=='400':
        message = "Select valid conversion types."
        returnstatus = status.HTTP_400_BAD_REQUEST
        httpstatus = 400
    elif status=='404':
        message = "File Not Found"
        returnstatus = status.HTTP_400_BAD_REQUEST
        httpstatus = 400
    jpype.detachThreadFromJVM()
    return (message, returnstatus, httpstatus)


@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def compare(request):
    """ Handle Compare api request """
    if request.method == 'GET':
        """ Return all compare api request """
        query = CompareFileUpload.objects.all()
        serializer = CompareSerializerReturn(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        """ Return compare tool result on the post file"""
        serializer = CompareSerializer(data=request.data)
        if serializer.is_valid():
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =settings.JAR_ABSOLUTE_PATH
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ Attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            verifyclass = package.Verify
            compareclass = package.CompareMultpleSpdxDocs
            result=""
            message="Success"
            erroroccurred = False
            rfilename = request.POST["rfilename"]
            query = CompareFileUpload.objects.create(
                owner=request.user,
                file1=request.data.get('file1'),
                file2=request.data.get('file2'),
                rfilename = rfilename,
            )
            uploaded_file1 = str(query.file1)
            uploaded_file2 = str(query.file2)
            uploaded_file1_path = str(query.file1.path)
            uploaded_file2_path = str(query.file2.path)
            try :
                if (request.FILES["file1"] and request.FILES["file2"]):
                    """ Saving file to the media directory """
                    if (extensionGiven(rfilename)==False):
                        rfilename = rfilename+".xlsx"
                    file1 = request.FILES["file1"]
                    file2 = request.FILES["file2"]
                    folder = "/".join(uploaded_file1_path.split('/')[:-1])
                    callfunc = [folder+"/"+rfilename]
                    callfunc.append(uploaded_file1_path)
                    callfunc.append(uploaded_file2_path)
                    """ Call the java function with parameters as list"""
                    retval1 = verifyclass.verifyRDFFile(uploaded_file1_path)
                    if (len(retval1) > 0):
                        erroroccurred = True
                        message = "The following error(s)/warning(s) were raised by " + str(uploaded_file1) + ": " +str(retval1)
                    retval2 = verifyclass.verifyRDFFile(uploaded_file2_path)
                    if (len(retval2) > 0):
                        erroroccurred = True
                        message += "The following error(s)/warning(s) were raised by " + str(uploaded_file2) + ": " +str(retval2)
                    try :
                        compareclass.onlineFunction(callfunc)
                        """Return only the path starting with MEDIA_URL"""
                        index = folder.split("/").index('media')
                        result = "/"+("/".join(folder.split("/")[index:]))+'/'+rfilename
                        returnstatus = status.HTTP_201_CREATED
                        httpstatus = 201
                    except :
                        message += "While running compare tool " + format_exc()
                        returnstatus = status.HTTP_400_BAD_REQUEST
                        httpstatus = 400
                    if (erroroccurred == False):
                        returnstatus = status.HTTP_201_CREATED
                        httpstatus = 201
                    else :
                        returnstatus = status.HTTP_406_BAD_REQUEST
                        httpstatus = 406
                    jpype.detachThreadFromJVM()
                else :
                    message = "File Not Uploaded"
                    returnstatus = status.HTTP_400_BAD_REQUEST
                    httpstatus = 400
                    jpype.detachThreadFromJVM()
            except jpype.JavaException as ex :
                """ Error raised by verifyclass.verify without exiting the application"""
                message = jpype.JavaException.message(ex) #+ "This SPDX Document is not a valid RDF/XML or tag/value format"
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM()
            except :
                message = format_exc()
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM()

            query.message=message
            query.result=result
            query.status=httpstatus
            CompareFileUpload.objects.filter(file1=uploaded_file1).filter(file2=uploaded_file2).update(message=message, result=result, status=httpstatus)
            serial = CompareSerializerReturn(instance=query)
            return Response(
                serial.data,status=returnstatus
                )
        else:
            return Response(
                serializer.errors,status=status.HTTP_400_BAD_REQUEST
                )

@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def check_license(request):
    """ Handle Check License api request """
    if request.method == 'GET':
        """ Return all check license api request """
        query = CheckLicenseFileUpload.objects.all()
        serializer = CheckLicenseSerializer(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        """ Return check license tool result on the post file"""
        serializer = CheckLicenseSerializer(data=request.data)
        if serializer.is_valid():
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =settings.JAR_ABSOLUTE_PATH
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ Attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.compare")
            compareclass = package.LicenseCompareHelper
            query = CheckLicenseFileUpload.objects.create(
                owner=request.user,
                file=request.data.get('file')
            )
            uploaded_file = str(query.file)
            uploaded_file_path = str(query.file.path)
            """ Reading the license text file into a string variable """
            licensetext = query.file.read()
            try :
                if request.FILES["file"]:
                    """Call the java function with parameter"""
                    matching_licenses = compareclass.matchingStandardLicenseIds(licensetext)
                    if (matching_licenses and len(matching_licenses) > 0):
                        matching_str = "The following license ID(s) match: "
                        matching_str+= matching_licenses[0]
                        for i in range(1,len(matching_licenses)):
                            matching_str += ", "
                            matching_str += matching_licenses[i]
                        result = matching_str
                        returnstatus = status.HTTP_201_CREATED
                        httpstatus = 201
                        jpype.detachThreadFromJVM()

                    else:
                        result = "There are no matching SPDX listed licenses"
                        returnstatus = status.HTTP_400_BAD_REQUEST
                        httpstatus = 400
                        jpype.detachThreadFromJVM()

                else :
                    result = "File Not Uploaded"
                    returnstatus = status.HTTP_400_BAD_REQUEST
                    httpstatus = 400
                    jpype.detachThreadFromJVM()
            
            except jpype.JavaException as ex :
                """ Java exception raised without exiting the application """
                result = jpype.JavaException.message(ex) 
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM()
            except :
                """ Other errors raised"""
                result = format_exc()
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM()
            query.result = result
            query.status=httpstatus
            CheckLicenseFileUpload.objects.filter(file=uploaded_file).update(result=result,status=httpstatus)
            serial = CheckLicenseSerializerReturn(instance=query)
            return Response(
                serial.data, status=returnstatus
                )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )


@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
@permission_classes((AllowAny, ))
def submit_license(request):
    """ Handle submit license api request """
    if request.method == 'GET':
        """ Return all check license api request """
        query = SubmitLicenseModel.objects.all()
        serializer = SubmitLicenseSerializer(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        """ Return the result of license submittal on the post license details """
        serializer = SubmitLicenseSerializer(data=request.data)
        if serializer.is_valid():
            serverUrl = request.build_absolute_uri('/')
            githubClientId = settings.SOCIAL_AUTH_GITHUB_KEY
            githubClientSecret = settings.SOCIAL_AUTH_GITHUB_SECRET
            code = request.data.get('code')
            userId = request.data.get('user_id')
            if code is None or code.strip() == '':
                return Response({
                        "result": "No authentication code provided."
                    }, status=status.HTTP_400_BAD_REQUEST)
            if userId:
                # Used for API testing only
                user = User.objects.get(id=userId)
                token = request.data.get('token')
            else:
                try:
                    token = generate_github_access_token(githubClientId, githubClientSecret, code)
                except PermissionDenied:
                    return Response({
                            "result": "Authentication code provided is incorrect."
                        }, status=status.HTTP_400_BAD_REQUEST)
                clientId = settings.OAUTHTOOLKIT_APP_CLIENT_ID
                clientSecret = settings.OAUTHTOOLKIT_APP_CLIENT_SECRET
                backend = settings.BACKEND
                djangoToken = convert_to_auth_token(serverUrl, clientId, clientSecret, backend, token)
                user = get_user_from_token(djangoToken)

            licenseName = request.data.get('fullname')
            licenseIdentifier = request.data.get('shortIdentifier')
            licenseAuthorName = request.data.get('licenseAuthorName')
            userEmail = request.data.get('userEmail')
            licenseSourceUrls = [request.data.get('sourceUrl')]
            licenseOsi = request.data.get('osiApproved')
            licenseComments = request.data.get('comments')
            licenseHeader = request.data.get('licenseHeader')
            licenseText = request.data.get('text')
            result=request.data.get('result')
            listVersionAdded = ''
            licenseNotes = ''
            result = validate_license_fields(licenseName, licenseIdentifier)
            if result != '1':
                return Response({
                    "result": [result]
                }, status=status.HTTP_400_BAD_REQUEST)

            xml = generateLicenseXml(licenseOsi, licenseIdentifier, licenseName,
                listVersionAdded, licenseSourceUrls, licenseHeader, licenseNotes, licenseText)
            now = datetime.datetime.now()
            licenseRequest = LicenseRequest(licenseAuthorName=licenseAuthorName, fullname=licenseName, shortIdentifier=licenseIdentifier,
                submissionDatetime=now, userEmail=userEmail, notes=licenseNotes, xml=xml)
            licenseRequest.save()
            licenseId = LicenseRequest.objects.get(shortIdentifier=licenseIdentifier).id
            licenseRequestUrl = join(serverUrl, reverse('license-requests')[1:], str(licenseId))
            query = SubmitLicenseModel.objects.create(
                owner=user,
                fullname=licenseName,
                shortIdentifier=licenseIdentifier,
                licenseAuthorName=licenseAuthorName,
                userEmail=userEmail,
                sourceUrl=licenseSourceUrls,
                osiApproved=licenseOsi,
                comments=licenseComments,
                licenseHeader=licenseHeader,
                text=licenseText,
                xml=xml,
                result=result
            )
            urlType = NORMAL
            if 'urlType' in request.POST:
                # This is present only when executing submit license via tests
                urlType = request.POST["urlType"]
            statusCode = createIssue(licenseAuthorName, licenseName, licenseIdentifier, licenseComments, licenseSourceUrls, licenseHeader, licenseOsi, licenseRequestUrl, token, urlType)
            if str(statusCode) == '201':
                result = "Success! The license request has been successfully submitted."
                query.result = result
                query.status = str(statusCode)
                SubmitLicenseModel.objects.filter(fullname=request.data.get('fullname')).update(result=result,status=statusCode)
            serial = SubmitLicenseSerializerReturn(instance=query)
            return Response(
                serial.data, status=str(statusCode)
                )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )


def generateLicenseXml(licenseOsi, licenseIdentifier, licenseName, listVersionAdded, licenseSourceUrls, licenseHeader, licenseNotes, licenseText):
    """ View for generating a spdx license xml
    returns the license xml as a string
    """
    root = ET.Element("SPDXLicenseCollection", xmlns="http://www.spdx.org/license")
    if licenseOsi=="Approved":
        licenseOsi = "true"
    else:
        licenseOsi = "false"
    license = ET.SubElement(root, "license", isOsiApproved=licenseOsi, licenseId=licenseIdentifier, name=licenseName, listVersionAdded=listVersionAdded)
    crossRefs = ET.SubElement(license, "crossRefs")
    for sourceUrl in licenseSourceUrls:
        ET.SubElement(crossRefs, "crossRef").text = sourceUrl
    ET.SubElement(license, "standardLicenseHeader").text = licenseHeader
    ET.SubElement(license, "notes").text = licenseNotes
    licenseTextElement = ET.SubElement(license, "text")
    licenseLines = licenseText.replace('\r','').split('\n')
    for licenseLine in licenseLines:
        ET.SubElement(licenseTextElement, "p").text = licenseLine
    xmlString = ET.tostring(root, method='xml').replace('>','>\n')
    return xmlString


def createIssue(licenseAuthorName, licenseName, licenseIdentifier, licenseComments, licenseSourceUrls, licenseHeader, licenseOsi, licenseRequestUrl, token, urlType):
    """ View for creating an GitHub issue
    when submitting a new license request
    """
    body = '**1.** License Name: ' + licenseName + '\n**2.** Short identifier: ' + licenseIdentifier + '\n**3.** License Author or steward: ' + licenseAuthorName + '\n**4.** Comments: ' + licenseComments + '\n**5.** Standard License Header: ' + licenseHeader + '\n**6.** License Request Url: ' + licenseRequestUrl + '\n**7.** URL: '
    for url in licenseSourceUrls:
        body += url
        body += '\n'
    body += '**8.** OSI Status: ' + licenseOsi
    title = 'New license request: ' + licenseIdentifier + ' [SPDX-Online-Tools]'
    payload = {'title' : title, 'body': body, 'labels': ['new license/exception request']}
    headers = {'Authorization': 'token ' + token}
    url = TYPE_TO_URL[urlType]
    r = post(url, data=dumps(payload), headers=headers)
    return r.status_code


def validate_license_fields(licenseName, licenseIdentifier):
    """ Validate the licenseName and licenseIdentifier
    when submitting a new license
    """
    no_comma_match = bool(re.compile(r'^((?!,).)*$').match(licenseName))
    no_version_match = bool(re.compile(r'^((?!version).)*$').match(licenseName))
    lower_v_match = bool(re.compile(r'^((?!v\.|v\s).)*$').match(licenseName))
    the_match = bool(re.compile(r'^(?!the|The.*$).*$').match(licenseName))

    if not no_comma_match:
        return 'No commas allowed in the fullname of license or exception.'
    elif not no_version_match:
        return 'The word "version" is not spelled out. Use "v" instead of "version".'
    elif not lower_v_match:
        return 'For version, use lower case v and no period or space between v and the version number.'
    elif not the_match:
        return 'The fullname must omit certain words such as "the " for alphabetical sorting purposes.'
    else:
        return '1'
