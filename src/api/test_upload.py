# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""Regression tests for large-file uploads.

Django stores uploads above FILE_UPLOAD_MAX_MEMORY_SIZE (default: 2.5 MB) as a
TemporaryUploadedFile on disk.
https://docs.djangoproject.com/en/5.2/topics/http/file-uploads/#where-uploaded-data-is-stored

Errors could occur if the code takes wrong assumptions about the file location.
See https://github.com/spdx/spdx-online-tools/issues/499

Setting the threshold to 0 forces every upload through file on disk path.
"""

import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from api.models import CompareFileUpload, ConvertFileUpload, ValidateFileUpload


def getExamplePath(filename):
    return os.path.join(settings.EXAMPLES_DIR, filename)


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
        self.tearDown()


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
        self.tearDown()


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
        self.tearDown()
