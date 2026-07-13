# SPDX-FileContributor: Vedant Jolly
# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for about view.
"""

from django.test import TestCase
from django.urls import reverse


class AboutViewsTestCase(TestCase):
    def test_about(self):
        """GET Request for about"""
        resp = self.client.get(reverse("about"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain, [])
        self.assertIn("app/about.html", (i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__, "about")
