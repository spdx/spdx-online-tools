# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for Convert API views and file upload.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from api.models import ConvertFileUpload
from tests.test_helpers import getExamplePath


class ConvertFileUploadTests(APITestCase):
    """Test for convert api with all
    possible combination of POST and GET
    request with login enabled.
    """

    def setUp(self):
        self.username = "convertapitestuser"
        self.password = "convertapitestpass"
        self.tearDown()
        self.credentials = {"username": self.username, "password": self.password}
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.tag = "TAG"
        self.rdf = "RDFXML"
        self.xlsx = "XLS"
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.2.spdx"), "rb")
        self.addCleanup(self.tv_file.close)
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf"), "rb")
        self.addCleanup(self.rdf_file.close)
        self.xlsx_file = open(getExamplePath("SPDXSpreadsheetExample-v2.2.xls"), "rb")
        self.addCleanup(self.xlsx_file.close)

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        ConvertFileUpload.objects.all().delete()

    def test_convert_api(self):
        # Access get without login
        resp1 = self.client.get(reverse("convert-api"))
        self.assertEqual(resp1.status_code, 200)
        # Access get after login
        self.client.login(username=self.username, password=self.password)
        resp2 = self.client.get(reverse("convert-api"))
        self.assertEqual(resp2.status_code, 200)
        self.client.logout()

    def test_convert_tagtordf_api(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.post(
            reverse("convert-api"),
            {
                "file": self.tv_file,
                "from_format": self.tag,
                "to_format": self.rdf,
                "cfilename": "tagtordf-apitest",
            },
            format="multipart",
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data["message"], "Success")
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(
            resp.data["owner"], User.objects.get_by_natural_key(self.username).id
        )
        self.client.logout()

    def test_convert_tagtoxlsx_api(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.post(
            reverse("convert-api"),
            {
                "file": self.tv_file,
                "from_format": self.tag,
                "to_format": self.xlsx,
                "cfilename": "tagtoxlsx-apitest",
            },
            format="multipart",
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data["message"], "Success")
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(
            resp.data["owner"], User.objects.get_by_natural_key(self.username).id
        )
        self.client.logout()

    def test_convert_rdftotag_api(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.post(
            reverse("convert-api"),
            {
                "file": self.rdf_file,
                "from_format": self.rdf,
                "to_format": self.tag,
                "cfilename": "rdftotag-apitest",
            },
            format="multipart",
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data["message"], "Success")
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(
            resp.data["owner"], User.objects.get_by_natural_key(self.username).id
        )
        self.client.logout()

    def test_convert_rdftoxlsx_api(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.post(
            reverse("convert-api"),
            {
                "file": self.rdf_file,
                "from_format": self.rdf,
                "to_format": self.xlsx,
                "cfilename": "rdftoxlsx-apitest",
            },
            format="multipart",
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data["message"], "Success")
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(
            resp.data["owner"], User.objects.get_by_natural_key(self.username).id
        )
        self.client.logout()

    def test_convert_xlsxtordf_api(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.post(
            reverse("convert-api"),
            {
                "file": self.xlsx_file,
                "from_format": self.xlsx,
                "to_format": self.rdf,
                "cfilename": "xlsxtordf-apitest",
            },
            format="multipart",
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data["message"], "Success")
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(
            resp.data["owner"], User.objects.get_by_natural_key(self.username).id
        )
        self.client.logout()

    def test_convert_xlsxtotag_api(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.post(
            reverse("convert-api"),
            {
                "file": self.xlsx_file,
                "from_format": self.xlsx,
                "to_format": self.tag,
                "cfilename": "xlsxtotag-apitest",
            },
            format="multipart",
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data["message"], "Success")
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(
            resp.data["owner"], User.objects.get_by_natural_key(self.username).id
        )
        self.client.logout()

    def test_convert_without_one_argument(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.post(
            reverse("convert-api"),
            {
                "file": self.xlsx_file,
                "to_format": self.tag,
                "cfilename": "xlsxtotag-apitest",
            },
            format="multipart",
        )
        self.assertEqual(resp.status_code, 400)

        resp2 = self.client.post(
            reverse("convert-api"),
            {
                "from_format": self.xlsx,
                "to_format": self.tag,
                "cfilename": "xlsxtotag-apitest",
            },
            format="multipart",
        )
        self.assertEqual(resp2.status_code, 400)

        resp3 = self.client.post(
            reverse("convert-api"),
            {"file": self.xlsx_file, "from_format": self.xlsx, "to_format": self.tag},
            format="multipart",
        )
        self.assertEqual(resp3.status_code, 400)

        resp4 = self.client.post(
            reverse("convert-api"),
            {
                "file": self.xlsx_file,
                "from_format": self.xlsx,
                "cfilename": "xlsxtotag-apitest",
            },
            format="multipart",
        )
        self.assertEqual(resp4.status_code, 400)
        self.client.logout()


@override_settings(FILE_UPLOAD_MAX_MEMORY_SIZE=0)
class ConvertLargeFileUploadTests(APITestCase):
    """Convert API must handle uploads routed through TemporaryUploadedFile."""

    def setUp(self):
        self.username = "convertuploadtestuser"
        self.password = "convertuploadtestpass"
        self.tearDown()
        self.credentials = {"username": self.username, "password": self.password}
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.tag = "TAG"
        self.rdf = "RDFXML"

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        ConvertFileUpload.objects.all().delete()

    def test_convert_api_large_file(self):
        """A large (temp-file) upload must not raise FileNotFoundError."""

        self.client.login(username=self.username, password=self.password)
        with open(getExamplePath("SPDXTagExample-v2.2.spdx"), "rb") as f:
            resp = self.client.post(
                reverse("convert-api"),
                {
                    "file": f,
                    "from_format": self.tag,
                    "to_format": self.rdf,
                    "cfilename": "tagtordf-largefiletest",
                },
                format="multipart",
            )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data["message"], "Success")
        self.client.logout()
