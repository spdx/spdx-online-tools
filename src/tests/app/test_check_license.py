# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for Check License views in the Web app.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from tests.test_helpers import getExamplePath


class CheckLicenseViewsTestCase(TestCase):

    def setUp(self):
        self.licensefile = open(getExamplePath("AFL-1.1.txt"))
        self.addCleanup(self.licensefile.close)
        self.licensetext = self.licensefile.read()

    def test_check_license(self):
        """GET Request for check license"""
        if not settings.ANONYMOUS_LOGIN_ENABLED:
            resp = self.client.get(reverse("check-license"), follow=True, secure=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotEqual(resp.redirect_chain, [])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.client.force_login(
                User.objects.get_or_create(username="checklicensetestuser")[0]
            )
        resp2 = self.client.get(reverse("check-license"), follow=True, secure=True)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.redirect_chain, [])
        self.assertIn("app/check_license.html", (i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__, "check_license")
        self.client.logout()
