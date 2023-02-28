# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2017 Rohit Lodha
# Copyright (c) 2017 Rohit Lodha
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License

from django.test import TestCase
from unittest import skipIf
from src.secret import getAuthCode,getGithubKey,getGithubSecret
from django.core.exceptions import ObjectDoesNotExist,PermissionDenied
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import now, timedelta

from rest_framework.test import APITestCase,APIClient
from oauth2_provider.models import AccessToken,Application
from oauth2_provider.settings import oauth2_settings
from oauthlib.common import generate_token
from rest_framework.authtoken.models import Token

from requests import get
from json import dumps, loads
from api.oauth import generate_github_access_token,get_user_from_token
from api.views import generateLicenseXml

from api.models import ValidateFileUpload,ConvertFileUpload,CompareFileUpload,CheckLicenseFileUpload,SubmitLicenseModel
from django.conf import settings
import os

def getExamplePath(filename):
    return os.path.join(settings.EXAMPLES_DIR, filename)

class ValidateFileUploadTests(APITestCase):
    """ Test for validate api with all
    possible combination of POST and GET 
    request with login enabled.
    """
    def setUp(self):
        self.username = "validateapitestuser"
        self.password = "validateapitestpass"
        self.tearDown()
        self.credentials = {'username':self.username,
            'password':self.password
            }
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"))
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.0.rdf"))
        self.invalid_tv_file = open(getExamplePath("SPDXTagExample-v2.0_invalid.spdx"))
        self.invalid_rdf_file = open(getExamplePath("SPDXRdfExample-v2.0_invalid.rdf"))

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        ValidateFileUpload.objects.all().delete()

    def test_validate_api(self):
        """Access get without login"""
        resp1 = self.client.get(reverse("validate-api"))
        self.assertTrue(resp1.status_code,403)
        self.client.login(username=self.username,password=self.password)
        """ Access get after login"""
        resp2 = self.client.get(reverse("validate-api")) 
        self.assertTrue(resp2.status_code,200)
        """ Valid Tag Value File"""
        resp3 = self.client.post(reverse("validate-api"),{"file":self.tv_file, "format" : "TAG"},format="multipart")
        self.assertEqual(resp3.status_code,200)
        self.assertEqual(resp3.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp3.data["result"],"This SPDX Document is valid.")
        """ Valid RDF File"""
        resp4 = self.client.post(reverse("validate-api"),{"file":self.rdf_file, "format" : "RDFXML"},format="multipart")
        self.assertEqual(resp4.status_code,200)
        self.assertEqual(resp4.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp4.data["result"],"This SPDX Document is valid.")
        """ Invalid Tag Value File"""
        resp5 = self.client.post(reverse("validate-api"),{"file":self.invalid_tv_file, "format" : "TAG"},format="multipart")
        self.assertEqual(resp5.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp5.status_code,400)
        self.assertNotEqual(resp5.data["result"],"This SPDX Document is valid.")
        """ Invalid RDF File"""
        resp6 = self.client.post(reverse("validate-api"),{"file":self.invalid_rdf_file, "format" : "RDFXML"},format="multipart")
        self.assertEqual(resp6.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp6.status_code,400)
        self.assertNotEqual(resp6.data["result"],"This SPDX Document is valid.")
        self.client.logout()
        self.tearDown()
        
    def test_validate_without_argument(self):
        self.client.login(username=self.username,password=self.password)
        resp7 = self.client.post(reverse("validate-api"),{},format="multipart")
        self.assertEqual(resp7.status_code,400)
        self.client.logout()
        self.tearDown()

class ConvertFileUploadTests(APITestCase):
    """ Test for convert api with all
    possible combination of POST and GET 
    request with login enabled.
    """
    def setUp(self):
        self.username = "convertapitestuser"
        self.password = "convertapitestpass"
        self.tearDown()
        self.credentials = {'username':self.username,'password':self.password }
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.tag = "TAG"
        self.rdf = "RDFXML"
        self.xlsx = "XLS"
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.2.spdx"), 'rb')
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.2.spdx.rdf.xml"), 'rb')
        self.xlsx_file = open(getExamplePath("SPDXSpreadsheetExample-v2.2.xls"), 'rb')

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        ConvertFileUpload.objects.all().delete()

    def test_convert_api(self):
        """Access get without login"""
        resp1 = self.client.get(reverse("convert-api"))
        self.assertTrue(resp1.status_code,403)
        """Access get after login"""
        self.client.login(username=self.username,password=self.password)
        resp2 = self.client.get(reverse("convert-api"))
        self.assertTrue(resp2.status_code,200)
        self.client.logout()

    def test_convert_tagtordf_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.tv_file,"from_format":self.tag,"to_format":self.rdf,"cfilename":"tagtordf-apitest"},format="multipart")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_tagtoxlsx_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.tv_file,"from_format":self.tag,"to_format":self.xlsx,"cfilename":"tagtoxlsx-apitest"},format="multipart")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_rdftotag_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.rdf_file,"from_format":self.rdf,"to_format":self.tag,"cfilename":"rdftotag-apitest"},format="multipart")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertTrue(resp.data['result'].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_rdftoxlsx_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.rdf_file,"from_format":self.rdf,"to_format":self.xlsx,"cfilename":"rdftoxlsx-apitest"},format="multipart")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_xlsxtordf_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"from_format":self.xlsx,"to_format":self.rdf,"cfilename":"xlsxtordf-apitest"},format="multipart")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_xlsxtotag_api(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"from_format":self.xlsx,"to_format":self.tag,"cfilename":"xlsxtotag-apitest"},format="multipart")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(resp.data['message'], 'Success')
        self.assertTrue(resp.data["result"].startswith(settings.MEDIA_URL))
        self.assertEqual(resp.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.client.logout()

    def test_convert_without_one_argument(self):
        self.client.login(username=self.username,password=self.password)
        resp = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"to_format":self.tag,"cfilename":"xlsxtotag-apitest"},format="multipart")
        self.assertEqual(resp.status_code,400)
        
        resp2 = self.client.post(reverse("convert-api"),{"from_format":self.xlsx,"to_format":self.tag,"cfilename":"xlsxtotag-apitest"},format="multipart")
        self.assertEqual(resp2.status_code,400)
        
        resp3 = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"from_format":self.xlsx,"to_format":self.tag},format="multipart")
        self.assertEqual(resp3.status_code,400)
        
        resp4 = self.client.post(reverse("convert-api"),{"file":self.xlsx_file,"from_format":self.xlsx,"cfilename":"xlsxtotag-apitest"},format="multipart")
        self.assertEqual(resp4.status_code,400)
        self.client.logout()

class CompareFileUploadTests(APITestCase):
    """ Test for compare api with all
    possible combination of POST and GET 
    request with login enabled.
    """
    def setUp(self):
        self.username = "compareapitestuser"
        self.password = "compareapitestpass"
        self.tearDown()
        self.credentials = {'username':self.username,'password':self.password }
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.rdf_file = open(getExamplePath("SPDXRdfExample-v2.0.rdf"))
        self.rdf_file2 = open(getExamplePath("SPDXRdfExample.rdf"))
        self.tv_file = open(getExamplePath("SPDXTagExample-v2.0.spdx"))

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        CompareFileUpload.objects.all().delete()

    def test_compare_api(self):
        """Access get without login"""
        resp1 = self.client.get(reverse("compare-api"))
        self.assertTrue(resp1.status_code,403)
        """Access get after login"""
        self.client.login(username=self.username,password=self.password)
        resp2 = self.client.get(reverse("compare-api"))
        self.assertTrue(resp2.status_code,200)
        """Compare two valid RDF files"""
        resp3 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"file2":self.rdf_file2,"rfilename":"compare-apitest.xls"},format="multipart")
        self.assertEqual(resp3.status_code,200)
        self.assertEqual(resp3.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertTrue(resp3.data["result"].startswith(settings.MEDIA_URL))
        """Compare with one  invalid RDF files"""
        resp4 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"file2":self.tv_file,"rfilename":"compare-apitest.xls"},format="multipart")
        self.assertEqual(resp4.status_code,400)
        self.client.logout()
        self.tearDown()
        
    def test_compare_without_one_argument(self):
        self.client.login(username=self.username,password=self.password)
        resp5 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"file2":self.rdf_file2},format="multipart")
        self.assertEqual(resp5.status_code,400)
        
        resp6 = self.client.post(reverse("compare-api"),{"file1":self.rdf_file,"rfilename":"compare-apitest.xls"},format="multipart")
        self.assertEqual(resp6.status_code,400)
        
        resp7 = self.client.post(reverse("compare-api"),{"file2":self.rdf_file,"rfilename":"compare-apitest.xls"},format="multipart")
        self.assertEqual(resp7.status_code,400)
        self.client.logout()
        self.tearDown()

class CheckLicenseFileUploadTests(APITestCase):

    def setUp(self):
        self.username = "checklicenseapitestuser"
        self.password = "checklicenseapitestpass"
        self.tearDown()
        self.credentials = {'username':self.username,
            'password':self.password
            }
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        self.license_file = open(getExamplePath("AFL-1.1.txt"))
        self.other_file = open(getExamplePath("Other.txt"))
        
    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        CheckLicenseFileUpload.objects.all().delete()

    def test_checklicense_api(self):
        """Access get without login"""
        resp1 = self.client.get(reverse("check_license-api"))
        self.assertTrue(resp1.status_code,403)
        self.client.login(username=self.username,password=self.password)
        """ Access get after login"""
        resp2 = self.client.get(reverse("check_license-api")) 
        self.assertTrue(resp2.status_code,200)
        """ Valid License File"""
        resp3 = self.client.post(reverse("check_license-api"),{"file":self.license_file},format="multipart")
        self.assertEqual(resp3.status_code,200)
        self.assertEqual(resp3.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp3.data["result"],"The following license ID(s) match: AFL-1.1")
        """ Other File"""
        resp4 = self.client.post(reverse("check_license-api"),{"file":self.other_file},format="multipart")
        self.assertEqual(resp4.data['owner'],User.objects.get_by_natural_key(self.username).id)
        self.assertEqual(resp4.status_code,404)
        self.assertEqual(resp4.data["result"],"There are no matching SPDX listed licenses")
        
    def test_checklicense_without_argument(self):
        self.client.login(username=self.username,password=self.password)
        resp5 = self.client.post(reverse("check_license-api"),{},format="multipart")
        self.assertEqual(resp5.status_code,400)
        self.client.logout()
        self.tearDown()

class SubmitLicenseModelsTests(APITestCase):

    def setUp(self):
        self.username = "submitlicenseapitestuser"
        self.password = "submitlicenseapitestpass"
        self.tearDown()
        self.credentials = {'username':self.username,
            'password':self.password
            }
        u = User.objects.create_user(**self.credentials)
        u.is_staff = True
        u.save()
        app = Application(
            client_type='confidential',
            authorization_grant_type='password',
            name='Owner',
            user=u
            )
        app.save()
        self.user = u
        self.emptyCode = ''
        self.invalidCode = 'code123'
        self.fullname = "BSD Zero Clause License"
        self.shortIdentifier = "0BSD"
        self.sourceUrl = "http://landley.net/toybox/license.html"
        self.urls = [self.sourceUrl]
        self.incorrectOsiApproved = "no" # "no" is not a valid choice for osi
        self.osiApproved = "Rejected"
        self.comments = ""
        self.notes = ""
        self.licenseHeader = ""
        self.text ='<text> <copyrightText> <p>Copyright (C) 2006 by Rob Landley &lt;rob@landley.net&gt;</p> </copyrightText> <p>Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.</p> <p>THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.</p> </text>'
        self.userEmail = "test@mail.com"
        self.licenseAuthorName = ""
        self.listVersionAdded = ""
        self.xml = '<SPDXLicenseCollection xmlns="http://www.spdx.org/license"><license isOsiApproved="false" licenseId="0BSD" listVersionAdded="" name="BSD Zero Clause License"><crossRefs><crossRef>http://landley.net/toybox/license.html</crossRef></crossRefs><standardLicenseHeader /><notes /><text><p>&lt;text&gt; &lt;copyrightText&gt; &lt;p&gt;Copyright (C) 2006 by Rob Landley &amp;lt;rob@landley.net&amp;gt;&lt;/p&gt; &lt;/copyrightText&gt; &lt;p&gt;Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.&lt;/p&gt; &lt;p&gt;THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.&lt;/p&gt; &lt;/text&gt;</p></text></license></SPDXLicenseCollection>'
        self.data = {"fullname": self.fullname, "shortIdentifier": self.shortIdentifier,
                    "sourceUrl": self.sourceUrl,'osiApproved': self.osiApproved, 'notes': self.notes,
                    "licenseHeader": self.licenseHeader, "text": self.text, "userEmail": self.userEmail,
                    "licenseAuthorName": self.licenseAuthorName, "urlType": "tests"}

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key(self.username)
            u.delete()
        except ObjectDoesNotExist:
            pass
        SubmitLicenseModel.objects.all().delete()

    def test_submitlicense_api(self):
        """Access submit license api get request without login"""
        resp1 = self.client.get(reverse("submit_license-api"),follow=True,secure=True)
        self.assertTrue(resp1.status_code,403)
        """ Access get after login"""
        app = Application.objects.get(name='Owner')
        token = generate_token()
        expires = now() + timedelta(seconds=oauth2_settings. \
            ACCESS_TOKEN_EXPIRE_SECONDS)
        scope = 'read write'
        access_token = AccessToken.objects.create(
            user=self.user,
            application=app,
            expires=expires,
            token=token,
            scope=scope
        )
        access_token.save()
        self.auth =  "Bearer {0}".format(access_token.token)
        resp2 = self.client.get(reverse("submit_license-api"), HTTP_AUTHORIZATION=self.auth)
        self.assertTrue(resp2.status_code,201)

    def test_generate_xml(self):
        """View for generating an xml from license submittal form fields"""
        xml = generateLicenseXml(self.osiApproved, self.shortIdentifier, self.fullname, self.listVersionAdded,
                                self.urls, self.licenseHeader, self.notes, self.text)
        self.assertEqual(self.xml, xml)

    def test_submitlicense_api_with_invalid_code(self):
        """ Post submit license api with empty authentication code"""
        resp3 = self.client.post(reverse("submit_license-api"),{"code":self.emptyCode,"fullname":self.fullname,"shortIdentifier":self.shortIdentifier,"licenseAuthorName":self.licenseAuthorName,"userEmail":self.userEmail,"text":self.text,"osiApproved":self.osiApproved,"sourceUrl":self.sourceUrl},format="multipart")
        self.assertIn("No authentication code provided.", str(resp3.content))
        """ Post submit license api with invalid authentication code"""
        resp4 = self.client.post(reverse("submit_license-api"),{"code":self.invalidCode,"fullname":self.fullname,"shortIdentifier":self.shortIdentifier,"licenseAuthorName":self.licenseAuthorName,"userEmail":self.userEmail,"text":self.text,"osiApproved":self.osiApproved,"sourceUrl":self.sourceUrl},format="multipart")
        self.assertIn("Authentication code provided is incorrect.", str(resp4.content))

    @skipIf(not getAuthCode(), "You need to set the authentication code in the secret.py file for this test to be executed properly.")
    def test_submitlicense_api_with_valid_fields(self):
        """ Test working of oauth.py file"""
        app = Application.objects.get(name='Owner')
        auth_code = getAuthCode()
        github_client_id = getGithubKey()
        github_client_secret = getGithubSecret()
        try:
            github_access_token = generate_github_access_token(github_client_id,github_client_secret,auth_code)
        except PermissionDenied:
            self.fail("Couldn't generate github access_token check if the code is correct. NOTE: You can only used your code once.")
        resp5 = self.client.post("/auth/convert-token", {"grant_type":"convert_token","token":github_access_token,"backend":"github","client_id":app.client_id,"client_secret":app.client_secret})
        self.assertIn('access_token', resp5.data, "Couldn't generate django access_token")
        access_token = resp5.data['access_token']   # django access token
        user = get_user_from_token(access_token)
        userID = user.id
        resp6 = get('https://api.github.com/user', headers={'Authorization': 'token %s' %  github_access_token})
        self.assertIn(user.username, resp6.json()['login'])
        """ Test submit licence with valid auth code and valid fields"""
        self.data.update({"user_id":userID,"code":auth_code,"token":github_access_token})
        resp7 = self.client.post(reverse("submit_license-api"), self.data, format="multipart")
        self.assertTrue(resp7.status_code,201)
        self.assertEqual(resp7.data['result'],"Success! The license request has been successfully submitted.")
        self.assertEqual(resp7.data['owner'], userID)

    def test_submitlicense_api_with_invalid_fields(self):
        """ Test for invalid serializer"""
        resp8 = self.client.post(reverse("submit_license-api"),{},format="multipart")
        self.assertEqual(resp8.status_code,400)
        """ Test with incorrect osi choice"""
        resp9 = self.client.post(reverse("submit_license-api"),{"osiApproved":self.incorrectOsiApproved},format="multipart")
        self.assertEqual(resp9.status_code,400)
        self.assertIn("is not a valid choice.", str(resp9.content))
