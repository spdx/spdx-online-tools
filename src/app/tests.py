# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.contrib.auth.models import User

import jpype
# Create your tests here.

class IndexViewsTestCase(TestCase):
    def test_index(self):
        resp = self.client.get('/app/')
        self.assertEqual(resp.status_code,200)

class AboutViewsTestCase(TestCase):
    def test_about(self):
        resp = self.client.get('/app/about/')
        self.assertEqual(resp.status_code,200)

class ValidateViewsTestCase(TestCase):
    def setUp(self):
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        self.invalid_tv_file = open("examples/SPDXTagExample-v2.0_invalid.spdx")
        self.invalid_rdf_file = open("examples/SPDXRdfExample-v2.0_invalid.rdf")
        self.other_file = open("examples/Other.txt")
    
    def test_validate(self):
        resp = self.client.get('/app/validate/')
        self.assertEqual(resp.status_code,200)

    def test_upload_tv(self):
        resp = self.client.post('/app/validate/',{'file' : self.tv_file},follow=True)
        self.assertEqual(resp.content,"This SPDX Document is valid.")
    
    def test_upload_rdf(self):
        resp = self.client.post('/app/validate/',{'file' : self.rdf_file},follow=True)
        self.assertEqual(resp.content,"This SPDX Document is valid.")
    
    def test_upload_other(self):
        resp = self.client.post('/app/validate/',{'file' : self.other_file},follow=True)
        self.assertTrue(resp.context['error'])

    def test_upload_inv_tv(self):
        resp = self.client.post('/app/validate/',{'file' : self.invalid_tv_file},follow=True)
        self.assertTrue(resp.context['error'])

    def test_upload_inv_rdf(self):
        resp = self.client.post('/app/validate/',{'file' : self.invalid_rdf_file},follow=True)
        self.assertTrue(resp.context['error'])


class CompareViewsTestCase(TestCase):
    def setUp(self):
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        self.rdf_file2 = open("examples/SPDXRdfExample2-v2.0.rdf")
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")

    def test_compare(self):
        resp = self.client.get('/app/compare/')
        self.assertEqual(resp.status_code,200)

    def test_compare_two_rdf(self):
        resp = self.client.post('/app/compare/',{'nofile': "2" ,'rfilename': "test",'file1' : self.rdf_file, 'file2' : self.rdf_file2},follow=True)
        print "here"
        print resp
        print resp.status_code
    
    
class ConvertViewsTestCase(TestCase):
    def test_convert(self):
        resp = self.client.get('/app/convert/')
        self.assertEqual(resp.status_code,200)

class SearchViewsTestCase(TestCase):
    def test_search(self):
        resp = self.client.get('/app/search/')
        self.assertEqual(resp.status_code,200)

class LoginViewsTestCase(TestCase):
    def setUp(self):
        self.credentials = {'username':'testuser','password':'testpass' }
        user = User.objects.create_user(**self.credentials)
        #A staff user
        user.is_staff = True
        user.save()
        self.credentials2 = {'username':'testuser2','password':'testpass2' }
        #An anonymous user
        user2 = User.objects.create_user(**self.credentials2)

    def test_login(self):
        resp = self.client.get('/app/login/')
        self.assertEqual(resp.status_code,200)

    def test_postlogin(self):
        resp = self.client.post('/app/login/',self.credentials,follow=True)
        self.assertTrue(resp.context['user'].is_active)
        self.client.get('/app/logout/')
        resp = self.client.post('/app/login/',self.credentials2,follow=True)
        self.assertFalse(resp.context['user'].is_active)

class RegisterViewsTestCase(TestCase):
    def test_register(self):
        resp = self.client.get('/app/register/')
        self.assertEqual(resp.status_code,200)
        self.assertTrue('user_form' in resp.context)
        self.assertTrue('profile_form' in resp.context)

    def test_formregister(self):
        self.data = {"first_name": "test","last_name" : "test" ,
            "email" : "test@spdx.org","username":"testuser3",
            "password":"testpass3","confirm_password":"testpass3","organisation":"spdx"}
        resp = self.client.post('/app/register/',self.data,follow=True)
        self.assertEqual(resp.status_code,200)
        resp = self.client.post('/app/login/',{'username':'testuser3','password':'testpass3'},follow=True)
        self.assertTrue(resp.context['user'].is_active)


class LogoutViewsTestCase(TestCase):
    def test_logout(self):
        resp = self.client.get('/app/logout/')
        # For Url Redirection to index after logout
        self.assertEqual(resp.status_code,302)

class RootViewsTestCase(TestCase):
    def test_logout(self):
        resp = self.client.get('/')
        # For View Redirection to index
        self.assertEqual(resp.status_code,302)
