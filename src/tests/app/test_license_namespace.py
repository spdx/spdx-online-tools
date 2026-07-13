# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for skipped license namespace views (issue #337).
"""

from unittest import skip, skipIf
from django.test import TestCase, tag
from django.urls import reverse

from selenium.webdriver.common.by import By

from app.generateXml import generateLicenseXml
from app.models import LicenseNamespace
from tests.test_helpers import (
    BaseSeleniumTestCase,
    GitHubLoginMixin,
    SELENIUM_AVAILABLE,
    getAccessToken,
    getGithubUserId,
    getGithubUserName,
)


@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
class LicenseNamespaceViewsTestCase(TestCase):

    def test_license_requests(self):
        """GET Request for license requests list"""
        resp = self.client.get(reverse("license-namespace-requests"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/license_namespace_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseNamespaceRequests")


@tag("selenium")
@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
@skipIf(not SELENIUM_AVAILABLE, "Selenium not available (Firefox or Chrome required)")
class PromoteLicenseNamespaceViewsTestCase(GitHubLoginMixin, BaseSeleniumTestCase):

    def setUp(self):
        super(PromoteLicenseNamespaceViewsTestCase, self).setUp()
        login = self.githubLogin()
        self.assertTrue(login)

    @skipIf(not getAccessToken() or not getGithubUserId() or not getGithubUserName(), "You need to set GitHub parameters in the secret.py file for this test to be executed properly.")
    def test_promote_license_namespace_feature(self):
        """Check if the license namespace is promoted when the promote action is taken"""
        # GitHub access token,id and username should be added in .env to execute the test properly
        driver = self.selenium
        driver.get(self.live_server_url+'/app/license_namespace_requests/')
        table_contents = driver.find_element(By.CSS_SELECTOR, 'tbody').text
        self.assertEqual(table_contents, "No data available in table")
        xml = generateLicenseXml('', "0BSD", "BSD Zero Clause License-00",
            '', ["http://wwww.spdx.org"], '', '', '')
        license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00",
                                                      licenseAuthorName="John Doe",
                                                      shortIdentifier="0BSD",
                                                      archive="False",
                                                      promoted="False",
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
        license_name = driver.find_element(By.CSS_SELECTOR, 'td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).promoted, False)

        resp = self.client.post(reverse("promoted-license-namespace-xml"),
                                {"promoted": True, "license_id": license_obj.id},
                                follow=True,
                                secure=True,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])


@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
class ArchiveLicenseNamespaceViewsTestCase(TestCase):

    def test_archive_license_requests(self):
        """GET Request for archive license namespace requests list"""
        resp = self.client.get(reverse("archive-license-namespace-xml"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/license_namespace_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"archiveLicenseNamespace")


@tag("selenium")
@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
@skipIf(not SELENIUM_AVAILABLE, "Selenium not available (Firefox or Chrome required)")
class ArchiveLicenseNamespaceSeleniumTestCase(GitHubLoginMixin, BaseSeleniumTestCase):

    def setUp(self):
        super(ArchiveLicenseNamespaceSeleniumTestCase, self).setUp()
        login = self.githubLogin()
        self.assertTrue(login)

    @skipIf(not getAccessToken() or not getGithubUserId() or not getGithubUserName(), "You need to set GitHub parameters in the secret.py file for this test to be executed properly.")
    def test_archive_license_requests_feature(self):
        """Check if the license requests is archived when the archive action is taken"""
        # GitHub access token,id and username should be added in .env to execute the test properly
        driver = self.selenium
        driver.get(self.live_server_url+'/app/license_namespace_requests/')
        table_contents = driver.find_element(By.CSS_SELECTOR, 'tbody').text
        self.assertEqual(table_contents, "No data available in table")
        xml = generateLicenseXml('', "0BSD", "BSD Zero Clause License-00",
            '', ["http://wwww.spdx.org"], '', '', '')
        license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00",
                                                      licenseAuthorName="John Doe",
                                                      shortIdentifier="0BSD",
                                                      archive="False",
                                                      promoted="False",
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
        license_name = driver.find_element(By.CSS_SELECTOR, 'td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).archive, False)

        resp = self.client.post(reverse("archive-license-namespace-xml"),
                                {"archive": True, "license_id": license_obj.id},
                                follow=True,
                                secure=True,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])


@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
class SubmitNewLicenseNamespaceViewsTestCase(TestCase):

    def test_submit_new_license_xml(self):
        """POST Request for submitting new license namespace xml"""
        resp = self.client.post(reverse("submit-new-license-namespace-xml"),{},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertEqual(resp.content, b"No XML file content.")
        self.assertEqual(resp.redirect_chain,[])

        xml = generateLicenseXml('', "0BSD", "BSD Zero Clause License-00",
            '', ["http://wwww.spdx.org"], '', '', '')
        license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00",
                                                      licenseAuthorName="John Doe",
                                                      shortIdentifier="0BSD",
                                                      archive="False",
                                                      promoted="False",
                                                      url="http://wwww.spdx.org",
                                                      description="Description",
                                                      notes="Notes",
                                                      namespace="bsd-zero-clause-license-00",
                                                      userEmail="johndoe@gmail.com",
                                                      publiclyShared="True",
                                                      license_list_url="http://wwww.spdx.org",
                                                      github_repo_url="http://wwww.spdx.org",
                                                      xml=xml)
        resp2 = self.client.post(reverse("submit-new-license-namespace-xml"),
                                 {'xmlfile': xml, 'license_id': license_obj.id},
                                 follow=True,
                                 secure=True,
                                 HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])


@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
class EditLicenseNamespaceXmlViewsTestCase(TestCase):

    def test_edit_license_xml(self):
        """View for editing the xml of a license namespace, given its id"""
        license_obj = LicenseNamespace.objects.create(fullname="BSD Zero Clause License-00", shortIdentifier="0BSD")
        license_id = license_obj.id
        resp = self.client.get(reverse("license_namespace_xml_editor", kwargs={'license_id': license_id}),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/ns_editor.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"edit_license_namespace_xml")

    def test_error_license_requests_edit_xml(self):
        """Check if error page is displayed when the license namespace id does not exist"""
        license_id = 0
        resp = self.client.get(reverse("license_namespace_xml_editor", kwargs={'license_id': license_id}),follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("404.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"edit_license_namespace_xml")

    def test_no_license_id_on_license_requests_edit_xml(self):
        """Check if the redirect works if no license namespace id is provided in the url"""
        resp = self.client.get(reverse("license_namespace_xml_editor_none"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn("app/license_namespace_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseNamespaceRequests")
