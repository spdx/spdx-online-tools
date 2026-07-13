# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for validate, compare, convert, and check license views.
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
            self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"))
            resp = self.client.post(reverse("validate"), {'file': self.tv_file, 'format': 'TAG'}, follow=True, secure=True)
            self.assertNotEqual(resp.redirect_chain, [])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.tv_file.close()
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
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"))
        resp = self.client.post(reverse("validate"), {'file': self.tv_file, 'format': 'TAG'}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"This SPDX document is valid.")
        self.client.logout()

    def test_upload_rdf(self):
        """POST Request for validate validating rdf files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf"))
        resp = self.client.post(reverse("validate"), {'file': self.rdf_file, 'format': 'RDFXML'}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"This SPDX document is valid.")
        self.rdf_file.close()
        self.client.logout()

    def test_upload_other(self):
        """POST Request for validate validating other files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.other_file = open(getExamplePath("Other.txt"))
        resp = self.client.post(reverse("validate"), {'file': self.other_file, 'format': 'TAG'}, follow=True, secure=True)
        self.assertTrue(resp.status_code, 400)
        self.assertTrue('error' in resp.context)
        self.other_file.close()
        self.client.logout()

    def test_upload_inv_tv(self):
        """POST Request for validate validating tag value files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.invalid_tv_file = open(getExamplePath("SPDXTagExample-v2.0_invalid.spdx"))
        resp = self.client.post(reverse("validate"), {'file': self.invalid_tv_file, 'format': 'TAG'}, follow=True)
        self.assertTrue(resp.status_code, 400)
        self.assertTrue('error' in resp.context)
        self.invalid_tv_file.close()
        self.client.logout()

    def test_upload_inv_rdf(self):
        """POST Request for validate validating rdf files """
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.invalid_rdf_file = open(getExamplePath("SPDXRdfExample-v2.0_invalid.rdf"))
        resp = self.client.post(reverse("validate"), {'file': self.invalid_rdf_file, 'format': 'RDFXML'}, follow=True)
        self.assertTrue(resp.status_code, 400)
        self.assertTrue('error' in resp.context)
        self.client.logout()


class CompareViewsTestCase(TestCase):

    def initialise(self):
        """ Open files"""
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf"))
        self.rdf_file2 = open(getExamplePath("SPDXRdfExample-v2.3.spdx.rdf"))
        self.invalid_rdf = open(getExamplePath("SPDXRdfExample-v2.0_invalid.rdf"))

    def exit(self):
        """ Close files"""
        self.rdf_file.close()
        self.rdf_file2.close()
        self.invalid_rdf.close()

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
            self.initialise()
            resp = self.client.post(reverse("compare"), {'rfilename': "comparetest", 'files': [self.rdf_file, self.rdf_file2]}, follow=True, secure=True)
            self.assertNotEqual(resp.redirect_chain, [])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.assertEqual(resp.status_code, 200)
            self.exit()

    def test_compare_post_without_file(self):
        """POST Request for compare without file upload"""
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"), {'rfilename': "comparetest"}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 404)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.exit()
        self.client.logout()

    def test_compare_post_with_one_file(self):
        """POST Request for compare with only one file"""
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"), {'rfilename': "comparetest", 'files': [self.rdf_file, ]}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 404)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.exit()
        self.client.logout()

    def test_compare_two_rdf(self):
        """POST Request for comparing two rdf files"""
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"), {'rfilename': 'comparetest', 'files': [self.rdf_file, self.rdf_file2]}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "application/vnd.ms-excel")
        self.exit()
        self.client.logout()

    def test_compare_invalid_rdf(self):
        """POST Request for comparing two files"""
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"), {'rfilename': 'comparetest', 'files': [self.rdf_file, self.invalid_rdf]}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 400)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.exit()
        self.client.logout()


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
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"))
        resp = self.client.post(reverse("convert"), {'cfilename': "tagtest", 'cfileformat': ".rdf.xml", 'from_format': "TAG", 'to_format': "RDFXML", 'file': self.tv_file}, follow=True, secure=True)
        self.assertTrue(resp.status_code == 406 or resp.status_code == 200)
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "application/rdf+xml")
        self.tv_file.close()
        self.client.logout()

    def test_convert_tagtoxlsx(self):
        """POST Request for convert tag to spreadsheet"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"))
        resp = self.client.post(reverse("convert"), {'cfilename': "tagtest", 'cfileformat': ".xlsx", 'from_format': "TAG", 'to_format': "XLSX", 'file': self.tv_file}, follow=True)
        self.assertTrue(resp.status_code == 406 or resp.status_code == 200)
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "application/vnd.ms-excel")
        self.tv_file.close()
        self.client.logout()

    def test_convert_rdftotag(self):
        """POST Request for convert rdf to tag"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf"))
        resp = self.client.post(reverse("convert"), {'cfilename': "rdftest", 'cfileformat': ".spdx", 'from_format': "RDFXML", 'to_format': "TAG", 'file': self.rdf_file}, follow=True)
        self.assertTrue(resp.status_code == 406 or resp.status_code == 200)
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "text/tag-value")
        self.rdf_file.close()
        self.client.logout()

    def test_convert_rdftoxlsx(self):
        """POST Request for convert rdf to spreadsheet"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf"))
        resp = self.client.post(reverse("convert"), {'cfilename': "rdftest", 'cfileformat': ".xls", 'from_format': "RDFXML", 'to_format': "XLS", 'file': self.rdf_file}, follow=True)
        self.assertTrue(resp.status_code == 406 or resp.status_code == 200)
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "application/vnd.ms-excel")
        self.rdf_file.close()
        self.client.logout()

    def test_convert_xlsxtotag(self):
        """POST Request for convert spreadsheet to tag"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.xls_file = open(getExamplePath("SPDXSpreadsheetExample-2.0.xls"), "rb")
        resp = self.client.post(reverse("convert"), {'cfilename': "xlsxtest", 'cfileformat': ".spdx", 'from_format': "XLS", 'to_format': "TAG", 'file': self.xls_file}, follow=True)
        self.assertTrue(resp.status_code == 406 or resp.status_code == 200)
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "text/tag-value")
        self.xls_file.close()
        self.client.logout()

    def test_convert_xlsxtordf(self):
        """POST Request for convert spreadsheet to rdf"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.xls_file = open(getExamplePath("SPDXSpreadsheetExample-2.0.xls"), "rb")
        resp = self.client.post(reverse("convert"), {'cfilename': "xlsxtest", 'cfileformat': ".rdf", 'from_format': "XLS", 'to_format': "RDFXML", 'file': self.xls_file}, follow=True)
        self.assertTrue(resp.status_code == 406 or resp.status_code == 200)
        self.assertIn("medialink", resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type", resp.context)
        self.assertEqual(resp.context["Content-Type"], "application/rdf+xml")
        self.xls_file.close()
        self.client.logout()

    def test_other_convert_formats(self):
        """POST Request for converting invalid formats"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.xls_file = open(getExamplePath("SPDXSpreadsheetExample-2.0.xls"), "rb")
        resp = self.client.post(reverse("convert"), {'cfilename': "xlsxtest", 'cfileformat': ".html", 'from_format': "Spreadsheet", 'to_format': "HTML", 'file': self.xls_file}, follow=True)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.context)
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.0.rdf"), "rb")
        resp = self.client.post(reverse("convert"), {'cfilename': "rdftest", 'cfileformat': ".pdf", 'from_format': "RDF", 'to_format': "PDF", 'file': self.rdf_file}, follow=True)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.context)
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"), "rb")
        resp = self.client.post(reverse("convert"), {'cfilename': "tagtest", 'cfileformat': ".txt", 'from_format': "Tag", 'to_format': "text", 'file': self.tv_file}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.context)
        self.client.logout()


class CheckLicenseViewsTestCase(TestCase):

    def setUp(self):
        self.licensefile = open(getExamplePath("AFL-1.1.txt"))
        self.licensetext = self.licensefile.read()

    def test_check_license(self):
        """GET Request for check license"""
        if not settings.ANONYMOUS_LOGIN_ENABLED:
            resp = self.client.get(reverse("check-license"), follow=True, secure=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotEqual(resp.redirect_chain, [])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.client.force_login(User.objects.get_or_create(username='checklicensetestuser')[0])
        resp2 = self.client.get(reverse("check-license"), follow=True, secure=True)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.redirect_chain, [])
        self.assertIn("app/check_license.html", (i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__, "check_license")
        self.client.logout()
