# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework.test import APITestCase,APIClient
from rest_framework.authtoken.models import Token

from models import ValidateFileUpload,ConvertFileUpload,CompareFileUpload

class ValidateFileUploadTests(APITestCase):
    # def setUp(self):
    # 	self.username : "validateapitestuser"
    # 	self.password : "validateapitestpass"
    #     self.tearDown()
    #     self.credentials = {'username':self.username,'password':self.password }
    #     u = User.objects.create_user(**self.credentials)
    #     u.save()
    #     #
    #     user = User.objects.get_or_create(**self.credentials)     # Staff

    def tearDown(self):
        ValidateFileUpload.objects.all().delete()

    def _create_test_file(self, path):
        f = open(path, 'w')
        f.write('test123\n')
        f.close()
        f = open(path, 'rb')
        return {'file': f}

    def test_upload_file(self):
    	self.tearDown()
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        resp = self.client.post(reverse("validate-api"), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('created', response.data)
        self.assertTrue(urlparse(
            response.data['file']).path.startswith(settings.MEDIA_URL))
        self.assertEqual(response.data['owner'],
                       User.objects.get_by_natural_key('test').id)
        self.assertIn('created', response.data)

        # assert unauthenticated user can not upload file
        client.logout()
        response = client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
