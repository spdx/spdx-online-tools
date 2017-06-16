# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.contrib.auth.models import User

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
	def test_validate(self):
		resp = self.client.get('/app/validate/')
		self.assertEqual(resp.status_code,200)
	
class CompareViewsTestCase(TestCase):
	def test_compare(self):
		resp = self.client.get('/app/compare/')
		self.assertEqual(resp.status_code,200)

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
		user.is_staff = True					#A staff user
		user.save()
		self.credentials2 = {'username':'testuser2','password':'testpass2' }
		user2 = User.objects.create_user(**self.credentials2)			#An anonymous user
		#user.is_staff = True	
		#user.save()
		
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
		self.assertEqual(resp.status_code,302)				# For Url Redirection to index after logout
		
class RootViewsTestCase(TestCase):
	def test_logout(self):
		resp = self.client.get('/')
		self.assertEqual(resp.status_code,302)				# For View Redirection to index
