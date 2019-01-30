# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

import jpype
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import time

from app.models import UserID
from app.models import LicenseRequest
from app.views import generateLicenseXml


class IndexViewsTestCase(TestCase):

    def test_index(self):
        """GET Request for index"""
        resp = self.client.get(reverse("index"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/index.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"index")

class AboutViewsTestCase(TestCase):

    def test_about(self):
        """GET Request for about"""
        resp = self.client.get(reverse("about"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/about.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"about")

class LoginViewsTestCase(TestCase):

    def initialise(self):
        """ Create users"""
        self.credentials = {'username':'testuser','password':'testpass' }
        user = User.objects.create_user(**self.credentials)
        user.is_staff = True
        user.is_active = True
        user.save()
        self.credentials2 = {'username':'testuser2','password':'testpass2' }
        user2 = User.objects.create_user(**self.credentials2)
        user2.is_staff = False
        user2.is_active = True
        user2.save()
        self.credentials3 = {'username':'testuser3','password':'testpass3' }
        user3 = User.objects.create_user(**self.credentials3)
        user3.is_staff = True
        user3.is_active = False
        user3.save()

    def test_login(self):
        """GET Request for login"""
        resp = self.client.get(reverse("login"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/login.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"loginuser")

    def test_postlogin(self):
        """POST Request for index with different user types."""
        self.initialise()
        resp = self.client.post(reverse("login"),self.credentials,follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.LOGIN_REDIRECT_URL, (i[0] for i in resp.redirect_chain))
        self.assertTrue(resp.context['user'].is_active)
        self.assertTrue(resp.context['user'].is_staff)
        self.assertFalse(resp.context['user'].is_superuser)
        self.client.get(reverse("logout"))

        resp2 = self.client.post(reverse("login"),self.credentials2,follow=True,secure=True)
        self.assertEqual(resp2.status_code,403)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertFalse(resp2.context['user'].is_active)
        self.assertFalse(resp2.context['user'].is_staff)
        self.assertFalse(resp2.context['user'].is_superuser)
        self.assertTrue('invalid' in resp2.context)
        self.assertIn("app/login.html",(i.name for i in resp2.templates))
        self.client.get(reverse("logout"))

        resp3 = self.client.post(reverse("login"),self.credentials3,follow=True,secure=True)
        self.assertEqual(resp3.status_code,403)
        self.assertEqual(resp3.redirect_chain,[])
        self.assertFalse(resp3.context['user'].is_active)
        self.assertFalse(resp3.context['user'].is_staff)
        self.assertFalse(resp3.context['user'].is_superuser)
        self.assertTrue('invalid' in resp3.context)
        self.assertIn("app/login.html",(i.name for i in resp3.templates))
        self.client.get(reverse("logout"))

class RegisterViewsTestCase(TestCase):

    def initialise(self):
        self.username = "testuser4"
        self.password ="testpass4"
        self.data = {"first_name": "test","last_name" : "test" ,
            "email" : "test@spdx.org","username":self.username,
            "password":self.password,"confirm_password":self.password,"organisation":"spdx"}

    def test_register(self):
        """GET Request for register"""
        resp = self.client.get(reverse("register"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertTrue('user_form' in resp.context)
        self.assertTrue('profile_form' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/register.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"register")

    def test_formregister(self):
        """POST Request for register"""
        self.initialise()
        resp = self.client.post(reverse("register"),self.data,follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.REGISTER_REDIRECT_UTL, (i[0] for i in resp.redirect_chain))

        loginresp = self.client.post(reverse("login"),{'username':self.username,'password':self.password},follow=True,secure=True)
        self.assertEqual(loginresp.status_code,200)
        self.assertTrue(loginresp.context['user'].is_active)
        self.assertTrue(loginresp.context['user'].is_staff)
        self.assertFalse(loginresp.context['user'].is_superuser)
        self.assertIn(settings.LOGIN_REDIRECT_URL, (i[0] for i in loginresp.redirect_chain))
        self.client.get(reverse("logout"))

class ValidateViewsTestCase(TestCase):

    def test_validate(self):
        """GET Request for validate"""
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            resp = self.client.get(reverse("validate"),follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code,200)

        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        resp2 = self.client.get(reverse("validate"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertIn("app/validate.html",(i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__,"validate")
        self.client.logout()

    def test_validate_post_without_login(self):
        """POST Request for validate without login or ANONYMOUS_LOGIN_DISABLED """
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
            resp = self.client.post(reverse("validate"),{'file' : self.tv_file},follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.tv_file.close()
            self.assertEqual(resp.status_code,200)

    def test_validate_post_without_file(self):
        """POST Request for validate without file upload"""
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        resp = self.client.post(reverse("validate"),{},follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.client.logout()

    def test_upload_tv(self):
        """POST Request for validate validating tag value files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        resp = self.client.post(reverse("validate"),{'file' : self.tv_file},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.content,"This SPDX Document is valid.")
        self.client.logout()

    def test_upload_rdf(self):
        """POST Request for validate validating rdf files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        resp = self.client.post(reverse("validate"),{'file' : self.rdf_file},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.content,"This SPDX Document is valid.")
        self.rdf_file.close()
        self.client.logout()

    def test_upload_other(self):
        """POST Request for validate validating other files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.other_file = open("examples/Other.txt")
        resp = self.client.post(reverse("validate"),{'file' : self.other_file},follow=True,secure=True)
        self.assertTrue(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.other_file.close()
        self.client.logout()

    def test_upload_inv_tv(self):
        """POST Request for validate validating tag value files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.invalid_tv_file = open("examples/SPDXTagExample-v2.0_invalid.spdx")
        resp = self.client.post(reverse("validate"),{'file' : self.invalid_tv_file},follow=True)
        self.assertTrue(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.invalid_tv_file.close()
        self.client.logout()

    def test_upload_inv_rdf(self):
        """POST Request for validate validating rdf files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.invalid_rdf_file = open("examples/SPDXRdfExample-v2.0_invalid.rdf")
        resp = self.client.post(reverse("validate"),{'file' : self.invalid_rdf_file},follow=True)
        self.assertTrue(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.client.logout()


class CompareViewsTestCase(TestCase):

    def initialise(self):
        """ Open files"""
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        self.rdf_file2 = open("examples/SPDXRdfExample.rdf")
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")

    def exit(self):
        """ Close files"""
        self.rdf_file.close()
        self.rdf_file2.close()
        self.tv_file.close()

    def test_compare(self):
        """GET Request for compare"""
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            resp = self.client.get(reverse("compare"),follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code,200)
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp2 = self.client.get(reverse("compare"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertIn("app/compare.html",(i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__,"compare")
        self.client.logout()

    def test_compare_post_without_login(self):
        """POST Request for compare without login or ANONYMOUS_LOGIN_ENABLED==False """
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            self.initialise()
            resp = self.client.post(reverse("compare"),{'rfilename': "comparetest", 'files' : [self.rdf_file,self.rdf_file2]},follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code,200)
            self.exit()

    def test_compare_post_without_file(self):
        """POST Request for compare without file upload"""
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"),{'rfilename': "comparetest"},follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.exit()
        self.client.logout()

    def test_compare_post_with_one_file(self):
        """POST Request for compare with only one file"""
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"),{'rfilename': "comparetest", 'files':[self.rdf_file,]},follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.exit()
        self.client.logout()

    def test_compare_two_rdf(self):
        """POST Request for comparing two rdf files"""
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"),{'rfilename': 'comparetest','files': [self.rdf_file,self.rdf_file2]},follow=True,secure=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/vnd.ms-excel")
        self.exit()
        self.client.logout()

    def test_compare_invalid_rdf(self):
        """POST Request for comparing two files"""
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"),{'rfilename': 'comparetest','files' : [self.rdf_file,self.tv_file]},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.exit()
        self.client.logout()


class ConvertViewsTestCase(TestCase):

    def test_convert(self):
        """GET Request for convert"""
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            resp = self.client.get(reverse("convert"),follow=True,secure=True)
            self.assertEqual(resp.status_code,200)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        resp2 = self.client.get(reverse("convert"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertIn("app/convert.html",(i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__,"convert")
        self.client.logout()

    def test_convert_tagtordf(self):
        """POST Request for convert tag to rdf"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        resp = self.client.post(reverse("convert"),{'cfilename': "tagtest" ,'cfileformat': ".rdf",'from_format' : "Tag", 'to_format' : "RDF", 'tagToRdfFormat': "TURTLE",'file' : self.tv_file},follow=True,secure=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/rdf+xml")
        self.tv_file.close()
        self.client.logout()

    def test_convert_tagtoxlsx(self):
        """POST Request for convert tag to spreadsheet"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        resp = self.client.post(reverse("convert"),{'cfilename': "tagtest" ,'cfileformat': ".xlsx",'from_format' : "Tag", 'to_format' : "Spreadsheet", 'file' : self.tv_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/vnd.ms-excel")
        self.tv_file.close()
        self.client.logout()

    def test_convert_rdftotag(self):
        """POST Request for convert rdf to tag"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".spdx",'from_format' : "RDF", 'to_format' : "Tag", 'file' : self.rdf_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"text/tag-value")
        self.rdf_file.close()
        self.client.logout()

    def test_convert_rdftoxlsx(self):
        """POST Request for convert rdf to spreadsheet"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".xlsx",'from_format' : "RDF", 'to_format' : "Spreadsheet", 'file' : self.rdf_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/vnd.ms-excel")
        self.rdf_file.close()
        self.client.logout()

    # def test_convert_rdftohtml(self):
    #     """POST Request for convert rdf to html"""
    #     self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
    #     self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
    #     resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".html",'from_format' : "RDF", 'to_format' : "Html", 'file' : self.rdf_file},follow=True)
    #     self.assertEqual(resp.status_code,200)
    #     self.assertNotEqual(resp.redirect_chain,[])
    #     self.rdf_file.close()
    #     self.client.logout()

    def test_convert_xlsxtotag(self):
        """POST Request for convert spreadsheet to tag"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.xls_file = open("examples/SPDXSpreadsheetExample-2.0.xls")
        resp = self.client.post(reverse("convert"),{'cfilename': "xlsxtest" ,'cfileformat': ".spdx",'from_format' : "Spreadsheet", 'to_format' : "Tag", 'file' : self.xls_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"text/tag-value")
        self.xls_file.close()
        self.client.logout()

    def test_convert_xlsxtordf(self):
        """POST Request for convert spreadsheet to rdf"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.xls_file = open("examples/SPDXSpreadsheetExample-2.0.xls")
        resp = self.client.post(reverse("convert"),{'cfilename': "xlsxtest" ,'cfileformat': ".rdf",'from_format' : "Spreadsheet", 'to_format' : "RDF", 'file' : self.xls_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/rdf+xml")
        self.xls_file.close()
        self.client.logout()

    def test_other_convert_formats(self):
        """POST Request for converting invalid formats"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.xls_file = open("examples/SPDXSpreadsheetExample-2.0.xls")
        resp = self.client.post(reverse("convert"),{'cfilename': "xlsxtest" ,'cfileformat': ".html",'from_format' : "Spreadsheet", 'to_format' : "HTML", 'file' : self.xls_file},follow=True)
        self.assertEqual(resp.status_code,400)
        self.assertIn("error", resp.context)
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".pdf",'from_format' : "RDF", 'to_format' : "PDF", 'file' : self.rdf_file},follow=True)
        self.assertEqual(resp.status_code,400)
        self.assertIn("error", resp.context)
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        resp = self.client.post(reverse("convert"),{'cfilename': "tagtest" ,'cfileformat': ".txt",'from_format' : "Tag", 'to_format' : "text", 'file' : self.tv_file},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertIn("error", resp.context)
        self.client.logout()


class CheckLicenseViewsTestCase(TestCase):

    def setUp(self):
        self.licensefile = open("examples/AFL-1.1.txt")
        self.licensetext = self.licensefile.read()

    def test_check_license(self):
        """GET Request for check license"""
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            resp = self.client.get(reverse("check-license"),follow=True,secure=True)
            self.assertEqual(resp.status_code,200)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.client.force_login(User.objects.get_or_create(username='checklicensetestuser')[0])
        resp2 = self.client.get(reverse("check-license"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertIn("app/check_license.html",(i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__,"check_license")
        self.client.logout()

    # def test_post_check_license(self):
    #     self.client.force_login(User.objects.get_or_create(username='checklicensetestuser')[0])
    #     resp = self.client.post(reverse("check-license"),{'licensetext': self.licensetext},follow=True)
    #     self.assertEqual(resp.status_code,200)
    #     self.assertIn("success",resp.context)
    #     self.client.logout()


class XMLUploadTestCase(TestCase):

    def test_xml_upload(self):
        """GET Request for XML upload page"""
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            resp = self.client.get(reverse("xml-upload"),follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code,200)

        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.get(reverse("xml-upload"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/xml_upload.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"xml_upload")
        self.client.logout()

    def test_xml_file_upload_post_without_login(self):
        """POST Request for XML file upload without login or ANONYMOUS_LOGIN_DISABLED """
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            self.xml_file = open("examples/Adobe-Glyph.xml")
            resp = self.client.post(reverse("xml-upload"),{'file': self.xml_file, 'uploadButton': 'uploadButton', 'page_id': 'asfw2432'},follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.xml_file.close()
            self.assertEqual(resp.status_code,200)

    def test_xml_file_upload_post_without_file(self):
        """POST Request for XML file upload without any file"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.post(reverse("xml-upload"),{'uploadButton': 'uploadButton', 'page_id': 'afaw214a'},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        resp = self.client.post(reverse("xml-upload"),{'uploadButton': 'uploadButton', 'page_id': 'afaw214a',"file": ""},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.client.logout()

    def test_xml_file_upload(self):
        """POST request for XML file upload"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        self.xml_file = open("examples/Adobe-Glyph.xml")
        resp = self.client.post(reverse("xml-upload"),{'file': self.xml_file, 'uploadButton': 'uploadButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.xml_file.close()
        self.client.logout()

    def test_invalid_file_upload(self):
        """ POST request for uploading non XML file"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        resp = self.client.post(reverse("xml-upload"),{'file': self.tv_file, 'uploadButton': 'uploadButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.tv_file.close()
        self.client.logout()

    def test_xml_input_textarea(self):
        """ POST request for xml input using textarea"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        self.xml_text = "<spdx></spdx>"
        resp = self.client.post(reverse("xml-upload"),{'xmltext': self.xml_text, 'xmlTextButton': 'xmlTextButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.client.logout()

    def test_xml_blank_input_textarea(self):
        """ POST request for blank xml input using textarea"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        self.xml_text = ""
        resp = self.client.post(reverse("xml-upload"),{'xmltext': self.xml_text, 'xmlTextButton': 'xmlTextButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertTrue('error' in resp.context)
        self.client.logout()

    def test_license_name(self):
        """ POST request for xml input using license identifier"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.post(reverse("xml-upload"),{'licenseName': 'Apache-2.0', 'licenseNameButton': 'licenseNameButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        """ POST request for xml input using license name"""
        resp = self.client.post(reverse("xml-upload"),{'licenseName': 'Apache License 2.0', 'licenseNameButton': 'licenseNameButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.client.logout()

    def test_exception_name(self):
        """ POST request for xml input using license exception identifier"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.post(reverse("xml-upload"),{'licenseName': '389-exception', 'licenseNameButton': 'licenseNameButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        """ POST request for xml input using license name"""
        resp = self.client.post(reverse("xml-upload"),{'licenseName': '389 Directory Server Exception', 'licenseNameButton': 'licenseNameButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.client.logout()

    def test_invalid_license_name(self):
        """ POST request for xml input using invalid license name"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.post(reverse("xml-upload"),{'licenseName': 'sampleTestLicense', 'licenseNameButton': 'licenseNameButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertTrue('error' in resp.context)
        self.client.logout()

    def test_blank_license_name(self):
        """ POST request for xml input using invalid license name"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.post(reverse("xml-upload"),{'licenseName': '', 'licenseNameButton': 'licenseNameButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.client.logout()

    def test_xml_new_file(self):
        """ POST request for making new XML license"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        resp = self.client.post(reverse("xml-upload"),{'newButton': 'newButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.client.logout()


class ValidateXMLViewsTestCase(TestCase):

    def test_validate_xml(self):
        """GET Request for validate_xml"""
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            resp = self.client.get(reverse("validate-xml"),follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code,200)

        self.client.force_login(User.objects.get_or_create(username='validateXMLtestuser')[0])
        resp2 = self.client.get(reverse("validate-xml"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertNotEqual(resp2.redirect_chain,[])
        self.assertIn(settings.HOME_URL, (i[0] for i in resp2.redirect_chain))
        self.assertEqual(resp2.resolver_match.func.__name__,"index")
        self.client.logout()

    def test_validate_xml_post_without_login(self):
        """POST Request for validate xml without login or ANONYMOUS_LOGIN_DISABLED """
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            self.xml_text = open("examples/Adobe-Glyph.xml").read()
            resp = self.client.post(reverse("validate-xml"),{'xmlText' : self.xml_text},follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code,200)

    def test_validate_xml_post_without_xmlText(self):
        """POST Request for validate xml without any xml text"""
        self.client.force_login(User.objects.get_or_create(username='validateXMLtestuser')[0])
        resp = self.client.post(reverse("validate-xml"),{},follow=True,secure=True)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, "No XML text given.")
        self.assertEqual(resp.redirect_chain,[])
        self.client.logout()

    def test_valid_xml(self):
        """POST Request for validating a valid XML text """
        self.client.force_login(User.objects.get_or_create(username='validateXMLtestuser')[0])
        self.xml_text = open("examples/Adobe-Glyph.xml").read()
        resp = self.client.post(reverse("validate-xml"),{'xmlText': self.xml_text},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.content,"This XML is valid against SPDX License Schema.")
        self.client.logout()

    def test_invalid_xml(self):
        """POST Request for validating an invalid XML text """
        self.client.force_login(User.objects.get_or_create(username='validateXMLtestuser')[0])
        self.xml_text = open("examples/invalid_license.xml").read()
        resp = self.client.post(reverse("validate-xml"),{'xmlText' : self.xml_text},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.client.logout()


class XMLEditorTestCase(StaticLiveServerTestCase):

    def setUp(self):
        options = Options()
        options.add_argument('-headless')
        self.selenium = webdriver.Firefox(firefox_options=options)
        self.initialXML = '<?xml version="1.0" encoding="UTF-8"?><SPDXLicenseCollection xmlns="http://www.spdx.org/license"><license></license></SPDXLicenseCollection>'
        self.invalidXML = '<?xml version="1.0" encoding="UTF-8"?><SPDXLicenseCollection xmlns="http://www.spdx.org/license"><license></license>'
        super(XMLEditorTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(XMLEditorTestCase, self).tearDown()

    def test_tree_editor_attributes(self):
        """ Test for adding, editing and deleting attributes using tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_link_text('New License XML').click()
        driver.find_element_by_id("new-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabTreeEditor").click()
        """ Adding attribute """
        driver.find_element_by_xpath("/html/body/div[2]/div/div[2]/div/ul/li/ul/li[3]/img[3]").click()
        driver.find_element_by_class_name("newAttributeName").send_keys("firstAttribute")
        driver.find_element_by_class_name("newAttributeValue").send_keys("firstValue")
        driver.find_element_by_class_name("addNewAttribute").click()
        """ Adding Invalid attribute """
        driver.find_element_by_xpath("/html/body/div[2]/div/div[2]/div/ul/li/ul/li[3]/img[3]").click()
        driver.find_element_by_class_name("newAttributeName").send_keys("secondAttribute")
        driver.find_element_by_class_name("addNewAttribute").click()
        modal_text = driver.find_element_by_id("modal-body").text
        self.assertEquals(modal_text, "Please enter valid attribute name and value")
        driver.find_element_by_css_selector("div.modal-footer button.btn").click()
        time.sleep(0.5)
        driver.find_element_by_class_name("newAttributeValue").send_keys("secondValue")
        driver.find_element_by_class_name("cancel").click()
        """ Editing attribute """
        driver.find_elements_by_css_selector("span.attributeValue")[1].click()
        driver.find_element_by_css_selector("input.textbox").clear()
        driver.find_element_by_css_selector("input.textbox").send_keys("Edited Value")
        driver.find_element_by_css_selector("img.editAttribute").click()
        editedValue = driver.find_elements_by_css_selector("span.attributeValue")[1].text
        self.assertEquals(editedValue, "Edited Value")
        """ Delete attribute """
        driver.find_elements_by_css_selector("span.attributeValue")[1].click()
        driver.find_element_by_css_selector("img.removeAttribute").click()
        modal_text = driver.find_element_by_id("modal-body").text
        self.assertEquals(modal_text, "Are you sure you want to delete this attribute? This action cannot be undone.")
        driver.find_element_by_id("modalOk").click()
        time.sleep(0.5)
        driver.find_element_by_id("tabTextEditor").click()
        codemirror = driver.find_elements_by_css_selector("pre.CodeMirror-line")
        time.sleep(0.2)
        finalXML = ""
        for i in codemirror:
            finalXML += i.text.strip()
        self.assertEquals(self.initialXML, finalXML)

    def test_tree_editor_nodes(self):
        """ Test for adding and deleting nodes(tags) using tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_link_text('New License XML').click()
        driver.find_element_by_id("new-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabTreeEditor").click()
        """ Adding node """
        driver.find_element_by_css_selector("li.addChild.last").click()
        driver.find_element_by_css_selector("input.textbox").send_keys("newNode")
        driver.find_element_by_class_name("buttonAddChild").click()
        """ Adding invalid node """
        driver.find_element_by_css_selector("li.addChild.last").click()
        driver.find_element_by_class_name("buttonAddChild").click()
        modal_text = driver.find_element_by_id("modal-body").text
        self.assertEquals(modal_text, "The tag name cannot be empty. Please enter a valid tag name.")
        driver.find_element_by_css_selector("div.modal-footer button.btn").click()
        time.sleep(0.5)
        driver.find_element_by_class_name("cancelAddChild").click()
        """ Delete attribute """
        driver.find_elements_by_css_selector("img.deleteNode")[2].click()
        modal_text = driver.find_element_by_id("modal-body").text
        self.assertEquals(modal_text, "Are you sure you want to delete this tag? This cannot be undone.")
        driver.find_element_by_id("modalOk").click()
        time.sleep(0.5)
        driver.find_element_by_id("tabTextEditor").click()
        codemirror = driver.find_elements_by_css_selector("pre.CodeMirror-line")
        finalXML = ""
        for i in codemirror:
            finalXML += i.text.strip()
        self.assertEquals(self.initialXML, finalXML)

    def test_tree_editor_text(self):
        """ Test for adding, editing and deleting text inside tags using tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_link_text('New License XML').click()
        driver.find_element_by_id("new-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabTreeEditor").click()
        """ Adding text """
        driver.find_element_by_css_selector("li.emptyText").click()
        driver.find_element_by_css_selector("div.treeContainer textarea").send_keys("This is some sample text.")
        driver.find_element_by_class_name("editNodeText").click()
        nodeText = driver.find_element_by_css_selector("li.nodeText").text
        self.assertEquals(nodeText, "This is some sample text.")
        """ Editing text """
        driver.find_element_by_css_selector("li.nodeText").click()
        driver.find_element_by_css_selector("div.treeContainer textarea").clear()
        driver.find_element_by_css_selector("div.treeContainer textarea").send_keys("Edited text.")
        driver.find_element_by_class_name("editNodeText").click()
        nodeText = driver.find_element_by_css_selector("li.nodeText").text
        self.assertEquals(nodeText, "Edited text.")
        """ Delete text """
        driver.find_element_by_css_selector("li.nodeText").click()
        driver.find_element_by_css_selector("div.treeContainer textarea").clear()
        driver.find_element_by_class_name("editNodeText").click()
        nodeText = driver.find_element_by_css_selector("li.emptyText").text
        self.assertEquals(nodeText, "(No text value. Click to edit.)")
        driver.find_element_by_id("tabTextEditor").click()
        codemirror = driver.find_elements_by_css_selector("pre.CodeMirror-line")
        finalXML = ""
        for i in codemirror:
            finalXML += i.text.strip()
        self.assertEquals(self.initialXML, finalXML)

    def test_tree_editor_invalid_xml(self):
        """ Test for invalid XML text provided """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_id("xmltext").send_keys(self.invalidXML)
        driver.find_element_by_id("xmlTextButton").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabTreeEditor").click()
        """ Checking for error message """
        error_title = driver.find_element_by_css_selector("h2.xmlParsingErrorMessage").text
        error_message = driver.find_element_by_css_selector("span.xmlParsingErrorMessage").text
        self.assertEquals(error_title, "Invalid XML.")
        assert "XML Parsing Error" in error_message


class PullRequestTestCase(TestCase):

    def test_pull_request_get_without_login(self):
        """GET request for pull request feature without login """
        resp = self.client.get(reverse("pull-request"),follow=True,secure=True)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.assertEqual(resp.status_code,200)

    def test_pull_request_get_with_login(self):
        """GET request for pull request feature with login"""
        self.client.force_login(User.objects.get_or_create(username='pullRequestTestUser')[0])
        resp = self.client.get(reverse("pull-request"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.HOME_URL, (i[0] for i in resp.redirect_chain))
        self.assertEqual(resp.resolver_match.func.__name__,"index")
        self.client.logout()

    def test_pull_request_post_with_login(self):
        """POST request for pull request feature with login"""
        self.client.force_login(User.objects.get_or_create(username='pullRequestTestUser')[0])
        resp = self.client.post(reverse("pull-request"),{},follow=True,secure=True)
        self.assertEqual(resp.status_code,401)
        self.assertEqual(resp.redirect_chain,[])
        self.assertEqual(resp.content, "Please login using GitHub to use this feature.")
        self.client.logout()


class LogoutViewsTestCase(TestCase):

    def test_logout(self):
        self.client.force_login(User.objects.get_or_create(username='logouttestuser')[0])
        resp = self.client.get(reverse("logout"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))


class RootViewsTestCase(TestCase):

    def test_root_url(self):
        resp = self.client.get(reverse("root"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn(settings.HOME_URL, (i[0] for i in resp.redirect_chain))


class ProfileViewsTestCase(TestCase):

    def initialise(self):
        self.username = "profiletestuser"
        self.password ="profiletestpass"
        self.credentials = {"first_name": "test","last_name" : "test" ,"email" : "profiletest@spdx.org",'username':self.username,'password':self.password }
        self.user = User.objects.create_user(**self.credentials)
        UserID.objects.get_or_create({"user":self.user,"organisation":"spdx"})

    def test_profile(self):
        """GET Request for profile"""
        resp = self.client.get(reverse("profile"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='profiletestuser')[0])

        resp2 = self.client.get(reverse("profile"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertIn("app/profile.html",(i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__,"profile")
        self.assertIn("form",resp2.context)
        self.assertIn("info_form",resp2.context)
        self.assertIn("orginfo_form",resp2.context)
        self.client.logout()

    def test_saveinfo(self):
        """POST Request for saving information"""
        self.initialise()
        user = User.objects.get_or_create(username='profiletestuser')[0]
        userid = UserID.objects.get_or_create(user=user)[0]
        self.assertEqual(user.first_name,"test")
        self.assertEqual(user.last_name,"test")
        self.assertEqual(user.email,"profiletest@spdx.org")
        self.assertEqual(userid.organisation,"spdx")
        self.client.force_login(user)

        save_info_resp = self.client.post(reverse("profile"),{'saveinfo':'saveinfo',"first_name": "john","last_name" : "doe" ,"email" : "johndoe@spdx.org","organisation":"Software Package Data Exchange"},follow=True,secure=True)
        self.assertEqual(save_info_resp.status_code,200)
        self.assertEqual(save_info_resp.redirect_chain,[])
        self.assertEqual(save_info_resp.context["success"],"Details Successfully Updated")
        user = User.objects.get_or_create(username='profiletestuser')[0]
        userid = UserID.objects.get_or_create(user=user)[0]
        self.assertEqual(user.first_name,"john")
        self.assertEqual(user.last_name,"doe")
        self.assertEqual(user.email,"johndoe@spdx.org")
        self.assertEqual(userid.organisation,"Software Package Data Exchange")
        self.client.logout()

    def test_changepwd(self):
        """POST Request for changing password"""
        self.initialise()
        resp = self.client.login(username='profiletestuser', password='profiletestpass')
        self.assertTrue(resp)
        change_pwd_resp = self.client.post(reverse("profile"),{'changepwd':'changepwd',"old_password": self.password,"new_password1" : "johndoepass" ,"new_password2" : "johndoepass"},follow=True,secure=True)
        self.assertEqual(change_pwd_resp.status_code,200)
        self.assertEqual(change_pwd_resp.redirect_chain,[])
        self.assertEqual(change_pwd_resp.context["success"],"Your password was successfully updated!")
        self.client.logout()

        resp2 = self.client.login(username='profiletestuser', password='profiletestpass')
        self.assertFalse(resp2)

        resp3 = self.client.login(username='profiletestuser', password='johndoepass')
        self.assertTrue(resp3)
        self.client.logout()


class CheckUserNameTestCase(TestCase):

    def initialise(self):
        self.username = "checktestuser"
        self.password ="checktestpass"
        self.credentials = {'username':self.username,'password':self.password }
        User.objects.create_user(**self.credentials)

    def test_check_username(self):
        """POST Request for checking username"""
        resp = self.client.post(reverse("check-username"),{"username":"spdx"},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)

        resp2 = self.client.post(reverse("check-username"),{"randomkey":"randomvalue"},follow=True,secure=True)
        self.assertEqual(resp2.status_code,400)

        self.initialise()
        resp3 = self.client.post(reverse("check-username"),{"username":"checktestuser"},follow=True,secure=True)
        self.assertEqual(resp3.status_code,404)

class LicenseRequestsViewsTestCase(TestCase):

    def test_license_requests(self):
        """GET Request for license requests list"""
        resp = self.client.get(reverse("license-requests"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/license_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseRequests")

class SubmitNewLicenseViewsTestCase(TestCase):

    def initialise(self):
        self.fullname = "BSD Zero Clause License"
        self.shortIdentifier = "0BSD"
        self.sourceUrl = "http://landley.net/toybox/license.html"
        self.urls = [self.sourceUrl]
        self.osiApproved = "no"
        self.notes = ""
        self.licenseHeader = ""
        self.text ='<text> <copyrightText> <p>Copyright (C) 2006 by Rob Landley &lt;rob@landley.net&gt;</p> </copyrightText> <p>Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.</p> <p>THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.</p> </text>'
        self.userEmail = "test@mail.com"
        self.licenseAuthorName = "Test Author Name"
        self.xml = '<SPDXLicenseCollection xmlns="http://www.spdx.org/license"> <license isOsiApproved="false" licenseId="0BSD" name="BSD Zero Clause License"> <crossRefs> <crossRef> http://landley.net/toybox/license.html</crossRef> </crossRefs> <standardLicenseHeader /> <notes /> <text> <p> &lt;text&gt; &lt;copyrightText&gt; &lt;p&gt;Copyright (C) 2006 by Rob Landley &amp;lt;rob@landley.net&amp;gt;&lt;/p&gt; &lt;/copyrightText&gt; &lt;p&gt;Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.&lt;/p&gt; &lt;p&gt;THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.&lt;/p&gt; &lt;/text&gt;</p> </text> </license> </SPDXLicenseCollection> '
        self.data = {"fullname": self.fullname, "shortIdentifier": self.shortIdentifier,
                    "sourceUrl": self.sourceUrl,'osiApproved': self.osiApproved, 'notes': self.notes,
                    "licenseHeader": self.licenseHeader, "text": self.text, "userEmail": self.userEmail,
                    "licenseAuthorName": self.licenseAuthorName }

    def test_submit_new_license(self):
        """GET Request for submit a new license"""
        resp = self.client.get(reverse("submit-new-license"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/submit_new_license.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"submitNewLicense")
        self.assertIn("form",resp.context)
        if "form" in resp.context:
            self.assertIn("fullname",resp.context["form"].fields)
            self.assertIn("shortIdentifier",resp.context["form"].fields)
            self.assertIn("sourceUrl",resp.context["form"].fields)
            self.assertIn("osiApproved",resp.context["form"].fields)
            self.assertIn("notes",resp.context["form"].fields)
            self.assertIn("licenseHeader",resp.context["form"].fields)
            self.assertIn("text",resp.context["form"].fields)
            self.assertIn("userEmail",resp.context["form"].fields)
            self.assertIn("licenseAuthorName",resp.context["form"].fields)

    def test_post_submit(self):
        """POST Request for submit a new license"""
        self.initialise()
        resp = self.client.post(reverse("register"), self.data, follow=True, secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])

    def test_generate_xml(self):
        """View for generating an xml from license submittal form fields"""
        self.initialise()
        xml = generateLicenseXml(self.osiApproved, self.shortIdentifier, self.fullname, self.urls,
                                self.licenseHeader, self.notes, self.text).replace("\n"," ")
        self.assertEqual(self.xml, xml)
