# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for Compare API views and file upload.
"""


from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from api.models import CompareFileUpload
from tests.test_helpers import getExamplePath


class CompareFileUploadTests(APITestCase):
    """Test for compare api with all
    possible combination of POST and GET
    request with login enabled.
    """

    def setUp(self):
        self.username = "compareapitestuser"
        self.password = "compareapitestpass"
        self.tearDown()
        self.credentials = {"username": self.username, "password": self.password}
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf"))
        self.addCleanup(self.rdf_file.close)
        self.rdf_file2 = open(getExamplePath("SPDXRdfExample-v2.3.spdx.rdf"))
        self.addCleanup(self.rdf_file2.close)
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"))
        self.addCleanup(self.tv_file.close)

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        CompareFileUpload.objects.all().delete()

    def test_compare_api(self):
        # Access get without login
        resp1 = self.client.get(reverse("compare-api"))
        self.assertEqual(resp1.status_code, 200)
        # Access get after login
        self.client.login(username=self.username, password=self.password)
        resp2 = self.client.get(reverse("compare-api"))
        self.assertEqual(resp2.status_code, 200)
        # Compare two valid RDF files
        resp3 = self.client.post(
            reverse("compare-api"),
            {
                "file1": self.rdf_file,
                "file2": self.rdf_file2,
                "rfilename": "compare-apitest.xls",
            },
            format="multipart",
        )
        self.assertEqual(resp3.status_code, 200)
        self.assertEqual(
            resp3.data["owner"], User.objects.get_by_natural_key(self.username).id
        )
        self.assertTrue(resp3.data["result"].startswith(settings.MEDIA_URL))
        # Compare RDF file with TAG Value file (mixed formats, both valid SPDX)
        self.rdf_file.seek(0)
        resp4 = self.client.post(
            reverse("compare-api"),
            {
                "file1": self.rdf_file,
                "file2": self.tv_file,
                "rfilename": "compare-apitest.xls",
            },
            format="multipart",
        )
        self.assertEqual(resp4.status_code, 200)
        self.client.logout()

    def test_compare_without_one_argument(self):
        self.client.login(username=self.username, password=self.password)
        resp5 = self.client.post(
            reverse("compare-api"),
            {"file1": self.rdf_file, "file2": self.rdf_file2},
            format="multipart",
        )
        self.assertEqual(resp5.status_code, 400)

        resp6 = self.client.post(
            reverse("compare-api"),
            {"file1": self.rdf_file, "rfilename": "compare-apitest.xls"},
            format="multipart",
        )
        self.assertEqual(resp6.status_code, 400)

        resp7 = self.client.post(
            reverse("compare-api"),
            {"file2": self.rdf_file, "rfilename": "compare-apitest.xls"},
            format="multipart",
        )
        self.assertEqual(resp7.status_code, 400)
        self.client.logout()


@override_settings(FILE_UPLOAD_MAX_MEMORY_SIZE=0)
class CompareLargeFileUploadTests(APITestCase):
    """Compare API must handle uploads routed through TemporaryUploadedFile."""

    def setUp(self):
        self.username = "compareuploadtestuser"
        self.password = "compareuploadtestpass"
        self.tearDown()
        self.credentials = {"username": self.username, "password": self.password}
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        CompareFileUpload.objects.all().delete()

    def test_compare_api_large_file(self):
        """A large (temp-file) upload must not raise FileNotFoundError."""

        self.client.login(username=self.username, password=self.password)
        with open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf")) as f1, \
                open(getExamplePath("SPDXRdfExample-v2.3.spdx.rdf")) as f2:
            resp = self.client.post(
                reverse("compare-api"),
                {
                    "file1": f1,
                    "file2": f2,
                    "rfilename": "compare-largefiletest",
                },
                format="multipart",
            )
        self.assertEqual(resp.status_code, 200)
        self.client.logout()
