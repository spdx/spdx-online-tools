# -*- coding: utf-8 -*-


from django.test import TestCase
from django.urls import reverse

class AboutViewsTestCase(TestCase):

    def test_about(self):
        """GET Request for about"""
        resp = self.client.get(reverse("about"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/about.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"about")