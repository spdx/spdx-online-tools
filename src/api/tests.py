# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse

from rest_framework.test import APITestCase,APIClient
from rest_framework.authtoken.models import Token

from models import ValidateFileUpload,ConvertFileUpload,CompareFileUpload

class ValidateFileUploadTests(APITestCase):
    def setUp(self):
        self.username = "validateapitestuser"
        self.password = "validateapitestpass"
        self.tearDown()
        self.credentials = {'username':self.username,'password':self.password }
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

    # def test_validate_api(self):
    #     resp1 = self.client.get(reverse("validate-api"))
    #     self.assertTrue(resp1.status_code,403)
    #     self.client.login(username=self.username,password=self.password)
    #     resp2 = self.client.get(reverse("validate-api")) 
    #     self.assertTrue(resp2.status_code,200)

    #     resp3 = self.client.post(reverse("validate-api"),{"file":self.tv_file},format="multipart")
    #     self.assertEqual(resp3.status_code,201)
    #     self.assertEqual(resp3.data["result"],"This SPDX Document is valid.")
    #     resp4 = self.client.post(reverse("validate-api"),{"file":self.rdf_file},format="multipart")
    #     self.assertEqual(resp4.status_code,201)
    #     self.assertEqual(resp4.data["result"],"This SPDX Document is valid.")
    #     resp5 = self.client.post(reverse("validate-api"),{"file":self.invalid_tv_file},format="multipart")
    #     self.assertEqual(resp5.status_code,400)
    #     self.assertNotEqual(resp5.data["result"],"This SPDX Document is valid.")
    #     resp6 = self.client.post(reverse("validate-api"),{"file":self.invalid_rdf_file},format="multipart")
    #     self.assertEqual(resp6.status_code,400)
    #     self.assertNotEqual(resp6.data["result"],"This SPDX Document is valid.")
    #     self.client.logout()
    #     self.tearDown()

        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # self.assertIn('created', response.data)
        # self.assertTrue(urlparse(response.data['file']).path.startswith(settings.MEDIA_URL))
        # self.assertEqual(response.data['owner'],
        #                User.objects.get_by_natural_key('test').id)
        # self.assertIn('created', response.data)

        # # assert unauthenticated user can not upload file
        # client.logout()
        # response = client.post(url, data, format='multipart')
        # self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class ConvertFileUploadTests(APITestCase):
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
        print("eher")
        ConvertFileUpload.objects.all().delete()

    def test_convert_api(self):
        resp1 = self.client.get(reverse("convert-api"))
        self.assertTrue(resp1.status_code,403)
        self.client.login(username=self.username,password=self.password)
        resp2 = self.client.get(reverse("convert-api"))
        self.assertTrue(resp2.status_code,200)
        self.client.logout()

    def test_convert_tagtordf_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.tv_file,"from_format":self.tag,"to_format":self.rdf,"cfilename":"tagtordf-apitest"},format="multipart")
        self.assertEqual(resp.status_code,406 or 201)
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.client.logout()

    def test_convert_tagtoxlsx_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.tv_file,"from_format":self.tag,"to_format":self.xlsx,"cfilename":"tagtoxlsx-apitest"},format="multipart")
        self.assertEqual(resp.status_code,406 or 201)
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.client.logout()

    def test_convert_rdftotag_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.rdf_file,"from_format":self.rdf,"to_format":self.tag,"cfilename":"rdftotag-apitest"},format="multipart")
        self.assertEqual(resp.status_code,406 or 201)
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.client.logout()

    def test_convert_rdftoxlsx_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.rdf_file,"from_format":self.rdf,"to_format":self.xlsx,"cfilename":"rdftoxlsx-apitest"},format="multipart")
        self.assertEqual(resp.status_code,406 or 201)
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.client.logout()

    # def test_convert_rdftohtml_api(self):
    #     self.client.login(username=self.username,password=self.password)
    #     resp = self.client.post(reverse("convert-api"),{"file":self.rdf_file,"from_format":self.rdf,"to_format":self.html,"cfilename":"rdftohtml-apitest"},format="multipart")
    #     self.assertEqual(resp.status_code,406 or 201)
    #     self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
    #     self.client.logout()

    def test_convert_xlsxtordf_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"from_format":self.xlsx,"to_format":self.rdf,"cfilename":"xlsxtordf-apitest"},format="multipart")
        self.assertEqual(resp.status_code,406 or 201)
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.client.logout()

    def test_convert_xlsxtotag_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"from_format":self.xlsx,"to_format":self.tag,"cfilename":"xlsxtotag-apitest"},format="multipart")
        self.assertEqual(resp.status_code,406 or 201)
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.client.logout()

class CompareFileUploadTests(APITestCase):
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
        resp1 = self.client.get(reverse("compare-api"))
        self.assertTrue(resp1.status_code,403)
        self.client.login(username=self.username,password=self.password)
        resp2 = self.client.get(reverse("compare-api"))
        self.assertTrue(resp2.status_code,200)

        resp3 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"file2":self.rdf_file2,"rfilename":"compare-apitest.xlsx"},format="multipart")
        self.assertEqual(resp3.status_code,201 or 406)
        resp4 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"file2":self.tv_file,"rfilename":"compare-apitest.xlsx"},format="multipart")
        self.assertEqual(resp4.status_code,400)

        self.client.logout()
        self.tearDown()
        #self.assertTrue(urlparse(response.data['result']).path.startswith(settings.MEDIA_URL))