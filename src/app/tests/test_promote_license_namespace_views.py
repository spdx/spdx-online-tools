# -*- coding: utf-8 -*-


from unittest import skipIf
from src.secret import getAccessToken, getGithubUserId, getGithubUserName
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

from app.models import LicenseNamespace
from app.generateXml import generateLicenseXml
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from social_django.models import UserSocialAuth



class PromoteLicenseNamespaceViewsTestCase(StaticLiveServerTestCase):

    def setUp(self):
        options = Options()
        options.add_argument('-headless')
        self.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_options=options)
        #login
        TEST_LOGIN_INFO = {
        "provider": "github",
        "uid": str(getGithubUserId()),
        "access_token": getAccessToken(),
        "login": getGithubUserName(),
        "id": getGithubUserId(),
        "password": 'pass'
        }
        # login first
        self.user = User.objects.create(username=TEST_LOGIN_INFO["login"],
                                        is_active=True,
                                        is_superuser=True)
        self.user.set_password(TEST_LOGIN_INFO["password"])
        self.user.save()
        social_auth = UserSocialAuth.objects.create(provider=TEST_LOGIN_INFO["provider"],
                                                    uid=TEST_LOGIN_INFO["uid"],
                                                    extra_data=TEST_LOGIN_INFO,
                                                    user=self.user)
        self.user = authenticate(username=TEST_LOGIN_INFO["login"],
                                 password=TEST_LOGIN_INFO["password"])
        login = self.client.login(username=TEST_LOGIN_INFO["login"],
                                  password=TEST_LOGIN_INFO["password"])
        self.assertTrue(login)
        # end login
        super(PromoteLicenseNamespaceViewsTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(PromoteLicenseNamespaceViewsTestCase, self).tearDown()


    @skipIf(not getAccessToken() and not getGithubUserId() and not getGithubUserName(), "You need to set gihub parameters in the secret.py file for this test to be executed properly.")
    def test_promote_license_namespace_feature(self):
        """Github access token,id and username should be added in .env to execute the test properly"""
        """Check if the license namespace is shifted to archive namespace when archive button is pressed"""
        driver = self.selenium
        driver.get(self.live_server_url+'/app/license_namespace_requests/')
        table_contents = driver.find_element_by_css_selector('tbody').text
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
        license_name = driver.find_element_by_css_selector('td').text
        self.assertEqual(license_name, "BSD Zero Clause License-00")
        self.assertEqual(LicenseNamespace.objects.get(id=license_obj.id).promoted, False)

        resp = self.client.post(reverse("promoted-license-namespace-xml"),
                                {"promoted": True, "license_id": license_obj.id},
                                follow=True,
                                secure=True,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])