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
# limitations under the License

from django.test import TestCase
from unittest import skipIf
from src.secret import getAuthCode,getGithubKey,getGithubSecret
from django.core.exceptions import ObjectDoesNotExist,PermissionDenied
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import now, timedelta

from rest_framework.test import APITestCase,APIClient
from oauth2_provider.models import AccessToken,Application
from oauth2_provider.settings import oauth2_settings
from oauthlib.common import generate_token
from rest_framework.authtoken.models import Token

from requests import get
from json import dumps, loads
from api.oauth import generate_github_access_token,get_user_from_token
from api.views import generateLicenseXml

from api.models import ValidateFileUpload,ConvertFileUpload,CompareFileUpload,SubmitLicenseModel
from django.conf import settings
import os

def getExamplePath(filename):
    return os.path.join(settings.EXAMPLES_DIR, filename)

class ConvertFileUploadTests(APITestCase):
    """ Test for convert api with all
    possible combination of POST and GET 
    request with login enabled.
    """
    def setUp(self):
        self.username = "convertapitestuser"
        self.password = "convertapitestpass"
        self.tearDown()
        self.credentials = {'username':self.username,'password':self.password }
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.tag = "TAG"
        self.rdf = "RDFXML"
        self.xlsx = "XLS"
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.2.spdx"), 'rb')
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf.xml"), 'rb')
        self.xlsx_file = open(getExamplePath("SPDXSpreadsheetExample-v2.2.xls"), 'rb')

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        ConvertFileUpload.objects.all().delete()

    def test_convert_api(self):
        """Access get without login"""
        resp1 = self.client.get(reverse("convert-api"))
        self.assertTrue(resp1.status_code,403)
        """Access get after login"""
        self.client.login(username=self.username,password=self.password)
        resp2 = self.client.get(reverse("convert-api"))
        self.assertTrue(resp2.status_code,200)
        self.client.logout()

    def test_convert_tagtordf_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.tv_file,"from_format":self.tag,"to_format":self.rdf,"cfilename":"tagtordf-apitest"},format="multipart")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_tagtoxlsx_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.tv_file,"from_format":self.tag,"to_format":self.xlsx,"cfilename":"tagtoxlsx-apitest"},format="multipart")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_rdftotag_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.rdf_file,"from_format":self.rdf,"to_format":self.tag,"cfilename":"rdftotag-apitest"},format="multipart")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertTrue(resp.data['result'].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_rdftoxlsx_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.rdf_file,"from_format":self.rdf,"to_format":self.xlsx,"cfilename":"rdftoxlsx-apitest"},format="multipart")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_xlsxtordf_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"from_format":self.xlsx,"to_format":self.rdf,"cfilename":"xlsxtordf-apitest"},format="multipart")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_xlsxtotag_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"from_format":self.xlsx,"to_format":self.tag,"cfilename":"xlsxtotag-apitest"},format="multipart")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_without_one_argument(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"to_format":self.tag,"cfilename":"xlsxtotag-apitest"},format="multipart")
        self.assertEqual(resp.status_code,400)
        
        resp2 = self.client.post(reverse("convert-api"),{"from_format":self.xlsx,"to_format":self.tag,"cfilename":"xlsxtotag-apitest"},format="multipart")
        self.assertEqual(resp2.status_code,400)
        
        resp3 = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"from_format":self.xlsx,"to_format":self.tag},format="multipart")
        self.assertEqual(resp3.status_code,400)
        
        resp4 = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"from_format":self.xlsx,"cfilename":"xlsxtotag-apitest"},format="multipart")
        self.assertEqual(resp4.status_code,400)
        self.client.logout()