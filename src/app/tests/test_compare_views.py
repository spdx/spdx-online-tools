# -*- coding: utf-8 -*-


from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse


from django.contrib.auth.models import User
from django.conf import settings
import os

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