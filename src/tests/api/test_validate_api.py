# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for Validate API views and file upload.
"""


from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from api.models import ValidateFileUpload
from tests.test_helpers import getExamplePath


class ValidateFileUploadTests(APITestCase):
    """Test for validate api with all
    possible combination of POST and GET
    request with login enabled.
    """

    def setUp(self):
        self.username = "validateapitestuser"
        self.password = "validateapitestpass"
        self.tearDown()
        self.credentials = {"username": self.username, "password": self.password}
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"))
        self.addCleanup(self.tv_file.close)
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf"))
        self.addCleanup(self.rdf_file.close)
        self.invalid_tv_file = open(getExamplePath("SPDXTagExample-v2.0_invalid.spdx"))
        self.addCleanup(self.invalid_tv_file.close)
        self.invalid_rdf_file = open(getExamplePath("SPDXRdfExample-v2.0_invalid.rdf"))
        self.addCleanup(self.invalid_rdf_file.close)

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        ValidateFileUpload.objects.all().delete()

    def test_validate_api(self):
        # Access get without login
        resp1 = self.client.get(reverse("validate-api"))
        self.assertEqual(resp1.status_code, 200)
        self.client.login(username=self.username, password=self.password)
        # Access get after login
        resp2 = self.client.get(reverse("validate-api"))
        self.assertEqual(resp2.status_code, 200)
        # Valid Tag Value file
        resp3 = self.client.post(
            reverse("validate-api"),
            {"file": self.tv_file, "format": "TAG"},
            format="multipart",
        )
        self.assertEqual(resp3.status_code, 200)
        self.assertEqual(
            resp3.data["owner"], User.objects.get_by_natural_key(self.username).id
        )
        self.assertEqual(resp3.data["result"], "This SPDX document is valid.")
        # Valid RDF file
        resp4 = self.client.post(
            reverse("validate-api"),
            {"file": self.rdf_file, "format": "RDFXML"},
            format="multipart",
        )
        self.assertEqual(resp4.status_code, 200)
        self.assertEqual(
            resp4.data["owner"], User.objects.get_by_natural_key(self.username).id
        )
        self.assertEqual(resp4.data["result"], "This SPDX document is valid.")
        # Invalid Tag Value file
        resp5 = self.client.post(
            reverse("validate-api"),
            {"file": self.invalid_tv_file, "format": "TAG"},
            format="multipart",
        )
        self.assertEqual(
            resp5.data["owner"], User.objects.get_by_natural_key(self.username).id
        )
        self.assertEqual(resp5.status_code, 400)
        self.assertNotEqual(resp5.data["result"], "This SPDX document is valid.")
        # Invalid RDF file
        resp6 = self.client.post(
            reverse("validate-api"),
            {"file": self.invalid_rdf_file, "format": "RDFXML"},
            format="multipart",
        )
        self.assertEqual(
            resp6.data["owner"], User.objects.get_by_natural_key(self.username).id
        )
        self.assertEqual(resp6.status_code, 400)
        self.assertNotEqual(resp6.data["result"], "This SPDX document is valid.")
        self.client.logout()

    def test_validate_without_argument(self):
        self.client.login(username=self.username, password=self.password)
        resp7 = self.client.post(reverse("validate-api"), {}, format="multipart")
        self.assertEqual(resp7.status_code, 400)
        self.client.logout()


@override_settings(FILE_UPLOAD_MAX_MEMORY_SIZE=0)
class ValidateLargeFileUploadTests(APITestCase):
    """Validate API must handle uploads routed through TemporaryUploadedFile."""

    def setUp(self):
        self.username = "validateuploadtestuser"
        self.password = "validateuploadtestpass"
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
        ValidateFileUpload.objects.all().delete()

    def test_validate_api_large_file(self):
        """A large (temp-file) upload must not raise FileNotFoundError."""

        self.client.login(username=self.username, password=self.password)
        with open(getExamplePath("SPDXTagExample-v2.0.spdx")) as f:
            resp = self.client.post(
                reverse("validate-api"),
                {"file": f, "format": "TAG"},
                format="multipart",
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["result"], "This SPDX document is valid.")
        self.client.logout()
