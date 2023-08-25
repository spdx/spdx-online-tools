# -*- coding: utf-8 -*-


from django.test import TestCase
from django.urls import reverse

class IndexViewsTestCase(TestCase):

    def test_index(self):
        """GET Request for index"""
        resp = self.client.get(reverse("index"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/index.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"index")