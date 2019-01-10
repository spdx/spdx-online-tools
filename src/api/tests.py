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
# limitations under the License


from __future__ import unicode_literals

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse

from rest_framework.test import APITestCase,APIClient
from rest_framework.authtoken.models import Token

from api.models import ValidateFileUpload,ConvertFileUpload,CompareFileUpload,CheckLicenseFileUpload


class ValidateFileUploadTests(APITestCase):
    """ Test for validate api with all
    possible combination of POST and GET 
    request with login enabled.
    """
    def setUp(self):
        self.username = "validateapitestuser"
        self.password = "validateapitestpass"
        self.tearDown()
        self.credentials = {'username':self.username,
            'password':self.password
            }
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        self.invalid_tv_file = open("examples/SPDXTagExample-v2.0_invalid.spdx")
        self.invalid_rdf_file = open("examples/SPDXRdfExample-v2.0_invalid.rdf")

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        ValidateFileUpload.objects.all().delete()

    def test_validate_api(self):
        """Access get without login"""
        resp1 = self.client.get(reverse("validate-api"))
        self.assertTrue(resp1.status_code,403)
        self.client.login(username=self.username,password=self.password)
        """ Access get after login"""
        resp2 = self.client.get(reverse("validate-api")) 
        self.assertTrue(resp2.status_code,200)
        """ Valid Tag Value File"""
        resp3 = self.client.post(reverse("validate-api"),{"file":self.tv_file},format="multipart")
        self.assertEqual(resp3.status_code,201)
        self.assertEqual(resp3.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp3.data["result"],"This SPDX Document is valid.")
        """ Valid RDF File"""
        resp4 = self.client.post(reverse("validate-api"),{"file":self.rdf_file},format="multipart")
        self.assertEqual(resp4.status_code,201)
        self.assertEqual(resp4.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp4.data["result"],"This SPDX Document is valid.")
        """ Invalid Tag Value File"""
        resp5 = self.client.post(reverse("validate-api"),{"file":self.invalid_tv_file},format="multipart")
        self.assertEqual(resp5.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp5.status_code,400)
        self.assertNotEqual(resp5.data["result"],"This SPDX Document is valid.")
        """ Invalid RDF File"""
        resp6 = self.client.post(reverse("validate-api"),{"file":self.invalid_rdf_file},format="multipart")
        self.assertEqual(resp6.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp6.status_code,400)
        self.assertNotEqual(resp6.data["result"],"This SPDX Document is valid.")
        self.client.logout()
        self.tearDown()
        
    def test_validate_without_argument(self):
        self.client.login(username=self.username,password=self.password)
        resp7 = self.client.post(reverse("validate-api"),{},format="multipart")
        self.assertEqual(resp7.status_code,400)
        self.client.logout()
        self.tearDown()

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
        self.tag = "Tag"
        self.rdf = "RDF"
        self.xlsx = "Spreadsheet"
        self.html ="HTML"
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        self.xlsx_file = open("examples/SPDXSpreadsheetExample-2.0.xls")

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
        self.assertTrue(resp.status_code==406 or resp.status_code == 201)
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertTrue(resp.data["tagToRdfFormat"]=="RDF/XML-ABBREV")
        self.client.logout()

    def test_convert_tagtoxlsx_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.tv_file,"from_format":self.tag,"to_format":self.xlsx,"cfilename":"tagtoxlsx-apitest"},format="multipart")
        self.assertTrue(resp.status_code==406 or resp.status_code == 201)
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_rdftotag_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.rdf_file,"from_format":self.rdf,"to_format":self.tag,"cfilename":"rdftotag-apitest"},format="multipart")
        self.assertTrue(resp.status_code==406 or resp.status_code == 201)
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_rdftoxlsx_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.rdf_file,"from_format":self.rdf,"to_format":self.xlsx,"cfilename":"rdftoxlsx-apitest"},format="multipart")
        self.assertTrue(resp.status_code==406 or resp.status_code == 201)
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    # def test_convert_rdftohtml_api(self):
    #     self.client.login(username=self.username,password=self.password)
    #     resp = self.client.post(reverse("convert-api"),{"file":self.rdf_file,"from_format":self.rdf,"to_format":self.html,"cfilename":"rdftohtml-apitest"},format="multipart")
    #     self.assertTrue(resp.status_code==406 or resp.status_code == 201)
    #     self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
    #     self.client.logout()

    def test_convert_xlsxtordf_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"from_format":self.xlsx,"to_format":self.rdf,"cfilename":"xlsxtordf-apitest"},format="multipart")
        self.assertTrue(resp.status_code==406 or resp.status_code == 201)
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_xlsxtotag_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"from_format":self.xlsx,"to_format":self.tag,"cfilename":"xlsxtotag-apitest"},format="multipart")
        self.assertTrue(resp.status_code==406 or resp.status_code == 201)
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
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        self.rdf_file2 = open("examples/SPDXRdfExample.rdf")
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")

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
        resp3 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"file2":self.rdf_file2,"rfilename":"compare-apitest.xlsx"},format="multipart")
        self.assertTrue(resp3.status_code==406 or resp3.status_code == 201)
        self.assertEqual(resp3.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertTrue(resp3.data["result"].startswith(settings.MEDIA_URL))
        """Compare with one  invalid RDF files"""
        resp4 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"file2":self.tv_file,"rfilename":"compare-apitest.xlsx"},format="multipart")
        self.assertEqual(resp4.status_code,400)
        self.client.logout()
        self.tearDown()
        
    def test_compare_without_one_argument(self):
        self.client.login(username=self.username,password=self.password)
        resp5 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"file2":self.rdf_file2},format="multipart")
        self.assertEqual(resp5.status_code,400)
        
        resp6 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"rfilename":"compare-apitest.xlsx"},format="multipart")
        self.assertEqual(resp6.status_code,400)
        
        resp7 = self.client.post(reverse("compare-api"),{"file2":self.rdf_file,"rfilename":"compare-apitest.xlsx"},format="multipart")
        self.assertEqual(resp7.status_code,400)
        self.client.logout()
        self.tearDown()

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
        self.license_file = open("examples/AFL-1.1.txt")
        self.other_file = open("examples/Other.txt")
        
    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        CheckLicenseFileUpload.objects.all().delete()

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
        self.assertEqual(resp3.status_code,201)
        self.assertEqual(resp3.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp3.data["result"],"The following license ID(s) match: AFL-1.1")
        """ Other File"""
        resp4 = self.client.post(reverse("check_license-api"),{"file":self.other_file},format="multipart")
        self.assertEqual(resp4.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp4.status_code,400)
        self.assertEqual(resp4.data["result"],"There are no matching SPDX listed licenses")
        
    def test_checklicense_without_argument(self):
        self.client.login(username=self.username,password=self.password)
        resp5 = self.client.post(reverse("check_license-api"),{},format="multipart")
        self.assertEqual(resp5.status_code,400)
        self.client.logout()
        self.tearDown()
