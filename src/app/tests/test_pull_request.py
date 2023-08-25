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



class PullRequestTestCase(TestCase):

    def test_pull_request_get_without_login(self):
        """GET request for pull request feature without login """
        resp = self.client.get(reverse("pull-request"),follow=True,secure=True)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.assertEqual(resp.status_code,200)

    def test_pull_request_get_with_login(self):
        """GET request for pull request feature with login"""
        self.client.force_login(User.objects.get_or_create(username='pullRequestTestUser')[0])
        resp = self.client.get(reverse("pull-request"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.HOME_URL, (i[0] for i in resp.redirect_chain))
        self.assertEqual(resp.resolver_match.func.__name__,"index")
        self.client.logout()

    def test_pull_request_post_with_login(self):
        """POST request for pull request feature with login"""
        self.client.force_login(User.objects.get_or_create(username='pullRequestTestUser')[0])
        resp = self.client.post(reverse("pull-request"),{},follow=True,secure=True)
        self.assertEqual(resp.status_code,401)
        self.assertEqual(resp.redirect_chain,[])
        self.assertEqual(resp.content, b"Please login using GitHub to use this feature.")
        self.client.logout()