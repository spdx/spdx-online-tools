# -*- coding: utf-8 -*-


from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse


from django.contrib.auth.models import User
from django.conf import settings
import os


class CheckUserNameTestCase(TestCase):

    def initialise(self):
        self.username = "checktestuser"
        self.password ="checktestpass"
        self.credentials = {'username':self.username,'password':self.password }
        User.objects.create_user(**self.credentials)

    def test_check_username(self):
        """POST Request for checking username"""
        resp = self.client.post(reverse("check-username"),{"username":"spdx"},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)

        resp2 = self.client.post(reverse("check-username"),{"randomkey":"randomvalue"},follow=True,secure=True)
        self.assertEqual(resp2.status_code,400)

        self.initialise()
        resp3 = self.client.post(reverse("check-username"),{"username":"checktestuser"},follow=True,secure=True)
        self.assertEqual(resp3.status_code,404)