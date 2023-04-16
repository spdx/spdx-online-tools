# -*- coding: utf-8 -*-


from django.test import TestCase
from unittest import skipIf
from unittest.mock import patch
from src.secret import getAccessToken, getGithubUserId, getGithubUserName
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
from webdriver_manager.firefox import GeckoDriverManager
import time

from app.models import UserID
from app.models import LicenseRequest, LicenseNamespace
from app.generateXml import generateLicenseXml
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from social_django.models import UserSocialAuth
from django.conf import settings
import os

def getExamplePath(filename):
    return os.path.join(settings.EXAMPLES_DIR, filename)


class TestUtil(TestCase):
    def gitHubLogin(self):
        TEST_LOGIN_INFO = {
        "provider": "github",
        "uid": str(getGithubUserId()),
        "access_token": getAccessToken(),
        "login": getGithubUserName(),
        "id": getGithubUserId(),
        "password": 'pass'
        }
        # login first
        self.user = User.objects.create(username=TEST_LOGIN_INFO["login"],
                                        is_active=True,
                                        is_superuser=True)
        self.user.set_password(TEST_LOGIN_INFO["password"])
        self.user.save()
        social_auth = UserSocialAuth.objects.create(provider=TEST_LOGIN_INFO["provider"],
        uid=TEST_LOGIN_INFO["uid"],
        extra_data=TEST_LOGIN_INFO,
        user=self.user)
        self.user = authenticate(username=TEST_LOGIN_INFO["login"],
                                 password=TEST_LOGIN_INFO["password"])
        login = self.client.login(username=TEST_LOGIN_INFO["login"],
                                  password=TEST_LOGIN_INFO["password"])
        return login

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
            self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"))
            resp = self.client.post(reverse("validate"),{'file' : self.tv_file, 'format' : 'TAG'},follow=True,secure=True)
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
        resp = self.client.post(reverse("validate"),{'file' : self.tv_file, 'format' : 'TAG'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.content,b"This SPDX Document is valid.")
        self.client.logout()

    def test_upload_rdf(self):
        """POST Request for validate validating rdf files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        resp = self.client.post(reverse("validate"),{'file' : self.rdf_file, 'format' : 'RDFXML'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.content,b"This SPDX Document is valid.")
        self.rdf_file.close()
        self.client.logout()

    def test_upload_other(self):
        """POST Request for validate validating other files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.other_file = open("examples/Other.txt")
        resp = self.client.post(reverse("validate"),{'file' : self.other_file, 'format' : 'TAG'},follow=True,secure=True)
        self.assertTrue(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.other_file.close()
        self.client.logout()

    def test_upload_inv_tv(self):
        """POST Request for validate validating tag value files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.invalid_tv_file = open("examples/SPDXTagExample-v2.0_invalid.spdx")
        resp = self.client.post(reverse("validate"),{'file' : self.invalid_tv_file, 'format' : 'TAG'},follow=True)
        self.assertTrue(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.invalid_tv_file.close()
        self.client.logout()

    def test_upload_inv_rdf(self):
        """POST Request for validate validating rdf files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.invalid_rdf_file = open("examples/SPDXRdfExample-v2.0_invalid.rdf")
        resp = self.client.post(reverse("validate"),{'file' : self.invalid_rdf_file, 'format' : 'RDFXML'},follow=True)
        self.assertTrue(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.client.logout()


class CompareViewsTestCase(TestCase):

    def initialise(self):
        """ Open files"""
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        self.rdf_file2 = open("examples/SPDXRdfExample.rdf")
        self.invalid_rdf = open("examples/SPDXRdfExample-v2.0_invalid.rdf")

    def exit(self):
        """ Close files"""
        self.rdf_file.close()
        self.rdf_file2.close()
        self.invalid_rdf.close()

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
        self.assertEqual(resp.status_code, 200)
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
        resp = self.client.post(reverse("compare"),{'rfilename': 'comparetest','files' : [self.rdf_file,self.invalid_rdf]},follow=True,secure=True)
        self.assertEqual(resp.status_code, 400)
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
        resp = self.client.post(reverse("convert"),{'cfilename': "tagtest" ,'cfileformat': ".rdf.xml",'from_format' : "TAG", 'to_format' : "RDFXML", 'file' : self.tv_file},follow=True,secure=True)
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
        resp = self.client.post(reverse("convert"),{'cfilename': "tagtest" ,'cfileformat': ".xlsx",'from_format' : "TAG", 'to_format' : "XLSX", 'file' : self.tv_file},follow=True)
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
        resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".spdx",'from_format' : "RDFXML", 'to_format' : "TAG", 'file' : self.rdf_file},follow=True)
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
        resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".xls",'from_format' : "RDFXML", 'to_format' : "XLS", 'file' : self.rdf_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/vnd.ms-excel")
        self.rdf_file.close()
        self.client.logout()

    def test_convert_xlsxtotag(self):
        """POST Request for convert spreadsheet to tag"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.xls_file = open("examples/SPDXSpreadsheetExample-2.0.xls", "rb")
        resp = self.client.post(reverse("convert"),{'cfilename': "xlsxtest" ,'cfileformat': ".spdx",'from_format' : "XLS", 'to_format' : "TAG", 'file' : self.xls_file},follow=True)
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
        self.xls_file = open("examples/SPDXSpreadsheetExample-2.0.xls", "rb")
        resp = self.client.post(reverse("convert"),{'cfilename': "xlsxtest" ,'cfileformat': ".rdf",'from_format' : "XLS", 'to_format' : "RDFXML", 'file' : self.xls_file},follow=True)
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
        self.xls_file = open(getExamplePath("SPDXSpreadsheetExample-2.0.xls"), "rb")
        resp = self.client.post(reverse("convert"),{'cfilename': "xlsxtest" ,'cfileformat': ".html",'from_format' : "Spreadsheet", 'to_format' : "HTML", 'file' : self.xls_file},follow=True)
        self.assertEqual(resp.status_code,400)
        self.assertIn("error", resp.context)
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.0.rdf"), "rb")
        resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".pdf",'from_format' : "RDF", 'to_format' : "PDF", 'file' : self.rdf_file},follow=True)
        self.assertEqual(resp.status_code,400)
        self.assertIn("error", resp.context)
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"), "rb")
        resp = self.client.post(reverse("convert"),{'cfilename': "tagtest" ,'cfileformat': ".txt",'from_format' : "Tag", 'to_format' : "text", 'file' : self.tv_file},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertIn("error", resp.context)
        self.client.logout()


class CheckLicenseViewsTestCase(TestCase):

    def setUp(self):
        self.licensefile = open(getExamplePath("AFL-1.1.txt"))
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
            self.xml_file = open(getExamplePath("Adobe-Glyph.xml"))
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
        self.xml_file = open(getExamplePath("Adobe-Glyph.xml"))
        resp = self.client.post(reverse("xml-upload"),{'file': self.xml_file, 'uploadButton': 'uploadButton', 'page_id': 'asfw2432'},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.xml_file.close()
        self.client.logout()

    def test_invalid_file_upload(self):
        """ POST request for uploading non XML file"""
        self.client.force_login(User.objects.get_or_create(username='xmltestuser')[0])
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"))
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
            self.xml_text = open(getExamplePath("Adobe-Glyph.xml")).read()
            resp = self.client.post(reverse("validate-xml"),{'xmlText' : self.xml_text},follow=True,secure=True)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code,200)

    def test_validate_xml_post_without_xmlText(self):
        """POST Request for validate xml without any xml text"""
        self.client.force_login(User.objects.get_or_create(username='validateXMLtestuser')[0])
        resp = self.client.post(reverse("validate-xml"),{},follow=True,secure=True)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b"No XML text given.")
        self.assertEqual(resp.redirect_chain,[])
        self.client.logout()

    def test_valid_xml(self):
        """POST Request for validating a valid XML text """
        self.client.force_login(User.objects.get_or_create(username='validateXMLtestuser')[0])
        self.xml_text = open(getExamplePath("Adobe-Glyph.xml")).read()
        resp = self.client.post(reverse("validate-xml"),{'xmlText': self.xml_text},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.content, b"This XML is valid against SPDX License Schema.")
        self.client.logout()

    def test_invalid_xml(self):
        """POST Request for validating an invalid XML text """
        self.client.force_login(User.objects.get_or_create(username='validateXMLtestuser')[0])
        self.xml_text = open(getExamplePath("invalid_license.xml")).read()
        resp = self.client.post(reverse("validate-xml"),{'xmlText' : self.xml_text},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.client.logout()


class LicenseXMLEditorTestCase(StaticLiveServerTestCase):

    def setUp(self):
        options = Options()
        options.add_argument('-headless')
        self.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_options=options)
        self.initialXML = '<?xml version="1.0" encoding="UTF-8"?><SPDXLicenseCollection xmlns="http://www.spdx.org/license"><license></license></SPDXLicenseCollection>'
        self.invalidXML = '<?xml version="1.0" encoding="UTF-8"?><SPDXLicenseCollection xmlns="http://www.spdx.org/license"><license></license>'
        super(LicenseXMLEditorTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(LicenseXMLEditorTestCase, self).tearDown()

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
        self.assertEqual(modal_text, "Please enter valid attribute name and value")
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
        self.assertEqual(editedValue, "Edited Value")
        """ Delete attribute """
        driver.find_elements_by_css_selector("span.attributeValue")[1].click()
        driver.find_element_by_css_selector("img.removeAttribute").click()
        modal_text = driver.find_element_by_id("modal-body").text
        self.assertEqual(modal_text, "Are you sure you want to delete this attribute? This action cannot be undone.")
        driver.find_element_by_id("modalOk").click()
        time.sleep(0.5)
        driver.find_element_by_id("tabTextEditor").click()
        codemirror = driver.find_elements_by_css_selector("pre.CodeMirror-line")
        time.sleep(0.2)
        finalXML = ""
        for i in codemirror:
            finalXML += i.text.strip()
        self.assertEqual(self.initialXML, finalXML)

    def test_split_tree_editor_attributes(self):
        """ Test for adding, editing and deleting attributes using split view tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to split view """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_link_text('New License XML').click()
        driver.find_element_by_id("new-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabSplitView").click()
        """ Adding attribute """
        driver.execute_script("document.getElementsByClassName('addAttribute')[1].click()")
        driver.execute_script("document.getElementsByClassName('newAttributeName')[0].value = 'firstAttribute'")
        driver.execute_script("document.getElementsByClassName('newAttributeValue')[0].value = 'firstValue'")
        driver.execute_script("document.getElementsByClassName('addNewAttribute')[0].click()")
        """ Adding Invalid attribute """
        driver.execute_script("document.getElementsByClassName('addAttribute')[1].click()")
        driver.execute_script("document.getElementsByClassName('newAttributeName')[0].value = 'secondAttribute'")
        driver.execute_script("document.getElementsByClassName('addNewAttribute')[0].click()")
        modal_text = driver.execute_script("return document.getElementById('modal-body').innerHTML")
        self.assertEqual(modal_text, "Please enter valid attribute name and value")
        driver.execute_script("document.querySelector('div.modal-footer button.btn').click()")
        time.sleep(0.5)
        driver.execute_script("document.getElementsByClassName('newAttributeValue')[0].value = 'secondValue'")
        driver.execute_script("document.getElementsByClassName('cancel')[0].click()")
        """ Editing attribute """
        driver.execute_script("document.querySelectorAll('span.attributeValue')[1].click()")
        driver.execute_script("document.querySelector('input.textbox').value = ''")
        driver.execute_script("document.querySelector('input.textbox').value = 'Edited Value'")
        driver.execute_script("document.querySelector('img.editAttribute').click()")
        editedValue = driver.find_elements_by_css_selector("span.attributeValue")[1].text
        self.assertEqual(editedValue, "Edited Value")
        """ Delete attribute """
        driver.execute_script("document.querySelectorAll('span.attributeValue')[1].click()")
        driver.execute_script("document.querySelector('img.removeAttribute').click()")
        modal_text = driver.execute_script("return document.getElementById('modal-body').innerHTML")
        self.assertEqual(modal_text, "Are you sure you want to delete this attribute? This action cannot be undone.")
        driver.execute_script("document.getElementById('modalOk').click()")
        time.sleep(0.5)
        driver.execute_script("document.getElementById('tabTextEditor').click()")
        finalXML = driver.execute_script("var xml = ''; var codemirror = document.querySelectorAll('pre.CodeMirror-line'); for (var i=1;i<(codemirror.length/2)-1;i++){xml = xml + codemirror[i].textContent.trim();} return xml;")
        time.sleep(0.2)
        self.assertEqual(self.initialXML, finalXML)

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
        self.assertEqual(modal_text, "The tag name cannot be empty. Please enter a valid tag name.")
        driver.find_element_by_css_selector("div.modal-footer button.btn").click()
        time.sleep(0.5)
        driver.find_element_by_class_name("cancelAddChild").click()
        """ Delete attribute """
        driver.find_elements_by_css_selector("img.deleteNode")[2].click()
        modal_text = driver.find_element_by_id("modal-body").text
        self.assertEqual(modal_text, "Are you sure you want to delete this tag? This cannot be undone.")
        driver.find_element_by_id("modalOk").click()
        time.sleep(0.5)
        driver.find_element_by_id("tabTextEditor").click()
        codemirror = driver.find_elements_by_css_selector("pre.CodeMirror-line")
        finalXML = ""
        for i in codemirror:
            finalXML += i.text.strip()
        self.assertEqual(self.initialXML, finalXML)

    def test_split_tree_editor_nodes(self):
        """ Test for adding and deleting nodes(tags) using split view tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to split view """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_link_text('New License XML').click()
        driver.find_element_by_id("new-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabSplitView").click()
        """ Adding node """
        driver.execute_script("document.querySelectorAll('li.addChild.last')[1].click()")
        driver.execute_script("document.querySelector('input.textbox').value = 'newNode'")
        driver.execute_script("document.getElementsByClassName('buttonAddChild')[0].click()")
        """ Adding invalid node """
        driver.execute_script("document.querySelectorAll('li.addChild.last')[1].click()")
        driver.execute_script("document.getElementsByClassName('buttonAddChild')[0].click()")
        modal_text = driver.execute_script("return document.getElementById('modal-body').innerHTML")
        self.assertEqual(modal_text, "The tag name cannot be empty. Please enter a valid tag name.")
        driver.execute_script("document.querySelector('div.modal-footer button.btn').click()")
        time.sleep(0.5)
        driver.execute_script("document.getElementsByClassName('cancelAddChild')[0].click()")
        """ Delete attribute """
        driver.execute_script("document.querySelectorAll('img.deleteNode')[2].click()")
        modal_text = driver.execute_script("return document.getElementById('modal-body').innerHTML")
        self.assertEqual(modal_text, "Are you sure you want to delete this tag? This cannot be undone.")
        driver.execute_script("document.getElementById('modalOk').click()")
        time.sleep(0.5)
        driver.execute_script("document.getElementById('tabTextEditor').click()")
        finalXML = driver.execute_script("var xml = ''; var codemirror = document.querySelectorAll('pre.CodeMirror-line'); for (var i=1;i<(codemirror.length/2)-1;i++){xml = xml + codemirror[i].textContent.trim();} return xml;")
        time.sleep(0.2)
        self.assertEqual(self.initialXML, finalXML)

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
        self.assertEqual(nodeText, "This is some sample text.")
        """ Editing text """
        driver.find_element_by_css_selector("li.nodeText").click()
        driver.find_element_by_css_selector("div.treeContainer textarea").clear()
        driver.find_element_by_css_selector("div.treeContainer textarea").send_keys("Edited text.")
        driver.find_element_by_class_name("editNodeText").click()
        nodeText = driver.find_element_by_css_selector("li.nodeText").text
        self.assertEqual(nodeText, "Edited text.")
        """ Delete text """
        driver.find_element_by_css_selector("li.nodeText").click()
        driver.find_element_by_css_selector("div.treeContainer textarea").clear()
        driver.find_element_by_class_name("editNodeText").click()
        nodeText = driver.find_element_by_css_selector("li.emptyText").text
        self.assertEqual(nodeText, "(No text value. Click to edit.)")
        driver.find_element_by_id("tabTextEditor").click()
        codemirror = driver.find_elements_by_css_selector("pre.CodeMirror-line")
        finalXML = ""
        for i in codemirror:
            finalXML += i.text.strip()
        self.assertEqual(self.initialXML, finalXML)

    def test_split_tree_editor_text(self):
        """ Test for adding, editing and deleting text inside tags using split view tree editor """
        driver = self.selenium
        """ Opening the editor and navigating to split view """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_link_text('New License XML').click()
        driver.find_element_by_id("new-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabSplitView").click()
        """ Adding text """
        driver.execute_script("document.querySelectorAll('li.emptyText')[1].click()")
        driver.execute_script("document.querySelectorAll('li.emptyText')[1].click()")
        driver.execute_script("document.querySelector('ul textarea').value = 'This is some sample text.'")
        driver.execute_script("document.getElementsByClassName('editNodeText')[0].click()")
        nodeText = driver.execute_script("return document.querySelector('li.nodeText').innerHTML")
        self.assertEqual(nodeText, "This is some sample text.")
        """ Editing text """
        driver.execute_script("document.querySelectorAll('li.nodeText')[0].click()")
        driver.execute_script("document.querySelector('ul textarea').value = ''")
        driver.execute_script("document.querySelector('ul textarea').value = 'Edited text.'")
        driver.execute_script("document.getElementsByClassName('editNodeText')[0].click()")
        nodeText = driver.execute_script("return document.querySelector('li.nodeText').innerHTML")
        self.assertEqual(nodeText, "Edited text.")
        """ Delete text """
        driver.execute_script("document.querySelectorAll('li.nodeText')[0].click()")
        driver.execute_script("document.querySelector('ul textarea').value = ''")
        driver.execute_script("document.getElementsByClassName('editNodeText')[0].click()")
        nodeText = driver.execute_script("return document.querySelector('li.emptyText').innerHTML")
        self.assertEqual(nodeText, "(No text value. Click to edit.)")
        driver.execute_script("document.getElementById('tabTextEditor').click()")
        finalXML = driver.execute_script("var xml = ''; var codemirror = document.querySelectorAll('pre.CodeMirror-line'); for (var i=1;i<(codemirror.length/2)-1;i++){xml = xml + codemirror[i].textContent.trim();} return xml;")
        time.sleep(0.2)
        self.assertEqual(self.initialXML, finalXML)

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
        self.assertEqual(error_title, "Invalid XML.")
        assert "XML Parsing Error" in error_message

    def test_split_tree_editor_invalid_xml(self):
        """ Test for invalid XML text provided """
        driver = self.selenium
        """ Opening the editor and navigating to tree editor """
        driver.get(self.live_server_url+'/app/xml_upload/')
        driver.find_element_by_id("xmltext").send_keys(self.invalidXML)
        driver.find_element_by_id("xmlTextButton").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        driver.find_element_by_id("tabSplitView").click()
        """ Checking for error message """
        error_title = driver.find_element_by_css_selector("h2.xmlParsingErrorMessage").text
        error_message = driver.find_element_by_css_selector("span.xmlParsingErrorMessage").text
        self.assertEqual(error_title, "Invalid XML.")
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
        self.assertEqual(resp.content, b"Please login using GitHub to use this feature.")
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


class ArchiveLicenseRequestsViewsTestCase(StaticLiveServerTestCase):

    def setUp(self):
        options = Options()
        options.add_argument('-headless')
        self.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_options=options)
        super(ArchiveLicenseRequestsViewsTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(ArchiveLicenseRequestsViewsTestCase, self).tearDown()

    def test_archive_license_requests(self):
        """GET Request for archive license requests list"""
        resp = self.client.get(reverse("archive-license-xml"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/archive_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"archiveRequests")

    def test_error_archive_license_requests(self):
        """Check if error page is displayed when the license id does not exist for archive license"""
        license_id = 0
        resp = self.client.get(reverse("archived-license-information", args=(license_id,)),follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("404.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseInformation")

    @skipIf(not getAccessToken() and not getGithubUserId() and not getGithubUserName(), "You need to set gihub parameters in the secret.py file for this test to be executed properly.")
    def test_archive_license_requests_feature(self):
        """Check if the license is shifted to archive requests when archive button is pressed"""
        login = TestUtil.gitHubLogin(self)
        self.assertTrue(login)
        cookie = self.client.cookies['sessionid']
        driver = self.selenium
        with patch('app.utils.checkPermission') as mock_checkPermission:
            mock_checkPermission.return_value = True
            driver.get(self.live_server_url+'/app/license_requests/')
            driver.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
            table_contents = driver.find_element_by_css_selector('tbody').text
            self.assertEqual(table_contents, "No data available in table")
            license_obj = LicenseRequest.objects.create(fullname="BSD Zero Clause License-00", shortIdentifier="0BSD")
            driver.refresh()
            license_name = driver.find_element_by_css_selector('td').text
            self.assertEqual(license_name, "BSD Zero Clause License-00")
            self.assertEqual(LicenseRequest.objects.get(id=license_obj.id).archive, False)
            if driver.find_element_by_id('archive_button' + str(license_obj.id)):
                driver.find_element_by_id('archive_button' + str(license_obj.id)).click()
                driver.find_element_by_id('confirm_archive').click()
                self.assertEqual(LicenseRequest.objects.get(id=license_obj.id).archive, True)
            else:
                pass

    @skipIf(not getAccessToken() and not getGithubUserId() and not getGithubUserName(), "You need to set gihub parameters in the secret.py file for this test to be executed properly.")
    def test_unarchive_license_requests_feature(self):
        """Check if license is shifted back to license requests when unarchive button is pressed"""
        login = TestUtil.gitHubLogin(self)
        self.assertTrue(login)
        cookie = self.client.cookies['sessionid']
        driver = self.selenium
        with patch('app.utils.checkPermission') as mock_checkPermission:
            mock_checkPermission.return_value = True
            driver.get(self.live_server_url+'/app/archive_requests/')
            driver.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
            table_contents = driver.find_element_by_css_selector('tbody').text
            self.assertEqual(table_contents, "No data available in table")
            archive_license_obj = LicenseRequest.objects.create(fullname="BSD Zero Clause License-00", shortIdentifier="0BSD", archive="True")
            driver.refresh()
            license_name = driver.find_element_by_css_selector('td').text
            self.assertEqual(license_name, "BSD Zero Clause License-00")
            self.assertEqual(LicenseRequest.objects.get(id=archive_license_obj.id).archive, True)
            if driver.find_element_by_id('unarchive_button' + str(archive_license_obj.id)):
                driver.find_element_by_id('unarchive_button' + str(archive_license_obj.id)).click()
                driver.find_element_by_id('confirm_unarchive').click()
                self.assertEqual(LicenseRequest.objects.get(id=archive_license_obj.id).archive, False)
            else:
                pass

class SubmitNewLicenseViewsTestCase(TestCase):

    def initialise(self):
        self.fullname = "BSD Zero Clause License"
        self.shortIdentifier = "0BSD"
        self.exampleUrl = "testUrl"
        self.sourceUrl = "http://landley.net/toybox/license.html"
        self.urls = [self.sourceUrl]
        self.osiApproved = "no"
        self.comments = "Test Comment"
        self.notes = ""
        self.licenseHeader = ""
        self.text ='<text> <copyrightText> <p>Copyright (C) 2006 by Rob Landley &lt;rob@landley.net&gt;</p> </copyrightText> <p>Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.</p> <p>THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.</p> </text>'
        self.userEmail = "test@mail.com"
        self.licenseAuthorName = ""
        self.listVersionAdded = ""
        self.xml = '<SPDXLicenseCollection xmlns="http://www.spdx.org/license"> <license isOsiApproved="false" licenseId="0BSD" listVersionAdded="" name="BSD Zero Clause License"> <crossRefs> <crossRef> http://landley.net/toybox/license.html</crossRef> </crossRefs> <standardLicenseHeader /> <notes /> <text> <p> &lt;text&gt; &lt;copyrightText&gt; &lt;p&gt;Copyright (C) 2006 by Rob Landley &amp;lt;rob@landley.net&amp;gt;&lt;/p&gt; &lt;/copyrightText&gt; &lt;p&gt;Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.&lt;/p&gt; &lt;p&gt;THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.&lt;/p&gt; &lt;/text&gt;</p> </text> </license> </SPDXLicenseCollection> '
        self.data_no_author = {"fullname": self.fullname, "shortIdentifier": self.shortIdentifier,
                    "sourceUrl": self.sourceUrl,'osiApproved': self.osiApproved, 'notes': self.notes,
                    "licenseHeader": self.licenseHeader, "text": self.text, "userEmail": self.userEmail,
                    "urlType": "tests", "exampleUrl":self.exampleUrl,"comments":self.comments}
        self.data = self.data_no_author.update({"licenseAuthorName": self.licenseAuthorName})

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
            self.assertIn("comments",resp.context["form"].fields)
            self.assertIn("licenseHeader",resp.context["form"].fields)
            self.assertIn("text",resp.context["form"].fields)
            self.assertIn("userEmail",resp.context["form"].fields)

    def test_generate_xml(self):
        """View for generating an xml from license submittal form fields"""
        self.initialise()
        xml = generateLicenseXml(self.osiApproved, self.shortIdentifier, self.fullname, self.listVersionAdded,
                                self.urls, self.licenseHeader, self.notes, self.text).replace(">","> ")
        self.assertEqual(self.xml, xml)

    @skipIf(not getAccessToken() and not getGithubUserId() and not getGithubUserName(), "You need to set gihub parameters in the secret.py file for this test to be executed properly.")
    def test_post_submit(self):
        """POST Request for submit a new license"""
        TEST_LOGIN_INFO = {
        "provider": "github",
        "uid": str(getGithubUserId()),
        "access_token": getAccessToken(),
        "login": getGithubUserName(),
        "id": getGithubUserId(),
        "password": 'pass'
        }
        # login first
        self.user = User.objects.create(username=TEST_LOGIN_INFO["login"],
                                        is_active=True,
                                        is_superuser=True)
        self.user.set_password(TEST_LOGIN_INFO["password"])
        self.user.save()
        social_auth = UserSocialAuth.objects.create(provider=TEST_LOGIN_INFO["provider"],
        uid=TEST_LOGIN_INFO["uid"],
        extra_data=TEST_LOGIN_INFO,
        user=self.user)
        self.user = authenticate(username=TEST_LOGIN_INFO["login"],
                                 password=TEST_LOGIN_INFO["password"])
        login = self.client.login(username=TEST_LOGIN_INFO["login"],
                                  password=TEST_LOGIN_INFO["password"])
        self.assertTrue(login)
        self.initialise()
        # login via GitHub
        resp = self.client.post(reverse("submit-new-license"),
                                self.data_no_author,
                                follow=True,
                                secure=True,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        licenseRequest = LicenseRequest.objects.last()
        self.assertEqual(licenseRequest.licenseAuthorName, "")


class EditLicenseXmlViewsTestCase(TestCase):
    def test_edit_license_xml(self):
        """View for editing the xml of a license, given its id"""
        license_obj = LicenseRequest.objects.create(fullname="BSD Zero Clause License-00", shortIdentifier="0BSD")
        license_id = license_obj.id
        resp = self.client.get(reverse("license_xml_editor", kwargs={'license_id': license_id}),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/editor.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"edit_license_xml")

    def test_error_license_requests_edit_xml(self):
        """Check if error page is displayed when the license id does not exist"""
        license_id = 0
        resp = self.client.get(reverse("license_xml_editor", kwargs={'license_id': license_id}),follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("404.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"edit_license_xml")

    def test_no_license_id_on_license_requests_edit_xml(self):
        """Check if the redirect works if no license id is provided in the url"""
        resp = self.client.get(reverse("license_xml_editor_none"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn("app/license_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseRequests")


class LicenseNamespaceViewsTestCase(TestCase):

    def test_license_requests(self):
        """GET Request for license requests list"""
        resp = self.client.get(reverse("license-namespace-requests"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/license_namespace_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseNamespaceRequests")


class PromoteLicenseNamespaceViewsTestCase(StaticLiveServerTestCase):

    def setUp(self):
        options = Options()
        options.add_argument('-headless')
        self.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_options=options)
        #login
        TEST_LOGIN_INFO = {
        "provider": "github",
        "uid": str(getGithubUserId()),
        "access_token": getAccessToken(),
        "login": getGithubUserName(),
        "id": getGithubUserId(),
        "password": 'pass'
        }
        # login first
        self.user = User.objects.create(username=TEST_LOGIN_INFO["login"],
                                        is_active=True,
                                        is_superuser=True)
        self.user.set_password(TEST_LOGIN_INFO["password"])
        self.user.save()
        social_auth = UserSocialAuth.objects.create(provider=TEST_LOGIN_INFO["provider"],
                                                    uid=TEST_LOGIN_INFO["uid"],
                                                    extra_data=TEST_LOGIN_INFO,
                                                    user=self.user)
        self.user = authenticate(username=TEST_LOGIN_INFO["login"],
                                 password=TEST_LOGIN_INFO["password"])
        login = self.client.login(username=TEST_LOGIN_INFO["login"],
                                  password=TEST_LOGIN_INFO["password"])
        self.assertTrue(login)
        # end login
        super(PromoteLicenseNamespaceViewsTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(PromoteLicenseNamespaceViewsTestCase, self).tearDown()


    @skipIf(not getAccessToken() and not getGithubUserId() and not getGithubUserName(), "You need to set gihub parameters in the secret.py file for this test to be executed properly.")
    def test_promote_license_namespace_feature(self):
        """Github access token,id and username should be added in .env to execute the test properly"""
        """Check if the license namespace is shifted to archive namespace when archive button is pressed"""
        driver = self.selenium
        driver.get(self.live_server_url+'/app/license_namespace_requests/')
        table_contents = driver.find_element_by_css_selector('tbody').text
        self.assertEqual(table_contents, "No data available in table")
        xml = generateLicenseXml('', "0BSD", "BSD Zero Clause License-00",
            '', ["http://wwww.spdx.org"], '', '', '')
        license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00",
                                                      licenseAuthorName="John Doe",
                                                      shortIdentifier="0BSD",
                                                      archive="False",
                                                      promoted="False",
                                                      url="http://wwww.spdx.org",
                                                      description="Description",
                                                      notes="Notes",
                                                      namespace="bsd-zero-clause-license-00",
                                                      userEmail="johndoe@gmail.com",
                                                      publiclyShared="True",
                                                      license_list_url="http://wwww.spdx.org",
                                                      github_repo_url="http://wwww.spdx.org",
                                                      xml=xml)
        driver.refresh()
        license_name = driver.find_element_by_css_selector('td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).promoted, False)

        resp = self.client.post(reverse("promoted-license-namespace-xml"),
                                {"promoted": True, "license_id": license_obj.id},
                                follow=True,
                                secure=True,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])


class ArchiveLicenseNamespaceViewsTestCase(StaticLiveServerTestCase):

    def setUp(self):
        options = Options()
        options.add_argument('-headless')
        self.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_options=options)
        super(ArchiveLicenseNamespaceViewsTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(ArchiveLicenseNamespaceViewsTestCase, self).tearDown()

    def test_archive_license_requests(self):
        """GET Request for archive license namespace requests list"""
        resp = self.client.get(reverse("archive-license-namespace-xml"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/archive_namespace_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"archiveNamespaceRequests")

    def test_error_archive_license_namespace(self):
        """Check if error page is displayed when the license id does not exist for archive license namespace"""
        license_id = 0
        resp = self.client.get(reverse("archived-license-namespace-information", args=(license_id,)),follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("404.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseNamespaceInformation")

    def test_archive_license_namespace_feature(self):
        """Check if the license namespace is shifted to archive namespace when archive button is pressed"""
        driver = self.selenium
        driver.get(self.live_server_url+'/app/license_namespace_requests/')
        table_contents = driver.find_element_by_css_selector('tbody').text
        self.assertEqual(table_contents, "No data available in table")
        xml = generateLicenseXml('', "0BSD", "BSD Zero Clause License-00",
            '', "http://wwww.spdx.org", '', '', '')
        license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00",
                                                      licenseAuthorName="John Doe",
                                                      shortIdentifier="0BSD",
                                                      archive="False",
                                                      url="http://wwww.spdx.org",
                                                      description="Description",
                                                      notes="Notes",
                                                      namespace="bsd-zero-clause-license-00",
                                                      userEmail="johndoe@gmail.com",
                                                      publiclyShared="True",
                                                      license_list_url="http://wwww.spdx.org",
                                                      github_repo_url="http://wwww.spdx.org",
                                                      xml=xml)
        driver.refresh()
        license_name = driver.find_element_by_css_selector('td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).archive, False)
        driver.find_element_by_id('archive_button' + str(license_obj.id)).click()
        driver.find_element_by_id('confirm_archive').click()
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).archive, True)

    def test_unarchive_license_namespace_feature(self):
        """Check if license namespace is shifted back to license namespace when unarchive button is pressed"""
        driver = self.selenium
        driver.get(self.live_server_url+'/app/archive_namespace_requests/')
        table_contents = driver.find_element_by_css_selector('tbody').text
        self.assertEqual(table_contents, "No data available in table")
        archive_license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00",
                                                              licenseAuthorName="John Doe",
                                                              shortIdentifier="0BSD",
                                                              archive="True",
                                                              url="http://wwww.spdx.org",
                                                              description="Description",
                                                              notes="Notes",
                                                              namespace="bsd-zero-clause-license-00",
                                                              userEmail="johndoe@gmail.com",
                                                              publiclyShared="True",
                                                              license_list_url="http://wwww.spdx.org",
                                                              github_repo_url="http://wwww.spdx.org")
        driver.refresh()
        license_name = driver.find_element_by_css_selector('td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=archive_license_obj.id).archive, True)
        driver.find_element_by_id('unarchive_button' + str(archive_license_obj.id)).click()
        driver.find_element_by_id('confirm_unarchive').click()
        self.assertEqual(LicenseNamespace.objects.get(id=archive_license_obj.id).archive, False)


class SubmitNewLicenseNamespaceViewsTestCase(TestCase):

    def initialise(self):
        self.fullname = "BSD Zero Clause License"
        self.shortIdentifier = "0BSD"
        self.sourceUrl = "http://landley.net/toybox/license.html"
        self.license_list_url = self.sourceUrl
        self.github_repo_url = self.sourceUrl
        self.osiApproved = "no"
        self.comments = ""
        self.notes = ""
        self.licenseHeader = ""
        self.text ='<text> <copyrightText> <p>Copyright (C) 2006 by Rob Landley &lt;rob@landley.net&gt;</p> </copyrightText> <p>Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.</p> <p>THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.</p> </text>'
        self.userEmail = "test@mail.com"
        self.licenseAuthorName = "John Doe"
        self.listVersionAdded = ""
        self.namespace = "j-d-ns"
        self.xml = '<SPDXLicenseCollection xmlns="http://www.spdx.org/license"> <license isOsiApproved="false" licenseId="0BSD" listVersionAdded="" name="BSD Zero Clause License"> <crossRefs> <crossRef> http://landley.net/toybox/license.html</crossRef> </crossRefs> <standardLicenseHeader /> <notes /> <text> <p> &lt;text&gt; &lt;copyrightText&gt; &lt;p&gt;Copyright (C) 2006 by Rob Landley &amp;lt;rob@landley.net&amp;gt;&lt;/p&gt; &lt;/copyrightText&gt; &lt;p&gt;Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.&lt;/p&gt; &lt;p&gt;THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.&lt;/p&gt; &lt;/text&gt;</p> </text> </license> </SPDXLicenseCollection> '
        self.data_no_author = {"fullname": self.fullname, "shortIdentifier": self.shortIdentifier,
                    "url": self.sourceUrl,'osiApproved': self.osiApproved, 'notes': self.notes,
                    "licenseHeader": self.licenseHeader, "text": self.text, "userEmail": self.userEmail,
                    "urlType": "tests", "namespace": self.namespace, "license_list_url": self.license_list_url, "github_repo_url": self.github_repo_url}
        self.data = self.data_no_author.update({"licenseAuthorName": self.licenseAuthorName})

    def test_submit_new_license_namespace(self):
        """GET Request for submit a new license namespace"""
        resp = self.client.get(reverse("submit-new-license-namespace"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/submit_new_license_namespace.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"submitNewLicenseNamespace")
        self.assertIn("form",resp.context)
        if "form" in resp.context:
            self.assertIn("fullname",resp.context["form"].fields)
            self.assertIn("organisation",resp.context["form"].fields)
            self.assertIn("namespace",resp.context["form"].fields)
            self.assertIn("shortIdentifier",resp.context["form"].fields)
            self.assertIn("publiclyShared",resp.context["form"].fields)
            self.assertIn("url",resp.context["form"].fields)
            self.assertIn("license_list_url",resp.context["form"].fields)
            self.assertIn("github_repo_url",resp.context["form"].fields)
            self.assertIn("description",resp.context["form"].fields)
            self.assertIn("licenseAuthorName",resp.context["form"].fields)
            self.assertIn("userEmail",resp.context["form"].fields)

    def test_generate_xml(self):
        """View for generating an xml from license namespace submittal form fields"""
        self.initialise()
        xml = generateLicenseXml(self.osiApproved, self.shortIdentifier, self.fullname, self.listVersionAdded,
                                [self.sourceUrl], self.licenseHeader, self.notes, self.text).replace(">","> ")
        self.assertEqual(self.xml, xml)

    @skipIf(not getAccessToken() and not getGithubUserId() and not getGithubUserName(), "You need to set gihub parameters in the secret.py file for this test to be executed properly.")
    def test_post_submit(self):
        """POST Request for submit a new license namespace"""
        TEST_LOGIN_INFO = {
        "provider": "github",
        "uid": str(getGithubUserId()),
        "access_token": getAccessToken(),
        "login": getGithubUserName(),
        "id": getGithubUserId(),
        "password": 'pass'
        }
        # login first
        self.user = User.objects.create(username=TEST_LOGIN_INFO["login"],
                                        is_active=True,
                                        is_superuser=True)
        self.user.set_password(TEST_LOGIN_INFO["password"])
        self.user.save()
        social_auth = UserSocialAuth.objects.create(provider=TEST_LOGIN_INFO["provider"],
        uid=TEST_LOGIN_INFO["uid"],
        extra_data=TEST_LOGIN_INFO,
        user=self.user)
        self.user = authenticate(username=TEST_LOGIN_INFO["login"],
                                 password=TEST_LOGIN_INFO["password"])
        login = self.client.login(username=TEST_LOGIN_INFO["login"],
                                  password=TEST_LOGIN_INFO["password"])
        self.assertTrue(login)
        self.initialise()
        # login via GitHub
        resp = self.client.post(reverse("submit-new-license-namespace"),
                                self.data,
                                follow=True,
                                secure=True,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])


class EditLicenseNamespaceXmlViewsTestCase(TestCase):
    def test_edit_license_xml(self):
        """View for editing the xml of a license namespace, given its id"""
        license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00", shortIdentifier="0BSD")
        license_id = license_obj.id
        resp = self.client.get(reverse("license_namespace_xml_editor", kwargs={'license_id': license_id}),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/ns_editor.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"edit_license_namespace_xml")

    def test_error_license_requests_edit_xml(self):
        """Check if error page is displayed when the license namespace id does not exist"""
        license_id = 0
        resp = self.client.get(reverse("license_namespace_xml_editor", kwargs={'license_id': license_id}),follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("404.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"edit_license_namespace_xml")

    def test_no_license_id_on_license_requests_edit_xml(self):
        """Check if the redirect works if no license namespace id is provided in the url"""
        resp = self.client.get(reverse("license_namespace_xml_editor_none"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn("app/license_namespace_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseNamespaceRequests")
