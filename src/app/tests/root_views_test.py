# -*- coding: utf-8 -*-


from django.test import TestCase
from django.conf import settings
from django.urls import reverse


from django.conf import settings
import os

class RootViewsTestCase(TestCase):

    def test_root_url(self):
        resp = self.client.get(reverse("root"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn(settings.HOME_URL, (i[0] for i in resp.redirect_chain))
