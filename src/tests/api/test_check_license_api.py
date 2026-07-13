# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for Check License API.
"""

import json
from unittest import skipIf

import redis as redis_lib
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from rest_framework.test import APITestCase

from tests.test_helpers import getExamplePath
from src.secret import getRedisHost


def isRedisAvailable():
    try:
        r = redis_lib.StrictRedis(host=getRedisHost(), port=6379, db=0)
        r.ping()
        return True
    except (redis_lib.exceptions.ConnectionError, Exception):
        return False


@skipIf(not isRedisAvailable(), "Redis is not available")
class CheckLicenseFileUploadTests(APITestCase):

    def setUp(self):
        self.username = "checklicenseapitestuser"
        self.password = "checklicenseapitestpass"
        self.tearDown()
        self.credentials = {"username": self.username, "password": self.password}
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.license = "AFL-1.1"
        self.license_file = open(getExamplePath("AFL-1.1.txt"))
        self.addCleanup(self.license_file.close)
        self.other_file = open(getExamplePath("Other.txt"))
        self.addCleanup(self.other_file.close)

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass

    def test_checklicense_api(self):
        """Access get without login"""
        resp1 = self.client.get(reverse("check_license-api"))
        self.assertEqual(resp1.status_code, 405)
        self.client.login(username=self.username, password=self.password)
        """ Access get after login"""
        resp2 = self.client.get(reverse("check_license-api"))
        self.assertEqual(resp2.status_code, 405)
        """ Valid License File"""
        resp3 = self.client.post(
            reverse("check_license-api"),
            {"file": self.license_file},
            format="multipart",
        )
        self.assertEqual(resp3.status_code, 200)
        result3 = json.loads(resp3.content)
        self.assertEqual(result3["matched_license"], self.license)
        self.assertEqual(result3["match_type"], "Perfect match")
        self.assertEqual(result3["all_matches"], {self.license: 1.0})
        """ Other File"""
        resp4 = self.client.post(
            reverse("check_license-api"), {"file": self.other_file}, format="multipart"
        )
        self.assertEqual(resp4.status_code, 404)
        result4 = json.loads(resp4.content)
        self.assertEqual(result4["matched_license"], None)
        self.assertEqual(result4["match_type"], "No match")
        self.assertEqual(result4["all_matches"], {})

    def test_checklicense_without_argument(self):
        self.client.login(username=self.username, password=self.password)
        resp5 = self.client.post(reverse("check_license-api"), {}, format="multipart")
        self.assertEqual(resp5.status_code, 400)
        self.client.logout()
