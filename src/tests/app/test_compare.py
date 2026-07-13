# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for Compare views in the Web app.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from tests.test_helpers import getExamplePath


class CompareViewsTestCase(TestCase):

    def setUp(self):
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf"))
        self.addCleanup(self.rdf_file.close)
        self.rdf_file2 = open(getExamplePath("SPDXRdfExample-v2.3.spdx.rdf"))
        self.addCleanup(self.rdf_file2.close)
        self.invalid_rdf = open(getExamplePath("SPDXRdfExample-v2.0_invalid.rdf"))
        self.addCleanup(self.invalid_rdf.close)

    def test_compare(self):
        """GET Request for compare"""
        if not settings.ANONYMOUS_LOGIN_ENABLED:
            resp = self.client.get(reverse("compare"), follow=True, secure=True)
            self.assertNotEqual(resp.redirect_chain, [])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code, 200)
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp2 = self.client.get(reverse("compare"), follow=True, secure=True)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.redirect_chain, [])
        self.assertIn("app/compare.html", (i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__, "compare")
        self.client.logout()

    def test_compare_post_without_login(self):
        """POST Request for compare without login or ANONYMOUS_LOGIN_ENABLED==False """
        if not settings.ANONYMOUS_LOGIN_ENABLED:
            resp = self.client.post(reverse("compare"), {'rfilename': "comparetest", 'files': [self.rdf_file, self.rdf_file2]}, follow=True, secure=True)
            self.assertNotEqual(resp.redirect_chain, [])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code, 200)

    def test_compare_post_without_file(self):
        """POST Request for compare without file upload"""
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"), {'rfilename': "comparetest"}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 404)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.client.logout()

    def test_compare_post_with_one_file(self):
        """POST Request for compare with only one file"""
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"), {'rfilename': "comparetest", 'files': [self.rdf_file, ]}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 404)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.client.logout()

    def test_compare_two_rdf(self):
        """POST Request for comparing two rdf files"""
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"), {'rfilename': 'comparetest', 'files': [self.rdf_file, self.rdf_file2]}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "application/vnd.ms-excel")
        self.client.logout()

    def test_compare_invalid_rdf(self):
        """POST Request for comparing two files"""
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"), {'rfilename': 'comparetest', 'files': [self.rdf_file, self.invalid_rdf]}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 400)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.client.logout()
