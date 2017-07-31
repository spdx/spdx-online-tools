# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from rest_framework.test import APITestCase
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from models import FileUpload
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

class FileUploadTests(APITestCase):

    def setUp(self):
        self.tearDown()
        u = User.objects.create_user('test', password='test',
                                     email='test@test.test')
        u.save()

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key('test')
            u.delete()

        except ObjectDoesNotExist:
            pass
        FileUpload.objects.all().delete()

    def _create_test_file(self, path):
        f = open(path, 'w')
        f.write('test123\n')
        f.close()
        f = open(path, 'rb')
        return {'datafile': f}

    def test_upload_file(self):
        url = reverse('file')
        data = self._create_test_file('/tmp/test_upload')

        # assert authenticated user can upload file
        token = Token.objects.get(user__username='test')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('created', response.data)
        self.assertTrue(urlparse(
            response.data['datafile']).path.startswith(settings.MEDIA_URL))
        self.assertEqual(response.data['owner'],
                       User.objects.get_by_natural_key('test').id)
        self.assertIn('created', response.data)

        # assert unauthenticated user can not upload file
        client.logout()
        response = client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
