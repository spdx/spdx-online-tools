# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2025-present SPDX Contributors
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2017 Rohit Lodha

from django.http import JsonResponse
from rest_framework import serializers as drf_serializers, status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer

from api.models import ValidateFileUpload, ConvertFileUpload, CompareFileUpload, SubmitLicenseModel
from api.serializers import (
    ValidateSerializer, ValidateSerializerReturn,
    ConvertSerializer, ConvertSerializerReturn,
    CompareSerializer, CompareSerializerReturn,
    CheckLicenseSerializer,
    SubmitLicenseSerializer, SubmitLicenseSerializerReturn,
)
from api.oauth import generate_github_access_token, convert_to_auth_token, get_user_from_token
from app.models import LicenseRequest

from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User

import datetime

import app.core as core
import api.utils as utils

from app.generateXml import generateLicenseXml
from app.utils import check_spdx_license, createIssue

from os.path import join


NORMAL = "normal"
TESTS = "tests"

TYPE_TO_URL = {
    NORMAL: settings.REPO_URL,
    TESTS: settings.DEV_REPO_URL,
}



# --- start /api2/ ViewSets -----

class ValidateViewSet(ModelViewSet):
    """Returns all validate API request"""
    queryset = ValidateFileUpload.objects.all()
    serializer_class = ValidateSerializerReturn
    parser_classes = (MultiPartParser, FormParser,)


class ConvertViewSet(ModelViewSet):
    """Returns all convert API request"""
    queryset = ConvertFileUpload.objects.all()
    serializer_class = ConvertSerializerReturn
    parser_classes = (MultiPartParser, FormParser,)


class CompareViewSet(ModelViewSet):
    """Returns all compare API request"""
    queryset = CompareFileUpload.objects.all()
    serializer_class = CompareSerializerReturn
    parser_classes = (MultiPartParser, FormParser,)

# --- end /api2/ ViewSets -----

_FORMAT_CHOICES = ['TAG', 'RDFXML', 'RDFTTL', 'JSON', 'XML', 'YAML', 'XLS', 'XLSX', 'JSONLD']
_FORMAT_HELP = (
    'File format of the document. '
    'TAG = Tag/Value (v2), RDFXML = RDF/XML (v2), RDFTTL = RDF/Turtle (v2), '
    'JSON = JSON (v2), XML = XML (v2), YAML = YAML (v2), '
    'XLS/XLSX = Spreadsheet (v2), JSONLD = JSON-LD (v3).'
)


@extend_schema(
    methods=['GET'],
    summary='List the authenticated user\'s past validate requests',
    description='Returns the authenticated user\'s historical SPDX document validation requests.',
    responses={200: ValidateSerializerReturn(many=True)},
    tags=['SBOM'],
)
@extend_schema(
    methods=['POST'],
    summary='Validate an SPDX document',
    description=(
        'Validates an SPDX document against the SPDX specification.\n\n'
        '**Backend:** SPDX Java Tools.'
    ),
    request=inline_serializer(
        name='ValidateRequest',
        fields={
            'file': drf_serializers.FileField(help_text='SPDX document to validate.'),
            'format': drf_serializers.ChoiceField(choices=_FORMAT_CHOICES, help_text=_FORMAT_HELP),
        },
    ),
    responses={
        200: ValidateSerializerReturn,
        400: OpenApiResponse(description='Validation failed or invalid request parameters.'),
        401: OpenApiResponse(description='Authentication required.'),
        404: OpenApiResponse(description='No file submitted.'),
    },
    tags=['SBOM'],
)
@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))

def validate(request):
    """Handle Validate API request"""
    if request.method == 'GET':
        # Return all validate API requests
        query = ValidateFileUpload.objects.all()
        serializer = ValidateSerializer(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Return validate tool result on the post file
        serializer = ValidateSerializer(data=request.data)

        if serializer.is_valid():
            core.initialise_jpype()
            with core.jvm_thread():
                response = core.license_validate_helper(request)
            httpstatus, _, result = utils.get_json_response_data(response)
            returnstatus = utils.get_return_code(httpstatus)
            uploaded_file_obj = request.FILES.get("file") or request.data.get("file")
            query = ValidateFileUpload.objects.create(
                owner=request.user, file=uploaded_file_obj
            )
            query.result = result
            query.status = httpstatus
            uploaded_file = str(query.file)
            ValidateFileUpload.objects.filter(file=uploaded_file).update(
                result=result, status=httpstatus
            )
            serial = ValidateSerializerReturn(instance=query)
            return Response(serial.data, status=returnstatus)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=['GET'],
    summary='List the authenticated user\'s past convert requests',
    description='Returns the authenticated user\'s historical SPDX document conversion requests.',
    responses={200: ConvertSerializerReturn(many=True)},
    tags=['SBOM'],
)
@extend_schema(
    methods=['POST'],
    summary='Convert an SPDX document to another format',
    description=(
        'Converts an SPDX document from one serialization format to another.\n\n'
        'On success, the `result` field contains a relative URL to download the converted file.\n\n'
        '**Backend:** SPDX Java Tools.'
    ),
    request=inline_serializer(
        name='ConvertRequest',
        fields={
            'file': drf_serializers.FileField(help_text='SPDX document to convert.'),
            'from_format': drf_serializers.ChoiceField(choices=_FORMAT_CHOICES, help_text='Source format. ' + _FORMAT_HELP),
            'to_format': drf_serializers.ChoiceField(choices=_FORMAT_CHOICES, help_text='Target format. ' + _FORMAT_HELP),
            'cfilename': drf_serializers.CharField(
                max_length=32,
                help_text='Base name for the output file (without extension, max 32 chars). The server appends the correct extension.',
            ),
        },
    ),
    responses={
        200: ConvertSerializerReturn,
        400: OpenApiResponse(description='Conversion failed or invalid request parameters.'),
        401: OpenApiResponse(description='Authentication required.'),
        404: OpenApiResponse(description='No file submitted.'),
        406: OpenApiResponse(description='Conversion completed but validation warnings were raised.'),
    },
    tags=['SBOM'],
)
@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))

def convert(request):
    """Handle Convert API request"""
    if request.method == 'GET':
        # Return all convert API requests
        query = ConvertFileUpload.objects.all()
        serializer = ConvertSerializer(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Return convert tool result on the post file
        serializer = ConvertSerializer(data=request.data)
        if serializer.is_valid():
            core.initialise_jpype()
            with core.jvm_thread():
                response = core.license_convert_helper(request)
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
            print("uploaded_file_path:", uploaded_file_path)
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


@extend_schema(
    methods=['GET'],
    summary='List the authenticated user\'s past compare requests',
    description='Returns the authenticated user\'s historical SPDX document comparison requests.',
    responses={200: CompareSerializerReturn(many=True)},
    tags=['SBOM'],
)
@extend_schema(
    methods=['POST'],
    summary='Compare two SPDX documents',
    description=(
        'Compares two SPDX documents and produces a difference report.\n\n'
        'On success, the `result` field contains a relative URL to download the Excel (.xls) comparison report.\n\n'
        '**Backend:** SPDX Java Tools.'
    ),
    request=inline_serializer(
        name='CompareRequest',
        fields={
            'file1': drf_serializers.FileField(help_text='First SPDX document.'),
            'file2': drf_serializers.FileField(help_text='Second SPDX document.'),
            'rfilename': drf_serializers.CharField(
                max_length=32,
                help_text='Base name for the comparison report file (max 32 chars).',
            ),
        },
    ),
    responses={
        200: CompareSerializerReturn,
        400: OpenApiResponse(description='Comparison failed or invalid request parameters.'),
        401: OpenApiResponse(description='Authentication required.'),
        404: OpenApiResponse(description='One or both files not submitted.'),
    },
    tags=['SBOM'],
)
@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))

def compare(request):
    """Handle Compare API request"""
    if request.method == 'GET':
        # Return all compare API requests
        query = CompareFileUpload.objects.all()
        serializer = CompareSerializerReturn(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Return compare tool result on the post file
        serializer = CompareSerializer(data=request.data)
        if serializer.is_valid():
            core.initialise_jpype()
            file1 = request.data.get('file1')
            file2 = request.data.get('file2')
            files = [file1, file2]
            request.FILES.setlist('files', files)
            with core.jvm_thread():
                response = core.license_compare_helper(request)
            httpstatus, result, message = utils.get_json_response_data(response)
            returnstatus = utils.get_return_code(httpstatus)

            if httpstatus != 200:
                message = 'Failed'

            rfilename = request.POST["rfilename"]
            file1_obj = request.FILES.get("file1") or file1
            file2_obj = request.FILES.get("file2") or file2
            query = CompareFileUpload.objects.create(
                owner=request.user,
                file1=file1_obj,
                file2=file2_obj,
                rfilename=rfilename,
            )
            uploaded_file1 = str(query.file1)
            uploaded_file2 = str(query.file2)
            query.message = message
            query.result = result
            query.status = httpstatus
            CompareFileUpload.objects.filter(file1=uploaded_file1).filter(
                file2=uploaded_file2
            ).update(message=message, result=result, status=httpstatus)
            serial = CompareSerializerReturn(instance=query)
            return Response(serial.data, status=returnstatus)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary='Match license text to an SPDX license ID',
    description=(
        'Matches the text of a license against the SPDX License List and returns the best matching '
        'SPDX license identifier.\n\n'
        '**Backend:** SPDX License Matcher.'
    ),
    request=inline_serializer(
        name='CheckLicenseRequest',
        fields={
            'file': drf_serializers.FileField(
                help_text='Plain text file containing the license text to match (UTF-8 encoded).',
            ),
        },
    ),
    responses={
        200: inline_serializer(
            name='CheckLicenseResponse',
            fields={
                'matched_license': drf_serializers.CharField(
                    allow_null=True,
                    help_text='SPDX license identifier of the best match, or null if no match was found.',
                ),
                'match_type': drf_serializers.CharField(
                    help_text='"Perfect match", "Standard License match", "Close match", or "No match".',
                ),
                'all_matches': drf_serializers.DictField(
                    child=drf_serializers.FloatField(),
                    help_text='Map of SPDX license ID to match score for all candidates evaluated.',
                ),
            },
        ),
        401: OpenApiResponse(description='Authentication required.'),
        404: OpenApiResponse(description='No match found (matched_license is null).'),
    },
    tags=['License'],
)
@api_view(['POST'])
def check_license(request):
    """Handle Check License API request"""
    if request.method == 'POST':
        serializer = CheckLicenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        license_text = serializer.validated_data['file'].read().decode('utf8')
        core.initialise_jpype()
        with core.jvm_thread():
            matching_id, matching_type, all_matches = check_spdx_license(license_text)
        response = {
            "matched_license": matching_id,
            "match_type": matching_type,
            "all_matches": all_matches,
        }
        return JsonResponse(response, status=200 if matching_id else 404)


@extend_schema(
    methods=['GET'],
    summary='List all past license submission requests',
    description='Returns the authenticated user\'s historical license submission requests.',
    responses={200: SubmitLicenseSerializer(many=True)},
    tags=['License'],
)
@extend_schema(
    methods=['POST'],
    summary='Submit a new license to the SPDX License List',
    description=(
        'Submits a new license for inclusion in the '
        '[SPDX License List](https://spdx.org/licenses/). '
        'On success, a GitHub issue is created in '
        '[spdx/license-list-XML](https://github.com/spdx/license-list-XML).\n\n'
        'Requires a short-lived, single-use GitHub OAuth `code` from the OAuth callback. '
        'Obtain it by directing the user through the GitHub OAuth flow '
        '(`https://github.com/login/oauth/authorize`).\n\n'
        '**License name rules** (`fullname`): no commas; use `v` not `version` '
        '(e.g. `MIT License v2`); version format — lowercase `v`, no space or period '
        'before the number; omit leading words like `the` that affect alphabetical sorting.\n\n'
        '**Backend:** GitHub API '
        '(issue creation in [spdx/license-list-XML](https://github.com/spdx/license-list-XML/issues)).'
    ),
    request=inline_serializer(
        name='SubmitLicenseRequest',
        fields={
            'code': drf_serializers.CharField(
                help_text='GitHub OAuth authorization code. Short-lived and single-use.',
            ),
            'fullname': drf_serializers.CharField(
                max_length=70,
                help_text='Full license name (max 70 chars). No commas; use "v" not "version".',
            ),
            'shortIdentifier': drf_serializers.CharField(
                max_length=25,
                help_text='Proposed SPDX short identifier (max 25 chars).',
            ),
            'userEmail': drf_serializers.EmailField(
                max_length=35,
                help_text='Submitter email address (max 35 chars).',
            ),
            'sourceUrl': drf_serializers.URLField(
                max_length=255,
                help_text='Canonical URL of the license source (max 255 chars).',
            ),
            'text': drf_serializers.CharField(
                help_text='Full text of the license.',
            ),
            'licenseAuthorName': drf_serializers.CharField(
                max_length=100,
                required=False,
                allow_blank=True,
                help_text='Name of the license author (optional, max 100 chars).',
            ),
            'osiApproved': drf_serializers.ChoiceField(
                choices=['-', 'Approved', 'Not Submitted', 'Pending', 'Rejected', 'Unknown'],
                required=False,
                default='-',
                help_text='OSI approval status (optional).',
            ),
            'comments': drf_serializers.CharField(
                required=False,
                allow_blank=True,
                help_text='Additional comments about the license (optional).',
            ),
            'licenseHeader': drf_serializers.CharField(
                max_length=25,
                required=False,
                allow_blank=True,
                help_text='Standard license header text, if any (optional, max 25 chars).',
            ),
        },
    ),
    responses={
        201: SubmitLicenseSerializerReturn,
        400: OpenApiResponse(
            description='Validation error, invalid OAuth code, or license name rule violation.'
        ),
    },
    tags=['License'],
)
@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def submit_license(request):
    """Handle submit license API request"""
    if request.method == 'GET':
        # Return all check license API requests
        query = SubmitLicenseModel.objects.all()
        serializer = SubmitLicenseSerializer(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Return the result of license submittal on the post license details
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
            statusCode, githubIssueId = createIssue(licenseAuthorName, licenseName, licenseIdentifier, licenseComments, licenseSourceUrls, licenseHeader, licenseOsi, licenseRequestUrl, token, urlType)
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
