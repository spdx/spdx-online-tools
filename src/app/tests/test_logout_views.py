# -*- coding: utf-8 -*-


from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse


from django.contrib.auth.models import User
from django.conf import settings
import os


class LogoutViewsTestCase(TestCase):

    def test_logout(self):
        self.client.force_login(User.objects.get_or_create(username='logouttestuser')[0])
        resp = self.client.get(reverse("logout"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))