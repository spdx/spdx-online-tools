# -*- coding: utf-8 -*-


from django.test import TestCase
from django.urls import reverse

class LicenseRequestsViewsTestCase(TestCase):

    def test_license_requests(self):
        """GET Request for license requests list"""
        resp = self.client.get(reverse("license-requests"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/license_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseRequests")