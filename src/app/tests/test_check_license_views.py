# -*- coding: utf-8 -*-


from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse


from django.contrib.auth.models import User
from django.conf import settings
import os


def getExamplePath(filename):
    return os.path.join(settings.EXAMPLES_DIR, filename)

class CheckLicenseViewsTestCase(TestCase):

    def setUp(self):
        self.licensefile = open(getExamplePath("AFL-1.1.txt"))
        self.licensetext = self.licensefile.read()

    def test_check_license(self):
        """GET Request for check license"""
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            resp = self.client.get(reverse("check-license"),follow=True,secure=True)
            self.assertEqual(resp.status_code,200)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
            self.client.force_login(User.objects.get_or_create(username='checklicensetestuser')[0])
        resp2 = self.client.get(reverse("check-license"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertIn("app/check_license.html",(i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__,"check_license")
        self.client.logout()

    # def test_post_check_license(self):
    #     self.client.force_login(User.objects.get_or_create(username='checklicensetestuser')[0])
    #     resp = self.client.post(reverse("check-license"),{'licensetext': self.licensetext},follow=True)
    #     self.assertEqual(resp.status_code,200)
    #     self.assertIn("success",resp.context)
    #     self.client.logout()