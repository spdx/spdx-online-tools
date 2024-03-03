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

class CheckLicenseFileUploadTests(APITestCase):

    def setUp(self):
        self.username = "checklicenseapitestuser"
        self.password = "checklicenseapitestpass"
        self.tearDown()
        self.credentials = {'username':self.username,
            'password':self.password
            }
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.license_file = open(getExamplePath("AFL-1.1.txt"))
        self.other_file = open(getExamplePath("Other.txt"))
        
    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass

    def test_checklicense_api(self):
        """Access get without login"""
        resp1 = self.client.get(reverse("check_license-api"))
        self.assertTrue(resp1.status_code,403)
        self.client.login(username=self.username,password=self.password)
        """ Access get after login"""
        resp2 = self.client.get(reverse("check_license-api")) 
        self.assertTrue(resp2.status_code,200)
        """ Valid License File"""
        resp3 = self.client.post(reverse("check_license-api"),{"file":self.license_file},format="multipart")
        self.assertEqual(resp3.status_code,200)
        self.assertEqual(resp3.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp3.data["result"],"The following license ID(s) match: AFL-1.1")
        """ Other File"""
        resp4 = self.client.post(reverse("check_license-api"),{"file":self.other_file},format="multipart")
        self.assertEqual(resp4.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp4.status_code,404)
        self.assertEqual(resp4.data["result"],"There are no matching SPDX listed licenses")
        
    def test_checklicense_without_argument(self):
        self.client.login(username=self.username,password=self.password)
        resp5 = self.client.post(reverse("check_license-api"),{},format="multipart")
        self.assertEqual(resp5.status_code,400)
        self.client.logout()
        self.tearDown()