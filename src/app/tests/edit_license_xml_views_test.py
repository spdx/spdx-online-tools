# -*- coding: utf-8 -*-


from django.test import TestCase
from django.urls import reverse


from app.models import LicenseRequest


class EditLicenseXmlViewsTestCase(TestCase):
    def test_edit_license_xml(self):
        """View for editing the xml of a license, given its id"""
        license_obj = LicenseRequest.objects.create(fullname="BSD Zero Clause License-00", shortIdentifier="0BSD")
        license_id = license_obj.id
        resp = self.client.get(reverse("license_xml_editor", kwargs={'license_id': license_id}),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/editor.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"edit_license_xml")

    def test_error_license_requests_edit_xml(self):
        """Check if error page is displayed when the license id does not exist"""
        license_id = 0
        resp = self.client.get(reverse("license_xml_editor", kwargs={'license_id': license_id}),follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("404.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"edit_license_xml")

    def test_no_license_id_on_license_requests_edit_xml(self):
        """Check if the redirect works if no license id is provided in the url"""
        resp = self.client.get(reverse("license_xml_editor_none"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn("app/license_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseRequests")