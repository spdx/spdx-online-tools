# -*- coding: utf-8 -*-


from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse


from app.models import UserID
from django.contrib.auth.models import User
from django.conf import settings
import os


class ProfileViewsTestCase(TestCase):

    def initialise(self):
        self.username = "profiletestuser"
        self.password ="profiletestpass"
        self.credentials = {"first_name": "test","last_name" : "test" ,"email" : "profiletest@spdx.org",'username':self.username,'password':self.password }
        self.user = User.objects.create_user(**self.credentials)
        UserID.objects.get_or_create({"user":self.user,"organisation":"spdx"})

    def test_profile(self):
        """GET Request for profile"""
        resp = self.client.get(reverse("profile"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='profiletestuser')[0])

        resp2 = self.client.get(reverse("profile"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertIn("app/profile.html",(i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__,"profile")
        self.assertIn("form",resp2.context)
        self.assertIn("info_form",resp2.context)
        self.assertIn("orginfo_form",resp2.context)
        self.client.logout()

    def test_saveinfo(self):
        """POST Request for saving information"""
        self.initialise()
        user = User.objects.get_or_create(username='profiletestuser')[0]
        userid = UserID.objects.get_or_create(user=user)[0]
        self.assertEqual(user.first_name,"test")
        self.assertEqual(user.last_name,"test")
        self.assertEqual(user.email,"profiletest@spdx.org")
        self.assertEqual(userid.organisation,"spdx")
        self.client.force_login(user)

        save_info_resp = self.client.post(reverse("profile"),{'saveinfo':'saveinfo',"first_name": "john","last_name" : "doe" ,"email" : "johndoe@spdx.org","organisation":"Software Package Data Exchange"},follow=True,secure=True)
        self.assertEqual(save_info_resp.status_code,200)
        self.assertEqual(save_info_resp.redirect_chain,[])
        self.assertEqual(save_info_resp.context["success"],"Details Successfully Updated")
        user = User.objects.get_or_create(username='profiletestuser')[0]
        userid = UserID.objects.get_or_create(user=user)[0]
        self.assertEqual(user.first_name,"john")
        self.assertEqual(user.last_name,"doe")
        self.assertEqual(user.email,"johndoe@spdx.org")
        self.assertEqual(userid.organisation,"Software Package Data Exchange")
        self.client.logout()

    def test_changepwd(self):
        """POST Request for changing password"""
        self.initialise()
        resp = self.client.login(username='profiletestuser', password='profiletestpass')
        self.assertTrue(resp)
        change_pwd_resp = self.client.post(reverse("profile"),{'changepwd':'changepwd',"old_password": self.password,"new_password1" : "johndoepass" ,"new_password2" : "johndoepass"},follow=True,secure=True)
        self.assertEqual(change_pwd_resp.status_code,200)
        self.assertEqual(change_pwd_resp.redirect_chain,[])
        self.assertEqual(change_pwd_resp.context["success"],"Your password was successfully updated!")
        self.client.logout()

        resp2 = self.client.login(username='profiletestuser', password='profiletestpass')
        self.assertFalse(resp2)

        resp3 = self.client.login(username='profiletestuser', password='johndoepass')
        self.assertTrue(resp3)
        self.client.logout()