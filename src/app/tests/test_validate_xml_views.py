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