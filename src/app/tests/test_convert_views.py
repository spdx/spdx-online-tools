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

class ConvertViewsTestCase(TestCase):

    def test_convert(self):
        """GET Request for convert"""
        if not settings.ANONYMOUS_LOGIN_ENABLED :
            resp = self.client.get(reverse("convert"),follow=True,secure=True)
            self.assertEqual(resp.status_code,200)
            self.assertNotEqual(resp.redirect_chain,[])
            self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        resp2 = self.client.get(reverse("convert"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertIn("app/convert.html",(i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__,"convert")
        self.client.logout()

    def test_convert_tagtordf(self):
        """POST Request for convert tag to rdf"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        resp = self.client.post(reverse("convert"),{'cfilename': "tagtest" ,'cfileformat': ".rdf.xml",'from_format' : "TAG", 'to_format' : "RDFXML", 'file' : self.tv_file},follow=True,secure=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/rdf+xml")
        self.tv_file.close()
        self.client.logout()

    def test_convert_tagtoxlsx(self):
        """POST Request for convert tag to spreadsheet"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        resp = self.client.post(reverse("convert"),{'cfilename': "tagtest" ,'cfileformat': ".xlsx",'from_format' : "TAG", 'to_format' : "XLSX", 'file' : self.tv_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/vnd.ms-excel")
        self.tv_file.close()
        self.client.logout()

    def test_convert_rdftotag(self):
        """POST Request for convert rdf to tag"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".spdx",'from_format' : "RDFXML", 'to_format' : "TAG", 'file' : self.rdf_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"text/tag-value")
        self.rdf_file.close()
        self.client.logout()

    def test_convert_rdftoxlsx(self):
        """POST Request for convert rdf to spreadsheet"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".xls",'from_format' : "RDFXML", 'to_format' : "XLS", 'file' : self.rdf_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/vnd.ms-excel")
        self.rdf_file.close()
        self.client.logout()

    def test_convert_xlsxtotag(self):
        """POST Request for convert spreadsheet to tag"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.xls_file = open("examples/SPDXSpreadsheetExample-2.0.xls", "rb")
        resp = self.client.post(reverse("convert"),{'cfilename': "xlsxtest" ,'cfileformat': ".spdx",'from_format' : "XLS", 'to_format' : "TAG", 'file' : self.xls_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"text/tag-value")
        self.xls_file.close()
        self.client.logout()

    def test_convert_xlsxtordf(self):
        """POST Request for convert spreadsheet to rdf"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.xls_file = open("examples/SPDXSpreadsheetExample-2.0.xls", "rb")
        resp = self.client.post(reverse("convert"),{'cfilename': "xlsxtest" ,'cfileformat': ".rdf",'from_format' : "XLS", 'to_format' : "RDFXML", 'file' : self.xls_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/rdf+xml")
        self.xls_file.close()
        self.client.logout()

    def test_other_convert_formats(self):
        """POST Request for converting invalid formats"""
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.xls_file = open(getExamplePath("SPDXSpreadsheetExample-2.0.xls"), "rb")
        resp = self.client.post(reverse("convert"),{'cfilename': "xlsxtest" ,'cfileformat': ".html",'from_format' : "Spreadsheet", 'to_format' : "HTML", 'file' : self.xls_file},follow=True)
        self.assertEqual(resp.status_code,400)
        self.assertIn("error", resp.context)
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.0.rdf"), "rb")
        resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".pdf",'from_format' : "RDF", 'to_format' : "PDF", 'file' : self.rdf_file},follow=True)
        self.assertEqual(resp.status_code,400)
        self.assertIn("error", resp.context)
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"), "rb")
        resp = self.client.post(reverse("convert"),{'cfilename': "tagtest" ,'cfileformat': ".txt",'from_format' : "Tag", 'to_format' : "text", 'file' : self.tv_file},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertIn("error", resp.context)
        self.client.logout()