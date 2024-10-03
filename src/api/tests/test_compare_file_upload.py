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

class CompareFileUploadTests(APITestCase):
    """ Test for compare api with all
    possible combination of POST and GET 
    request with login enabled.
    """
    def setUp(self):
        self.username = "compareapitestuser"
        self.password = "compareapitestpass"
        self.tearDown()
        self.credentials = {'username':self.username,'password':self.password }
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.0.rdf"))
        self.rdf_file2 = open(getExamplePath("SPDXRdfExample.rdf"))
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"))

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        CompareFileUpload.objects.all().delete()

    def test_compare_api(self):
        """Access get without login"""
        resp1 = self.client.get(reverse("compare-api"))
        self.assertTrue(resp1.status_code,403)
        """Access get after login"""
        self.client.login(username=self.username,password=self.password)
        resp2 = self.client.get(reverse("compare-api"))
        self.assertTrue(resp2.status_code,200)
        """Compare two valid RDF files"""
        resp3 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"file2":self.rdf_file2,"rfilename":"compare-apitest.xls"},format="multipart")
        self.assertEqual(resp3.status_code,200)
        self.assertEqual(resp3.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertTrue(resp3.data["result"].startswith(settings.MEDIA_URL))
        """Compare with one  invalid RDF files"""
        resp4 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"file2":self.tv_file,"rfilename":"compare-apitest.xls"},format="multipart")
        self.assertEqual(resp4.status_code,400)
        self.client.logout()
        self.tearDown()
        
    def test_compare_without_one_argument(self):
        self.client.login(username=self.username,password=self.password)
        resp5 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"file2":self.rdf_file2},format="multipart")
        self.assertEqual(resp5.status_code,400)
        
        resp6 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"rfilename":"compare-apitest.xls"},format="multipart")
        self.assertEqual(resp6.status_code,400)
        
        resp7 = self.client.post(reverse("compare-api"),{"file2":self.rdf_file,"rfilename":"compare-apitest.xls"},format="multipart")
        self.assertEqual(resp7.status_code,400)
        self.client.logout()
        self.tearDown()