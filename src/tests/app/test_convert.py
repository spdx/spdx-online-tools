# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for Convert views in the Web app.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from tests.test_helpers import getExamplePath


class ConvertViewsTestCase(TestCase):

    def test_convert(self):
        """GET Request for convert"""
        if not settings.ANONYMOUS_LOGIN_ENABLED:
            resp = self.client.get(reverse("convert"), follow=True, secure=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotEqual(resp.redirect_chain, [])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        resp2 = self.client.get(reverse("convert"), follow=True, secure=True)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.redirect_chain, [])
        self.assertIn("app/convert.html", (i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__, "convert")
        self.client.logout()

    def test_convert_tagtordf(self):
        """POST Request for convert tag to rdf"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        with open(getExamplePath("SPDXTagExample-v2.0.spdx")) as tv_file:
            resp = self.client.post(reverse("convert"), {'cfilename': "tagtest", 'cfileformat': ".rdf.xml", 'from_format': "TAG", 'to_format': "RDFXML", 'file': tv_file}, follow=True, secure=True)
        self.assertIn(resp.status_code, [200, 406])
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "application/rdf+xml")
        self.client.logout()

    def test_convert_tagtoxlsx(self):
        """POST Request for convert tag to spreadsheet"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        with open(getExamplePath("SPDXTagExample-v2.0.spdx")) as tv_file:
            resp = self.client.post(reverse("convert"), {'cfilename': "tagtest", 'cfileformat': ".xlsx", 'from_format': "TAG", 'to_format': "XLSX", 'file': tv_file}, follow=True)
        self.assertIn(resp.status_code, [200, 406])
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "application/vnd.ms-excel")
        self.client.logout()

    def test_convert_rdftotag(self):
        """POST Request for convert rdf to tag"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        with open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf")) as rdf_file:
            resp = self.client.post(reverse("convert"), {'cfilename': "rdftest", 'cfileformat': ".spdx", 'from_format': "RDFXML", 'to_format': "TAG", 'file': rdf_file}, follow=True)
        self.assertIn(resp.status_code, [200, 406])
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "text/tag-value")
        self.client.logout()

    def test_convert_rdftoxlsx(self):
        """POST Request for convert rdf to spreadsheet"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        with open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf")) as rdf_file:
            resp = self.client.post(reverse("convert"), {'cfilename': "rdftest", 'cfileformat': ".xls", 'from_format': "RDFXML", 'to_format': "XLS", 'file': rdf_file}, follow=True)
        self.assertIn(resp.status_code, [200, 406])
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "application/vnd.ms-excel")
        self.client.logout()

    def test_convert_xlsxtotag(self):
        """POST Request for convert spreadsheet to tag"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        with open(getExamplePath("SPDXSpreadsheetExample-2.0.xls"), "rb") as xls_file:
            resp = self.client.post(reverse("convert"), {'cfilename': "xlsxtest", 'cfileformat': ".spdx", 'from_format': "XLS", 'to_format': "TAG", 'file': xls_file}, follow=True)
        self.assertIn(resp.status_code, [200, 406])
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "text/tag-value")
        self.client.logout()

    def test_convert_xlsxtordf(self):
        """POST Request for convert spreadsheet to rdf"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        with open(getExamplePath("SPDXSpreadsheetExample-2.0.xls"), "rb") as xls_file:
            resp = self.client.post(reverse("convert"), {'cfilename': "xlsxtest", 'cfileformat': ".rdf", 'from_format': "XLS", 'to_format': "RDFXML", 'file': xls_file}, follow=True)
        self.assertIn(resp.status_code, [200, 406])
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "application/rdf+xml")
        self.client.logout()

    def test_other_convert_formats(self):
        """POST Request for converting invalid formats"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        with open(getExamplePath("SPDXSpreadsheetExample-2.0.xls"), "rb") as xls_file:
            resp = self.client.post(reverse("convert"), {'cfilename': "xlsxtest", 'cfileformat': ".html", 'from_format': "Spreadsheet", 'to_format': "HTML", 'file': xls_file}, follow=True)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.context)
        with open(getExamplePath("SPDXRdfExample-v2.0.rdf"), "rb") as rdf_file:
            resp = self.client.post(reverse("convert"), {'cfilename': "rdftest", 'cfileformat': ".pdf", 'from_format': "RDF", 'to_format': "PDF", 'file': rdf_file}, follow=True)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.context)
        with open(getExamplePath("SPDXTagExample-v2.0.spdx"), "rb") as tv_file:
            resp = self.client.post(reverse("convert"), {'cfilename': "tagtest", 'cfileformat': ".txt", 'from_format': "Tag", 'to_format': "text", 'file': tv_file}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.context)
        self.client.logout()
