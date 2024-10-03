# -*- coding: utf-8 -*-


from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse


from django.contrib.auth.models import User
from django.conf import settings
import os


def getExamplePath(filename):
    return os.path.join(settings.EXAMPLES_DIR, filename)

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