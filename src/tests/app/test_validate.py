# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for Validate views in the Web app.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from tests.test_helpers import getExamplePath


class ValidateViewsTestCase(TestCase):

    def test_validate(self):
        """GET Request for validate"""
        if not settings.ANONYMOUS_LOGIN_ENABLED:
            resp = self.client.get(reverse("validate"), follow=True, secure=True)
            self.assertNotEqual(resp.redirect_chain, [])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code, 200)

        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        resp2 = self.client.get(reverse("validate"), follow=True, secure=True)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.redirect_chain, [])
        self.assertIn("app/validate.html", (i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__, "validate")
        self.client.logout()

    def test_validate_post_without_login(self):
        """POST Request for validate without login or ANONYMOUS_LOGIN_DISABLED """
        if not settings.ANONYMOUS_LOGIN_ENABLED:
            with open(getExamplePath("SPDXTagExample-v2.0.spdx")) as tv_file:
                resp = self.client.post(reverse("validate"), {'file': tv_file, 'format': 'TAG'}, follow=True, secure=True)
            self.assertNotEqual(resp.redirect_chain, [])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code, 200)

    def test_validate_post_without_file(self):
        """POST Request for validate without file upload"""
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        resp = self.client.post(reverse("validate"), {}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 404)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.client.logout()

    def test_upload_tv(self):
        """POST Request for validate validating tag value files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        with open(getExamplePath("SPDXTagExample-v2.0.spdx")) as tv_file:
            resp = self.client.post(reverse("validate"), {'file': tv_file, 'format': 'TAG'}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"This SPDX document is valid.")
        self.client.logout()

    def test_upload_rdf(self):
        """POST Request for validate validating rdf files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        with open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf")) as rdf_file:
            resp = self.client.post(reverse("validate"), {'file': rdf_file, 'format': 'RDFXML'}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"This SPDX document is valid.")
        self.client.logout()

    def test_upload_other(self):
        """POST Request for validate validating other files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        with open(getExamplePath("Other.txt")) as other_file:
            resp = self.client.post(reverse("validate"), {'file': other_file, 'format': 'TAG'}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 400)
        self.assertTrue('error' in resp.context)
        self.client.logout()

    def test_upload_inv_tv(self):
        """POST Request for validate validating tag value files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        with open(getExamplePath("SPDXTagExample-v2.0_invalid.spdx")) as invalid_tv_file:
            resp = self.client.post(reverse("validate"), {'file': invalid_tv_file, 'format': 'TAG'}, follow=True)
        self.assertEqual(resp.status_code, 400)
        self.assertTrue('error' in resp.context)
        self.client.logout()

    def test_upload_inv_rdf(self):
        """POST Request for validate validating rdf files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        with open(getExamplePath("SPDXRdfExample-v2.0_invalid.rdf")) as invalid_rdf_file:
            resp = self.client.post(reverse("validate"), {'file': invalid_rdf_file, 'format': 'RDFXML'}, follow=True)
        self.assertEqual(resp.status_code, 400)
        self.assertTrue('error' in resp.context)
        self.client.logout()
