# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

from unittest import skip, skipIf

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from social_django.models import UserSocialAuth

from app.generateXml import generateLicenseXml
from app.models import LicenseNamespace
from src.secret import getAccessToken, getGithubUserId, getGithubUserName
from tests.test_helpers import BaseSeleniumTestCase, SELENIUM_AVAILABLE


class TestUtil(TestCase):
    def gitHubLogin(self):
        TEST_LOGIN_INFO = {
            "provider": "github",
            "uid": str(getGithubUserId()),
            "access_token": getAccessToken(),
            "login": getGithubUserName(),
            "id": getGithubUserId(),
            "password": "pass",
        }
        self.user = User.objects.create(username=TEST_LOGIN_INFO["login"],
                                        is_active=True,
                                        is_superuser=True)
        self.user.set_password(TEST_LOGIN_INFO["password"])
        self.user.save()
        UserSocialAuth.objects.create(provider=TEST_LOGIN_INFO["provider"],
                                      uid=TEST_LOGIN_INFO["uid"],
                                      extra_data=TEST_LOGIN_INFO,
                                      user=self.user)
        self.user = authenticate(username=TEST_LOGIN_INFO["login"],
                                 password=TEST_LOGIN_INFO["password"])
        login = self.client.login(username=TEST_LOGIN_INFO["login"],
                                  password=TEST_LOGIN_INFO["password"])
        return login





@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
class LicenseNamespaceViewsTestCase(TestCase):

    def test_license_requests(self):
        """GET Request for license requests list"""
        resp = self.client.get(reverse("license-namespace-requests"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/license_namespace_requests.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"licenseNamespaceRequests")


# @skipIf is intentionally kept alongside the BaseSeleniumTestCase.setUp check to skip
# the class before any fixtures are set up, which is faster.
@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
@skipIf(not SELENIUM_AVAILABLE, "Selenium not available (Firefox or Chrome required)")
class PromoteLicenseNamespaceViewsTestCase(BaseSeleniumTestCase):

    def setUp(self):
        super(PromoteLicenseNamespaceViewsTestCase, self).setUp()
        login = TestUtil.gitHubLogin(self)
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


# @skipIf is intentionally kept alongside the BaseSeleniumTestCase.setUp check to skip
# the class before any fixtures are set up, which is faster.
@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
@skipIf(not SELENIUM_AVAILABLE, "Selenium not available (Firefox or Chrome required)")
class ArchiveLicenseNamespaceSeleniumTestCase(BaseSeleniumTestCase):

    def test_archive_license_namespace_feature(self):
        """Check if the license namespace is shifted to archive namespace when archive button is pressed"""
        driver = self.selenium
        driver.get(self.live_server_url+'/app/license_namespace_requests/')
        table_contents = driver.find_element(By.CSS_SELECTOR, 'tbody').text
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
        license_name = driver.find_element(By.CSS_SELECTOR, 'td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).archive, False)
        driver.find_element(By.ID, 'archive_button' + str(license_obj.id)).click()
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'confirm_archive')))
        driver.find_element(By.ID, 'confirm_archive').click()
        WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'tbody'), "No data available in table")
        )
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).archive, True)

    def test_unarchive_license_namespace_feature(self):
        """Check if license namespace is shifted back to license namespace when unarchive button is pressed"""
        driver = self.selenium
        driver.get(self.live_server_url+'/app/archive_namespace_requests/')
        table_contents = driver.find_element(By.CSS_SELECTOR, 'tbody').text
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
        license_name = driver.find_element(By.CSS_SELECTOR, 'td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=archive_license_obj.id).archive, True)
        driver.find_element(By.ID, 'unarchive_button' + str(archive_license_obj.id)).click()
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'confirm_unarchive')))
        driver.find_element(By.ID, 'confirm_unarchive').click()
        WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'tbody'), "No data available in table")
        )
        self.assertEqual(LicenseNamespace.objects.get(id=archive_license_obj.id).archive, False)


@skip("URLs disabled: license namespace not accepted into SPDX spec (see issue #337)")
class SubmitNewLicenseNamespaceViewsTestCase(TestCase):

    def initialise(self):
        self.fullname = "BSD Zero Clause License"
        self.shortIdentifier = "0BSD"
        self.sourceUrl = "http://landley.net/toybox/license.html"
        self.license_list_url = self.sourceUrl
        self.github_repo_url = self.sourceUrl
        self.osiApproved = "Unknown"
        self.comments = ""
        self.notes = ""
        self.licenseHeader = ""
        self.text ='<text> <copyrightText> <p>Copyright (C) 2006 by Rob Landley &lt;rob@landley.net&gt;</p> </copyrightText> <p>Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.</p> <p>THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.</p> </text>'
        self.userEmail = "test@mail.com"
        self.licenseAuthorName = "John Doe"
        self.listVersionAdded = ""
        self.namespace = "j-d-ns"
        self.xml = '<SPDXLicenseCollection xmlns="http://www.spdx.org/license"> <license isOsiApproved="false" licenseId="0BSD" listVersionAdded="" name="BSD Zero Clause License"> <crossRefs> <crossRef> http://landley.net/toybox/license.html</crossRef> </crossRefs> <standardLicenseHeader /> <notes /> <text> <p> &lt;text&gt; &lt;copyrightText&gt; &lt;p&gt;Copyright (C) 2006 by Rob Landley &amp;lt;rob@landley.net&amp;gt;&lt;/p&gt; &lt;/copyrightText&gt; &lt;p&gt;Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.&lt;/p&gt; &lt;p&gt;THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.&lt;/p&gt; &lt;/text&gt;</p> </text> </license> </SPDXLicenseCollection> '
        self.data_no_author = {"fullname": self.fullname, "shortIdentifier": self.shortIdentifier,
                    "url": self.sourceUrl,'osiApproved': self.osiApproved, 'notes': self.notes,
                    "licenseHeader": self.licenseHeader, "text": self.text, "userEmail": self.userEmail,
                    "urlType": "tests", "namespace": self.namespace, "license_list_url": self.license_list_url,
                    "github_repo_url": self.github_repo_url, "licenseAuthorName": self.licenseAuthorName}

    @skip("URL disabled: license namespace not accepted into SPDX spec (see issue #337)")
    def test_submit_new_license_namespace(self):
        """GET Request for submit a new license namespace.

        Note that the license namespace feature is not accepted into the SPDX
        specification, and therefore this URL is disabled.
        The test is skipped to avoid failures.

        See more details in the following links:
        - https://github.com/spdx/spdx-spec/issues/113
        - https://github.com/spdx/spdx-spec/pull/209
        - https://github.com/spdx/spdx-online-tools/issues/337#issuecomment-1504244538
        """
        resp = self.client.get(reverse("submit-new-license-namespace"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/submit_new_license_namespace.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"submitNewLicenseNamespace")
        self.assertIn("form",resp.context)
        self.assertIn("fullname",resp.context["form"].fields)
        self.assertIn("organisation",resp.context["form"].fields)
        self.assertIn("namespace",resp.context["form"].fields)
        self.assertIn("shortIdentifier",resp.context["form"].fields)
        self.assertIn("publiclyShared",resp.context["form"].fields)
        self.assertIn("url",resp.context["form"].fields)
        self.assertIn("license_list_url",resp.context["form"].fields)
        self.assertIn("github_repo_url",resp.context["form"].fields)
        self.assertIn("description",resp.context["form"].fields)
        self.assertIn("licenseAuthorName",resp.context["form"].fields)
        self.assertIn("userEmail",resp.context["form"].fields)

    def test_generate_xml(self):
        """View for generating an xml from license namespace submittal form fields"""
        self.initialise()
        xml = generateLicenseXml(self.osiApproved, self.shortIdentifier, self.fullname, self.listVersionAdded,
                                [self.sourceUrl], self.licenseHeader, self.notes, self.text).replace(">","> ")
        self.assertEqual(self.xml, xml)

    @skip("URL disabled: license namespace not accepted into SPDX spec (see issue #337)")
    @skipIf(not getAccessToken() or not getGithubUserId() or not getGithubUserName(), "You need to set GitHub parameters in the secret.py file for this test to be executed properly.")
    def test_post_submit(self):
        """POST Request for submit a new license namespace.

        Note that the license namespace feature is not accepted into the SPDX
        specification, and therefore this URL is disabled.
        The test is skipped to avoid failures.

        See more details in the following links:
        - https://github.com/spdx/spdx-spec/issues/113
        - https://github.com/spdx/spdx-spec/pull/209
        - https://github.com/spdx/spdx-online-tools/issues/337#issuecomment-1504244538
        """
        login = TestUtil.gitHubLogin(self)
        self.assertTrue(login)
        self.initialise()
        resp = self.client.post(reverse("submit-new-license-namespace"),
                                self.data_no_author,
                                follow=True,
                                secure=True,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])


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


