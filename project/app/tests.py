# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

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
	def test_login(self):
		resp = self.client.get('/app/login/')
		self.assertEqual(resp.status_code,200)
	
class RegisterViewsTestCase(TestCase):
	def test_register(self):
		resp = self.client.get('/app/register/')
		self.assertEqual(resp.status_code,200)
