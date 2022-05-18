# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2017 Rohit Lodha
# Copyright (c) 2017 Rohit Lodha
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
from django.utils.datastructures import MultiValueDict

import codecs
import jpype
import re
import datetime
import xml.etree.cElementTree as ET
import app.core as core
import api.utils as utils

from app.generateXml import generateLicenseXml
from app.utils import createIssue

from traceback import format_exc
from os.path import abspath, join, sep, splitext
from time import time
from urllib.parse import urljoin
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
            core.initialise_jpype()
            response = core.license_validate_helper(request)
            httpstatus, _, result = utils.get_json_response_data(response)
            jpype.detachThreadFromJVM()
            returnstatus = utils.get_return_code(httpstatus)
            query = ValidateFileUpload.objects.create(owner=request.user, file=request.data.get('file'))
            query.result = result
            query.status = httpstatus
            uploaded_file = str(query.file)
            uploaded_file_path = str(query.file.path)
            ValidateFileUpload.objects.filter(file=uploaded_file).update(result=result, status=httpstatus)
            serial = ValidateSerializerReturn(instance=query)
            return Response(
                serial.data, status=returnstatus
                )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )


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
            core.initialise_jpype()
            response = core.license_convert_helper(request)
            jpype.detachThreadFromJVM()
            httpstatus, result, message = utils.get_json_response_data(response)
            returnstatus = utils.get_return_code(httpstatus)
            
            if httpstatus != 200:
                message = 'Failed'
            
            query = ConvertFileUpload.objects.create(
                owner=request.user,
                file=request.data.get('file'),
                from_format=request.POST["from_format"],
                to_format=request.POST["to_format"],
                cfilename=request.POST["cfilename"],
            )
            uploaded_file = str(query.file)
            uploaded_file_path = str(query.file.path)
            query.message = message
            query.status = httpstatus
            query.result = result
            ConvertFileUpload.objects.filter(file=uploaded_file).update(status=httpstatus, result=result, message=message)
            serial = ConvertSerializerReturn(instance=query)
            return Response(
                serial.data,status=returnstatus
                )
        else:
            return Response(
                serializer.errors,status=status.HTTP_400_BAD_REQUEST
                )


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
            core.initialise_jpype()
            file1 = request.data.get('file1')
            file2 = request.data.get('file2')
            files = [file1, file2]
            request.FILES.setlist('files', files)
            response = core.license_compare_helper(request)
            httpstatus, result, message = utils.get_json_response_data(response)
            returnstatus = utils.get_return_code(httpstatus)
            
            if httpstatus != 200:
                message = 'Failed'

            rfilename = request.POST["rfilename"]
            query = CompareFileUpload.objects.create(
                owner=request.user,
                file1=file1,
                file2=file2,
                rfilename = rfilename,
            )
            uploaded_file1 = str(query.file1)
            uploaded_file2 = str(query.file2)
            uploaded_file1_path = str(query.file1.path)
            uploaded_file2_path = str(query.file2.path)
            query.message = message
            query.result = result
            query.status = httpstatus
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
            core.initialise_jpype()
            query = CheckLicenseFileUpload.objects.create(owner=request.user, file=request.data.get('file'))
            uploaded_file = str(query.file)
            uploaded_file_path = str(query.file.path)
            """ Reading the license text file into a string variable """
            licensetext = codecs.open(uploaded_file_path, 'r', encoding='unicode_escape').read()
            request.data['licensetext'] = str(licensetext)
            response = core.license_check_helper(request)
            jpype.detachThreadFromJVM()

            httpstatus, result, message = utils.get_json_response_data(response)
            returnstatus = utils.get_return_code(httpstatus)
            
            query.result = result
            query.status = httpstatus
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
            result = utils.validate_license_fields(licenseName, licenseIdentifier)
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
