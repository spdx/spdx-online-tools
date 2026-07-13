# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Tests for license requests views and submit new license view.
"""

from unittest import skipIf
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from social_django.models import UserSocialAuth

from app.generateXml import generateLicenseXml
from app.models import LicenseRequest
from src.secret import getAccessToken, getGithubUserId, getGithubUserName
from tests.test_helpers import BaseSeleniumTestCase, SELENIUM_AVAILABLE, GitHubLoginMixin


class PullRequestTestCase(TestCase):

    def test_pull_request_get_without_login(self):
        """GET request for pull request feature without login """
        resp = self.client.get(reverse("pull-request"), follow=True, secure=True)
        self.assertNotEqual(resp.redirect_chain, [])
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.assertEqual(resp.status_code, 200)

    def test_pull_request_get_with_login(self):
        """GET request for pull request feature with login"""
        self.client.force_login(User.objects.get_or_create(username='pullRequestTestUser')[0])
        resp = self.client.get(reverse("pull-request"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.redirect_chain, [])
        self.assertIn(settings.HOME_URL, (i[0] for i in resp.redirect_chain))
        self.assertEqual(resp.resolver_match.func.__name__, "index")
        self.client.logout()

    def test_pull_request_post_with_login(self):
        """POST request for pull request feature with login"""
        self.client.force_login(User.objects.get_or_create(username='pullRequestTestUser')[0])
        resp = self.client.post(reverse("pull-request"), {}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.redirect_chain, [])
        self.assertEqual(resp.content, b"Please login using GitHub to use this feature.")
        self.client.logout()


class LicenseRequestsViewsTestCase(TestCase):

    def test_license_requests(self):
        """GET Request for license requests list"""
        resp = self.client.get(reverse("license-requests"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain, [])
        self.assertIn("app/license_requests.html", (i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__, "licenseRequests")

    def test_license_information_displays_github_issue_link(self):
        """GET license information page shows a link to the linked GitHub issue when present"""
        license_obj = LicenseRequest.objects.create(
            fullname="BSD Zero Clause License-00",
            shortIdentifier="0BSD",
            xml="<root></root>",
            github_issue_number=42,
            github_issue_url="https://github.com/spdx/license-list-XML/issues/42",
        )
        resp = self.client.get(reverse("license-information", args=(license_obj.id,)), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("app/license_information.html", (i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__, "licenseInformation")
        self.assertContains(resp, "https://github.com/spdx/license-list-XML/issues/42")
        self.assertContains(resp, "#42")


class ArchiveLicenseRequestsViewsTestCase(TestCase):

    def test_archive_license_requests(self):
        """GET Request for archive license requests list"""
        resp = self.client.get(reverse("archive-license-xml"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain, [])
        self.assertIn("app/archive_requests.html", (i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__, "archiveRequests")

    def test_error_archive_license_requests(self):
        """Check if error page is displayed when the license id does not exist for archive license"""
        license_id = 0
        resp = self.client.get(reverse("archived-license-information", args=(license_id,)), follow=True, secure=True)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.redirect_chain, [])
        self.assertIn("404.html", (i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__, "licenseInformation")

    def test_archive_button_hidden_for_anonymous_user(self):
        """A user who is not logged in via GitHub must not see the Archive button.

        The archive/unarchive feature is only available to GitHub-authorised
        collaborators (see the ``{% if github_login and authorized %}`` guard in
        the templates and ``checkPermission`` in utils.py). The logged-in path is
        covered by ArchiveLicenseRequestsSeleniumTestCase; this is the negative
        case and needs no GitHub credentials, so it is intentionally not gated
        with @skipIf."""
        license_obj = LicenseRequest.objects.create(
            fullname="BSD Zero Clause License-00", shortIdentifier="0BSD")
        resp = self.client.get(reverse("license-requests"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "archive_button" + str(license_obj.id))

    def test_unarchive_button_hidden_for_anonymous_user(self):
        """A user who is not logged in via GitHub must not see the Unarchive button."""
        archive_license_obj = LicenseRequest.objects.create(
            fullname="BSD Zero Clause License-00", shortIdentifier="0BSD", archive="True")
        resp = self.client.get(reverse("archive-license-xml"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "unarchive_button" + str(archive_license_obj.id))

    def loginGithubUser(self):
        """Create a GitHub-associated user and log them in.

        Returns the user. The archive/unarchive buttons require both a GitHub
        social-auth record (``github_login``) and ``authorized`` (set from
        ``checkPermission``), so the social-auth row is needed for the buttons
        to ever render. checkPermission is mocked in the individual tests, so no
        real GitHub credentials are needed and these tests are not @skipIf-gated."""
        user = User.objects.create(username="collab-test-user", is_active=True)
        UserSocialAuth.objects.create(provider="github", uid="0BSD-collab-uid",
                                      extra_data={"login": "collab-test-user"},
                                      user=user)
        self.client.force_login(user)
        return user

    def test_archive_button_shown_for_collaborator(self):
        """A GitHub collaborator (checkPermission True) must see the Archive button."""
        self.loginGithubUser()
        license_obj = LicenseRequest.objects.create(
            fullname="BSD Zero Clause License-00", shortIdentifier="0BSD")
        with patch("app.utils.checkPermission", return_value=True):
            resp = self.client.get(reverse("license-requests"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "archive_button" + str(license_obj.id))

    def test_archive_button_hidden_for_non_collaborator(self):
        """A logged-in non-collaborator (checkPermission False) must not see the Archive button."""
        self.loginGithubUser()
        license_obj = LicenseRequest.objects.create(
            fullname="BSD Zero Clause License-00", shortIdentifier="0BSD")
        with patch("app.utils.checkPermission", return_value=False):
            resp = self.client.get(reverse("license-requests"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "archive_button" + str(license_obj.id))

    def test_unarchive_button_shown_for_collaborator(self):
        """A GitHub collaborator (checkPermission True) must see the Unarchive button."""
        self.loginGithubUser()
        archive_license_obj = LicenseRequest.objects.create(
            fullname="BSD Zero Clause License-00", shortIdentifier="0BSD", archive="True")
        with patch("app.utils.checkPermission", return_value=True):
            resp = self.client.get(reverse("archive-license-xml"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "unarchive_button" + str(archive_license_obj.id))

    def test_unarchive_button_hidden_for_non_collaborator(self):
        """A logged-in non-collaborator (checkPermission False) must not see the Unarchive button."""
        self.loginGithubUser()
        archive_license_obj = LicenseRequest.objects.create(
            fullname="BSD Zero Clause License-00", shortIdentifier="0BSD", archive="True")
        with patch("app.utils.checkPermission", return_value=False):
            resp = self.client.get(reverse("archive-license-xml"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "unarchive_button" + str(archive_license_obj.id))


# @skipIf is intentionally kept alongside the BaseSeleniumTestCase.setUp check to skip
# the class before any fixtures are set up, which is faster.
@skipIf(not SELENIUM_AVAILABLE, "Selenium not available (Firefox or Chrome required)")
class ArchiveLicenseRequestsSeleniumTestCase(BaseSeleniumTestCase, GitHubLoginMixin):

    @skipIf(not getAccessToken() or not getGithubUserId() or not getGithubUserName(), "You need to set GitHub parameters in the secret.py file for this test to be executed properly.")
    def test_archive_license_requests_feature(self):
        """Check if the license is shifted to archive requests when archive button is pressed"""
        login = self.githubLogin()
        self.assertTrue(login)
        cookie = self.client.cookies['sessionid']
        driver = self.selenium
        with patch('app.utils.checkPermission') as mock_checkPermission:
            mock_checkPermission.return_value = True
            driver.get(self.live_server_url+'/app/license_requests/')
            driver.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
            driver.refresh()
            self.disable_animations()
            table_contents = driver.find_element(By.CSS_SELECTOR, 'tbody').text
            self.assertEqual(table_contents, "No data available in table")
            license_obj = LicenseRequest.objects.create(fullname="BSD Zero Clause License-00", shortIdentifier="0BSD")
            driver.refresh()
            self.disable_animations()
            license_name = driver.find_element(By.CSS_SELECTOR, 'td').text
            self.assertEqual(license_name, "BSD Zero Clause License-00")
            self.assertEqual(LicenseRequest.objects.get(id=license_obj.id).archive, False)
            driver.find_element(By.ID, 'archive_button' + str(license_obj.id)).click()
            confirm_btn = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'confirm_archive')))
            driver.execute_script("arguments[0].click();", confirm_btn)
            WebDriverWait(driver, 30).until(
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'tbody'), "No data available in table")
            )
            self.assertEqual(LicenseRequest.objects.get(id=license_obj.id).archive, True)

    @skipIf(not getAccessToken() or not getGithubUserId() or not getGithubUserName(), "You need to set GitHub parameters in the secret.py file for this test to be executed properly.")
    def test_unarchive_license_requests_feature(self):
        """Check if license is shifted back to license requests when unarchive button is pressed"""
        login = self.githubLogin()
        self.assertTrue(login)
        cookie = self.client.cookies['sessionid']
        driver = self.selenium
        with patch('app.utils.checkPermission') as mock_checkPermission:
            mock_checkPermission.return_value = True
            driver.get(self.live_server_url+'/app/archive_requests/')
            driver.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
            driver.refresh()
            self.disable_animations()
            table_contents = driver.find_element(By.CSS_SELECTOR, 'tbody').text
            self.assertEqual(table_contents, "No data available in table")
            archive_license_obj = LicenseRequest.objects.create(fullname="BSD Zero Clause License-00", shortIdentifier="0BSD", archive="True")
            driver.refresh()
            self.disable_animations()
            license_name = driver.find_element(By.CSS_SELECTOR, 'td').text
            self.assertEqual(license_name, "BSD Zero Clause License-00")
            self.assertEqual(LicenseRequest.objects.get(id=archive_license_obj.id).archive, True)
            driver.find_element(By.ID, 'unarchive_button' + str(archive_license_obj.id)).click()
            confirm_btn = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'confirm_unarchive')))
            driver.execute_script("arguments[0].click();", confirm_btn)
            WebDriverWait(driver, 30).until(
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'tbody'), "No data available in table")
            )
            self.assertEqual(LicenseRequest.objects.get(id=archive_license_obj.id).archive, False)


class SubmitNewLicenseViewsTestCase(TestCase, GitHubLoginMixin):

    def initialise(self):
        self.fullname = "BSD Zero Clause License"
        self.shortIdentifier = "0BSD"
        self.exampleUrl = "testUrl"
        self.sourceUrl = "http://landley.net/toybox/license.html"
        self.urls = [self.sourceUrl]
        self.osiApproved = "Unknown"
        self.comments = "Test Comment"
        self.notes = ""
        self.licenseHeader = ""
        self.text = "<text> <copyrightText> <p>Copyright (C) 2026 by Quom Glimp-Noodle &lt;qgn@example.com&gt;</p> </copyrightText> <p>This is a fictional test license text XYZ-UNIQUE-9a3f2b created solely for automated testing. It does not correspond to any real open source license. Permission is granted for testing purposes only.</p> <p>The heavy cast-iron skillet hissed loudly as the diced onions hit the shimmering oil. A fragrant cloud of steam billowed toward the ceiling, carrying hints of crushed garlic and smoky paprika. Outside the kitchen window, a lone blue jay perched on the weathered fence, chirping at the morning sun.</p> <p>Beneath the rolling turquoise waves, a vibrant coral reef teemed with rhythmic life.</p> </text>"
        self.userEmail = "test@mail.com"
        self.licenseAuthorName = ""
        self.listVersionAdded = ""
        self.xml = '<SPDXLicenseCollection xmlns="http://www.spdx.org/license"> <license isOsiApproved="false" licenseId="0BSD" listVersionAdded="" name="BSD Zero Clause License"> <crossRefs> <crossRef> http://landley.net/toybox/license.html</crossRef> </crossRefs> <standardLicenseHeader /> <notes /> <text> <p> &lt;text&gt; &lt;copyrightText&gt; &lt;p&gt;Copyright (C) 2026 by Quom Glimp-Noodle &amp;lt;qgn@example.com&amp;gt;&lt;/p&gt; &lt;/copyrightText&gt; &lt;p&gt;This is a fictional test license text XYZ-UNIQUE-9a3f2b created solely for automated testing. It does not correspond to any real open source license. Permission is granted for testing purposes only.&lt;/p&gt; &lt;p&gt;The heavy cast-iron skillet hissed loudly as the diced onions hit the shimmering oil. A fragrant cloud of steam billowed toward the ceiling, carrying hints of crushed garlic and smoky paprika. Outside the kitchen window, a lone blue jay perched on the weathered fence, chirping at the morning sun.&lt;/p&gt; &lt;p&gt;Beneath the rolling turquoise waves, a vibrant coral reef teemed with rhythmic life.&lt;/p&gt; &lt;/text&gt;</p> </text> </license> </SPDXLicenseCollection> '
        self.data_no_author = {"fullname": self.fullname, "shortIdentifier": self.shortIdentifier,
                    "sourceUrl": self.sourceUrl, 'osiApproved': self.osiApproved, 'notes': self.notes,
                    "licenseHeader": self.licenseHeader, "text": self.text, "userEmail": self.userEmail,
                    "urlType": "tests", "exampleUrl": self.exampleUrl, "comments": self.comments,
                    "isException": "False"}

    def test_submit_new_license(self):
        """GET Request for submit a new license"""
        resp = self.client.get(reverse("submit-new-license"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain, [])
        self.assertIn("app/submit_new_license.html", (i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__, "submitNewLicense")
        self.assertIn("form", resp.context)
        self.assertIn("fullname", resp.context["form"].fields)
        self.assertIn("shortIdentifier", resp.context["form"].fields)
        self.assertIn("sourceUrl", resp.context["form"].fields)
        self.assertIn("osiApproved", resp.context["form"].fields)
        self.assertIn("comments", resp.context["form"].fields)
        self.assertIn("licenseHeader", resp.context["form"].fields)
        self.assertIn("text", resp.context["form"].fields)
        self.assertIn("userEmail", resp.context["form"].fields)

    def test_generate_xml(self):
        """View for generating an xml from license submittal form fields"""
        self.initialise()
        xml = generateLicenseXml(self.osiApproved, self.shortIdentifier, self.fullname, self.listVersionAdded,
                                self.urls, self.licenseHeader, self.notes, self.text).replace(">", "> ")
        self.assertEqual(self.xml, xml)

    @skipIf(not getAccessToken() or not getGithubUserId() or not getGithubUserName(), "You need to set GitHub parameters in the secret.py file for this test to be executed properly.")
    def test_post_submit(self):
        """POST Request for submit a new license"""
        login = self.githubLogin()
        self.assertTrue(login)
        self.initialise()
        resp = self.client.post(reverse("submit-new-license"),
                                self.data_no_author,
                                follow=True,
                                secure=True,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain, [])
        licenseRequest = LicenseRequest.objects.last()
        self.assertEqual(licenseRequest.licenseAuthorName, "")
