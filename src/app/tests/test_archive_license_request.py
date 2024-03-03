# -*- coding: utf-8 -*-


from unittest import skipIf
from src.secret import getAccessToken, getGithubUserId, getGithubUserName
from django.urls import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

from app.models import LicenseRequest


class ArchiveLicenseRequestsViewsTestCase(StaticLiveServerTestCase):

    def setUp(self):
        options = Options()
        options.add_argument('-headless')
        self.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_options=options)
        super(ArchiveLicenseRequestsViewsTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(ArchiveLicenseRequestsViewsTestCase, self).tearDown()

    def test_archive_license_requests(self):
        """GET Request for archive license requests list"""
        resp = self.client.get(reverse("archive-license-xml"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/archive_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"archiveRequests")

    def test_error_archive_license_requests(self):
        """Check if error page is displayed when the license id does not exist for archive license"""
        license_id = 0
        resp = self.client.get(reverse("archived-license-information", args=(license_id,)),follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("404.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseInformation")

    @skipIf(not getAccessToken() and not getGithubUserId() and not getGithubUserName(), "You need to set gihub parameters in the secret.py file for this test to be executed properly.")
    def test_archive_license_requests_feature(self):
        """Check if the license is shifted to archive requests when archive button is pressed"""
        driver = self.selenium
        driver.get(self.live_server_url+'/app/license_requests/')
        table_contents = driver.find_element_by_css_selector('tbody').text
        self.assertEqual(table_contents, "No data available in table")
        license_obj = LicenseRequest.objects.create(fullname="BSD Zero Clause License-00", shortIdentifier="0BSD")
        driver.refresh()
        license_name = driver.find_element_by_css_selector('td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseRequest.objects.get(id=license_obj.id).archive, False)
        if driver.find_element_by_id('archive_button' + str(license_obj.id)):
            driver.find_element_by_id('archive_button' + str(license_obj.id)).click()
            driver.find_element_by_id('confirm_archive').click()
            self.assertEqual(LicenseRequest.objects.get(id=license_obj.id).archive, True)
        else:
            pass

    @skipIf(not getAccessToken() and not getGithubUserId() and not getGithubUserName(), "You need to set gihub parameters in the secret.py file for this test to be executed properly.")
    def test_unarchive_license_requests_feature(self):
        """Check if license is shifted back to license requests when unarchive button is pressed"""
        driver = self.selenium
        driver.get(self.live_server_url+'/app/archive_requests/')
        table_contents = driver.find_element_by_css_selector('tbody').text
        self.assertEqual(table_contents, "No data available in table")
        archive_license_obj = LicenseRequest.objects.create(fullname="BSD Zero Clause License-00", shortIdentifier="0BSD", archive="True")
        driver.refresh()
        license_name = driver.find_element_by_css_selector('td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseRequest.objects.get(id=archive_license_obj.id).archive, True)
        if driver.find_element_by_id('unarchive_button' + str(archive_license_obj.id)):
            driver.find_element_by_id('unarchive_button' + str(archive_license_obj.id)).click()
            driver.find_element_by_id('confirm_unarchive').click()
            self.assertEqual(LicenseRequest.objects.get(id=archive_license_obj.id).archive, False)
        else:
            pass