# -*- coding: utf-8 -*-


from django.urls import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

from app.models import LicenseNamespace
from app.generateXml import generateLicenseXml



class ArchiveLicenseNamespaceViewsTestCase(StaticLiveServerTestCase):

    def setUp(self):
        options = Options()
        options.add_argument('-headless')
        self.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_options=options)
        super(ArchiveLicenseNamespaceViewsTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(ArchiveLicenseNamespaceViewsTestCase, self).tearDown()

    def test_archive_license_requests(self):
        """GET Request for archive license namespace requests list"""
        resp = self.client.get(reverse("archive-license-namespace-xml"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/archive_namespace_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"archiveNamespaceRequests")

    def test_error_archive_license_namespace(self):
        """Check if error page is displayed when the license id does not exist for archive license namespace"""
        license_id = 0
        resp = self.client.get(reverse("archived-license-namespace-information", args=(license_id,)),follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("404.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseNamespaceInformation")

    def test_archive_license_namespace_feature(self):
        """Check if the license namespace is shifted to archive namespace when archive button is pressed"""
        driver = self.selenium
        driver.get(self.live_server_url+'/app/license_namespace_requests/')
        table_contents = driver.find_element_by_css_selector('tbody').text
        self.assertEqual(table_contents, "No data available in table")
        xml = generateLicenseXml('', "0BSD", "BSD Zero Clause License-00",
            '', "http://wwww.spdx.org", '', '', '')
        license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00",
                                                      licenseAuthorName="John Doe",
                                                      shortIdentifier="0BSD",
                                                      archive="False",
                                                      url="http://wwww.spdx.org",
                                                      description="Description",
                                                      notes="Notes",
                                                      namespace="bsd-zero-clause-license-00",
                                                      userEmail="johndoe@gmail.com",
                                                      publiclyShared="True",
                                                      license_list_url="http://wwww.spdx.org",
                                                      github_repo_url="http://wwww.spdx.org",
                                                      xml=xml)
        driver.refresh()
        license_name = driver.find_element_by_css_selector('td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).archive, False)
        driver.find_element_by_id('archive_button' + str(license_obj.id)).click()
        driver.find_element_by_id('confirm_archive').click()
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).archive, True)

    def test_unarchive_license_namespace_feature(self):
        """Check if license namespace is shifted back to license namespace when unarchive button is pressed"""
        driver = self.selenium
        driver.get(self.live_server_url+'/app/archive_namespace_requests/')
        table_contents = driver.find_element_by_css_selector('tbody').text
        self.assertEqual(table_contents, "No data available in table")
        archive_license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00",
                                                              licenseAuthorName="John Doe",
                                                              shortIdentifier="0BSD",
                                                              archive="True",
                                                              url="http://wwww.spdx.org",
                                                              description="Description",
                                                              notes="Notes",
                                                              namespace="bsd-zero-clause-license-00",
                                                              userEmail="johndoe@gmail.com",
                                                              publiclyShared="True",
                                                              license_list_url="http://wwww.spdx.org",
                                                              github_repo_url="http://wwww.spdx.org")
        driver.refresh()
        license_name = driver.find_element_by_css_selector('td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=archive_license_obj.id).archive, True)
        driver.find_element_by_id('unarchive_button' + str(archive_license_obj.id)).click()
        driver.find_element_by_id('confirm_unarchive').click()
        self.assertEqual(LicenseNamespace.objects.get(id=archive_license_obj.id).archive, False)