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
