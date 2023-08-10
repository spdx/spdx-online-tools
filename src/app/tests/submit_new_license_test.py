# -*- coding: utf-8 -*-


from django.test import TestCase
from unittest import skipIf
from src.secret import getAccessToken, getGithubUserId, getGithubUserName
from django.contrib.auth.models import User
from django.urls import reverse


from app.models import LicenseRequest
from app.generateXml import generateLicenseXml
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from social_django.models import UserSocialAuth


class SubmitNewLicenseViewsTestCase(TestCase):

    def initialise(self):
        self.fullname = "BSD Zero Clause License"
        self.shortIdentifier = "0BSD"
        self.exampleUrl = "testUrl"
        self.sourceUrl = "http://landley.net/toybox/license.html"
        self.urls = [self.sourceUrl]
        self.osiApproved = "no"
        self.comments = "Test Comment"
        self.notes = ""
        self.licenseHeader = ""
        self.text ='<text> <copyrightText> <p>Copyright (C) 2006 by Rob Landley &lt;rob@landley.net&gt;</p> </copyrightText> <p>Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.</p> <p>THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.</p> </text>'
        self.userEmail = "test@mail.com"
        self.licenseAuthorName = ""
        self.listVersionAdded = ""
        self.xml = '<SPDXLicenseCollection xmlns="http://www.spdx.org/license"> <license isOsiApproved="false" licenseId="0BSD" listVersionAdded="" name="BSD Zero Clause License"> <crossRefs> <crossRef> http://landley.net/toybox/license.html</crossRef> </crossRefs> <standardLicenseHeader /> <notes /> <text> <p> &lt;text&gt; &lt;copyrightText&gt; &lt;p&gt;Copyright (C) 2006 by Rob Landley &amp;lt;rob@landley.net&amp;gt;&lt;/p&gt; &lt;/copyrightText&gt; &lt;p&gt;Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.&lt;/p&gt; &lt;p&gt;THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.&lt;/p&gt; &lt;/text&gt;</p> </text> </license> </SPDXLicenseCollection> '
        self.data_no_author = {"fullname": self.fullname, "shortIdentifier": self.shortIdentifier,
                    "sourceUrl": self.sourceUrl,'osiApproved': self.osiApproved, 'notes': self.notes,
                    "licenseHeader": self.licenseHeader, "text": self.text, "userEmail": self.userEmail,
                    "urlType": "tests", "exampleUrl":self.exampleUrl,"comments":self.comments}
        self.data = self.data_no_author.update({"licenseAuthorName": self.licenseAuthorName})

    def test_submit_new_license(self):
        """GET Request for submit a new license"""
        resp = self.client.get(reverse("submit-new-license"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/submit_new_license.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"submitNewLicense")
        self.assertIn("form",resp.context)
        if "form" in resp.context:
            self.assertIn("fullname",resp.context["form"].fields)
            self.assertIn("shortIdentifier",resp.context["form"].fields)
            self.assertIn("sourceUrl",resp.context["form"].fields)
            self.assertIn("osiApproved",resp.context["form"].fields)
            self.assertIn("comments",resp.context["form"].fields)
            self.assertIn("licenseHeader",resp.context["form"].fields)
            self.assertIn("text",resp.context["form"].fields)
            self.assertIn("userEmail",resp.context["form"].fields)

    def test_generate_xml(self):
        """View for generating an xml from license submittal form fields"""
        self.initialise()
        xml = generateLicenseXml(self.osiApproved, self.shortIdentifier, self.fullname, self.listVersionAdded,
                                self.urls, self.licenseHeader, self.notes, self.text).replace(">","> ")
        self.assertEqual(self.xml, xml)

    @skipIf(not getAccessToken() and not getGithubUserId() and not getGithubUserName(), "You need to set gihub parameters in the secret.py file for this test to be executed properly.")
    def test_post_submit(self):
        """POST Request for submit a new license"""
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
        self.initialise()
        # login via GitHub
        resp = self.client.post(reverse("submit-new-license"),
                                self.data_no_author,
                                follow=True,
                                secure=True,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        licenseRequest = LicenseRequest.objects.last()
        self.assertEqual(licenseRequest.licenseAuthorName, "")
