# -*- coding: utf-8 -*-


from django.test import TestCase
from django.conf import settings
from django.urls import reverse


from django.conf import settings
import os

class RegisterViewsTestCase(TestCase):

    def initialise(self):
        self.username = "testuser4"
        self.password ="testpass4"
        self.data = {"first_name": "test","last_name" : "test" ,
            "email" : "test@spdx.org","username":self.username,
            "password":self.password,"confirm_password":self.password,"organisation":"spdx"}

    def test_register(self):
        """GET Request for register"""
        resp = self.client.get(reverse("register"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertTrue('user_form' in resp.context)
        self.assertTrue('profile_form' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/register.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"register")

    def test_formregister(self):
        """POST Request for register"""
        self.initialise()
        resp = self.client.post(reverse("register"),self.data,follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.REGISTER_REDIRECT_UTL, (i[0] for i in resp.redirect_chain))

        loginresp = self.client.post(reverse("login"),{'username':self.username,'password':self.password},follow=True,secure=True)
        self.assertEqual(loginresp.status_code,200)
        self.assertTrue(loginresp.context['user'].is_active)
        self.assertTrue(loginresp.context['user'].is_staff)
        self.assertFalse(loginresp.context['user'].is_superuser)
        self.assertIn(settings.LOGIN_REDIRECT_URL, (i[0] for i in loginresp.redirect_chain))
        self.client.get(reverse("logout"))