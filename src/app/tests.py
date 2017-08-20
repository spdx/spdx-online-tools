# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse

import jpype

from app.models import UserID


class IndexViewsTestCase(TestCase):

    def test_index(self):
        resp = self.client.get(reverse("index"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/index.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"index")

class AboutViewsTestCase(TestCase):

    def test_about(self):
        resp = self.client.get(reverse("about"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/about.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"about")

class LoginViewsTestCase(TestCase):

    def initialise(self):
        self.credentials = {'username':'testuser','password':'testpass' }
        user = User.objects.create_user(**self.credentials)
        user.is_staff = True
        user.is_active = True
        user.save()
        self.credentials2 = {'username':'testuser2','password':'testpass2' }
        user2 = User.objects.create_user(**self.credentials2)
        user2.is_staff = False
        user2.is_active = True
        user2.save()
        self.credentials3 = {'username':'testuser3','password':'testpass3' }
        user3 = User.objects.create_user(**self.credentials3)
        user3.is_staff = True
        user3.is_active = False
        user3.save()

    def test_login(self):
        resp = self.client.get(reverse("login"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/login.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"loginuser")

    def test_postlogin(self):
        self.initialise()
        resp = self.client.post(reverse("login"),self.credentials,follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.LOGIN_REDIRECT_URL, (i[0] for i in resp.redirect_chain))
        self.assertTrue(resp.context['user'].is_active)
        self.assertTrue(resp.context['user'].is_staff)
        self.assertFalse(resp.context['user'].is_superuser)
        self.client.get(reverse("logout"))

        resp2 = self.client.post(reverse("login"),self.credentials2,follow=True,secure=True)
        self.assertEqual(resp2.status_code,403)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertFalse(resp2.context['user'].is_active)
        self.assertFalse(resp2.context['user'].is_staff)
        self.assertFalse(resp2.context['user'].is_superuser)
        self.assertTrue('invalid' in resp2.context)
        self.assertIn("app/login.html",(i.name for i in resp2.templates))
        self.client.get(reverse("logout"))

        resp3 = self.client.post(reverse("login"),self.credentials3,follow=True,secure=True)
        self.assertEqual(resp3.status_code,403)
        self.assertEqual(resp3.redirect_chain,[])
        self.assertFalse(resp3.context['user'].is_active)
        self.assertFalse(resp3.context['user'].is_staff)
        self.assertFalse(resp3.context['user'].is_superuser)
        self.assertTrue('invalid' in resp3.context)
        self.assertIn("app/login.html",(i.name for i in resp3.templates))
        self.client.get(reverse("logout"))

class RegisterViewsTestCase(TestCase):

    def initialise(self):
        self.username = "testuser4"
        self.password ="testpass4"
        self.data = {"first_name": "test","last_name" : "test" ,
            "email" : "test@spdx.org","username":self.username,
            "password":self.password,"confirm_password":self.password,"organisation":"spdx"}
            
    def test_register(self):
        resp = self.client.get(reverse("register"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertTrue('user_form' in resp.context)
        self.assertTrue('profile_form' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertIn("app/register.html",(i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__,"register")

    def test_formregister(self):
        self.initialise()
        resp = self.client.post(reverse("register"),self.data,follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.REGISTER_REDIRECT_UTL, (i[0] for i in resp.redirect_chain))

        loginresp = self.client.post(reverse("login"),{'username':self.username,'password':self.password},follow=True,secure=True)
        self.assertEqual(loginresp.status_code,200)
        self.assertTrue(loginresp.context['user'].is_active)
        self.assertTrue(loginresp.context['user'].is_staff)
        self.assertFalse(loginresp.context['user'].is_superuser)
        self.assertIn(settings.LOGIN_REDIRECT_URL, (i[0] for i in loginresp.redirect_chain))
        self.client.get(reverse("logout"))

class ValidateViewsTestCase(TestCase):

    def test_validate(self):
        resp = self.client.get(reverse("validate"),follow=True,secure=True)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.assertEqual(resp.status_code,200)
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])

        resp2 = self.client.get(reverse("validate"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertIn("app/validate.html",(i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__,"validate")
        self.client.logout()
        
    def test_validate_post_without_login(self):
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        resp = self.client.post(reverse("validate"),{'file' : self.tv_file},follow=True,secure=True)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.tv_file.close()
        self.assertEqual(resp.status_code,200)

    def test_validate_post_without_file(self):
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        resp = self.client.post(reverse("validate"),{},follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.client.logout()

    def test_upload_tv(self):
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        resp = self.client.post(reverse("validate"),{'file' : self.tv_file},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.content,"This SPDX Document is valid.")
        self.client.logout()

    def test_upload_rdf(self):
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        resp = self.client.post(reverse("validate"),{'file' : self.rdf_file},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.content,"This SPDX Document is valid.")
        self.rdf_file.close()
        self.client.logout()
    
    def test_upload_other(self):
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.other_file = open("examples/Other.txt")
        resp = self.client.post(reverse("validate"),{'file' : self.other_file},follow=True,secure=True)
        self.assertTrue(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.other_file.close()
        self.client.logout()

    def test_upload_inv_tv(self):
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.invalid_tv_file = open("examples/SPDXTagExample-v2.0_invalid.spdx")
        resp = self.client.post(reverse("validate"),{'file' : self.invalid_tv_file},follow=True)
        self.assertTrue(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.invalid_tv_file.close()
        self.client.logout()

    def test_upload_inv_rdf(self):
        self.client.force_login(User.objects.get_or_create(username='validatetestuser')[0])
        self.invalid_rdf_file = open("examples/SPDXRdfExample-v2.0_invalid.rdf")
        resp = self.client.post(reverse("validate"),{'file' : self.invalid_rdf_file},follow=True)
        self.assertTrue(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.client.logout()


class CompareViewsTestCase(TestCase):
    
    def initialise(self):
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        self.rdf_file2 = open("examples/SPDXRdfExample.rdf")
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")

    def exit(self):
        self.rdf_file.close()
        self.rdf_file2.close()
        self.tv_file.close()

    def test_compare(self):
        resp = self.client.get(reverse("compare"),follow=True,secure=True)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.assertEqual(resp.status_code,200)
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp2 = self.client.get(reverse("compare"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertIn("app/compare.html",(i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__,"compare")
        self.client.logout()

    def test_compare_post_without_login(self):
        self.initialise()
        resp = self.client.post(reverse("compare"),{'compare':'compare','nofile': "2" ,'rfilename': "comparetest",'file1' : self.rdf_file, 'file2' : self.rdf_file2},follow=True,secure=True)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.assertEqual(resp.status_code,200)
        self.exit()

    def test_compare_post_without_file(self):
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"),{'compare':'compare','nofile': "2" ,'rfilename': "comparetest"},follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.exit()
        self.client.logout()

    def test_compare_post_without_valid_compare_method(self):
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"),{'nofile': "2" ,'rfilename': "comparetest",'file1' : self.rdf_file, 'file2' : self.rdf_file2},follow=True,secure=True)
        self.assertEqual(resp.status_code,404)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.exit()
        self.client.logout()

    def test_compare_two_rdf(self):
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"),{'compare':'compare','nofile': '2' ,'rfilename': 'comparetest','file1' : self.rdf_file, 'file2' : self.rdf_file2},follow=True,secure=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/vnd.ms-excel")
        self.exit()
        self.client.logout()

    def test_compare_invalid_rdf(self):
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='comparetestuser')[0])
        resp = self.client.post(reverse("compare"),{'compare':'compare','nofile': '2' ,'rfilename': 'comparetest','file1' : self.rdf_file, 'file2' : self.tv_file},follow=True,secure=True)
        self.assertEqual(resp.status_code,400)
        self.assertTrue('error' in resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.exit()
        self.client.logout()

    
    
class ConvertViewsTestCase(TestCase):

    def test_convert(self):
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
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        resp = self.client.post(reverse("convert"),{'cfilename': "tagtest" ,'cfileformat': ".rdf",'from_format' : "Tag", 'to_format' : "RDF", 'file' : self.tv_file},follow=True,secure=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/rdf+xml")
        self.tv_file.close()
        self.client.logout()

    def test_convert_tagtoxlsx(self):
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.tv_file = open("examples/SPDXTagExample-v2.0.spdx")
        resp = self.client.post(reverse("convert"),{'cfilename': "tagtest" ,'cfileformat': ".xlsx",'from_format' : "Tag", 'to_format' : "Spreadsheet", 'file' : self.tv_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/vnd.ms-excel")
        self.tv_file.close()
        self.client.logout()

    def test_convert_rdftotag(self):
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".spdx",'from_format' : "RDF", 'to_format' : "Tag", 'file' : self.rdf_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"text/tag-value")
        self.rdf_file.close()
        self.client.logout()

    def test_convert_rdftoxlsx(self):
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
        resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".xlsx",'from_format' : "RDF", 'to_format' : "Spreadsheet", 'file' : self.rdf_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/vnd.ms-excel")
        self.rdf_file.close()
        self.client.logout()

    # def test_convert_rdftohtml(self):
    #     self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
    #     self.rdf_file = open("examples/SPDXRdfExample-v2.0.rdf")
    #     resp = self.client.post(reverse("convert"),{'cfilename': "rdftest" ,'cfileformat': ".html",'from_format' : "RDF", 'to_format' : "Html", 'file' : self.rdf_file},follow=True)
    #     self.assertEqual(resp.status_code,200)
    #     self.assertNotEqual(resp.redirect_chain,[])
    #     self.rdf_file.close()
    #     self.client.logout()

    def test_convert_xlsxtotag(self):
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.xls_file = open("examples/SPDXSpreadsheetExample-2.0.xls")
        resp = self.client.post(reverse("convert"),{'cfilename': "xlsxtest" ,'cfileformat': ".spdx",'from_format' : "Spreadsheet", 'to_format' : "Tag", 'file' : self.xls_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"text/tag-value")
        self.xls_file.close()
        self.client.logout()

    def test_convert_xlsxtordf(self):
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        self.xls_file = open("examples/SPDXSpreadsheetExample-2.0.xls")
        resp = self.client.post(reverse("convert"),{'cfilename': "xlsxtest" ,'cfileformat': ".rdf",'from_format' : "Spreadsheet", 'to_format' : "RDF", 'file' : self.xls_file},follow=True)
        self.assertTrue(resp.status_code==406 or resp.status_code == 200)
        self.assertIn("medialink",resp.context)
        self.assertEqual(resp.redirect_chain,[])
        self.assertTrue(resp.context["medialink"].startswith(settings.MEDIA_URL))
        self.assertIn("Content-Type",resp.context)
        self.assertEqual(resp.context["Content-Type"],"application/rdf+xml")
        self.xls_file.close()
        self.client.logout()

class CheckLicenseViewsTestCase(TestCase):

    def test_check_license(self):
        resp = self.client.get(reverse("check-license"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.client.force_login(User.objects.get_or_create(username='converttestuser')[0])
        
        resp2 = self.client.get(reverse("check-license"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertIn("app/check_license.html",(i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__,"check_license")
        self.client.logout()

        
class LogoutViewsTestCase(TestCase):

    def test_logout(self):
        resp = self.client.get(reverse("logout"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))

class RootViewsTestCase(TestCase):

    def test_root_url(self):
        resp = self.client.get(reverse("root"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertIn(settings.HOME_URL, (i[0] for i in resp.redirect_chain))


class ProfileViewsTestCase(TestCase):

    def initialise(self):
        self.username = "profiletestuser"
        self.password ="profiletestpass"
        self.credentials = {"first_name": "test","last_name" : "test" ,"email" : "profiletest@spdx.org",'username':self.username,'password':self.password }
        self.user = User.objects.create_user(**self.credentials)
        UserID.objects.get_or_create({"user":self.user,"organisation":"spdx"})

    def test_profile(self):
        resp = self.client.get(reverse("profile"),follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        self.assertNotEqual(resp.redirect_chain,[])
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='profiletestuser')[0])
        
        resp2 = self.client.get(reverse("profile"),follow=True,secure=True)
        self.assertEqual(resp2.status_code,200)
        self.assertEqual(resp2.redirect_chain,[])
        self.assertIn("app/profile.html",(i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__,"profile")
        self.assertIn("form",resp2.context)
        self.assertIn("info_form",resp2.context)
        self.assertIn("orginfo_form",resp2.context)
        self.client.logout()

    def test_saveinfo(self):
        self.initialise()
        user = User.objects.get_or_create(username='profiletestuser')[0]
        userid = UserID.objects.get_or_create(user=user)[0]
        self.assertEqual(user.first_name,"test")
        self.assertEqual(user.last_name,"test")
        self.assertEqual(user.email,"profiletest@spdx.org")
        self.assertEqual(userid.organisation,"spdx")
        self.client.force_login(user)
        
        save_info_resp = self.client.post(reverse("profile"),{'saveinfo':'saveinfo',"first_name": "john","last_name" : "doe" ,"email" : "johndoe@spdx.org","organisation":"Software Package Data Exchange"},follow=True,secure=True)
        self.assertEqual(save_info_resp.status_code,200)
        self.assertEqual(save_info_resp.redirect_chain,[])
        self.assertEqual(save_info_resp.context["success"],"Details Successfully Updated")
        user = User.objects.get_or_create(username='profiletestuser')[0]
        userid = UserID.objects.get_or_create(user=user)[0]
        self.assertEqual(user.first_name,"john")
        self.assertEqual(user.last_name,"doe")
        self.assertEqual(user.email,"johndoe@spdx.org")
        self.assertEqual(userid.organisation,"Software Package Data Exchange")
        self.client.logout()

    def test_changepwd(self):
        self.initialise()
        resp = self.client.login(username='profiletestuser', password='profiletestpass')
        self.assertTrue(resp)
        change_pwd_resp = self.client.post(reverse("profile"),{'changepwd':'changepwd',"old_password": self.password,"new_password1" : "johndoepass" ,"new_password2" : "johndoepass"},follow=True,secure=True)
        self.assertEqual(change_pwd_resp.status_code,200)
        self.assertEqual(change_pwd_resp.redirect_chain,[])
        self.assertEqual(change_pwd_resp.context["success"],"Your password was successfully updated!")
        self.client.logout()
        
        resp2 = self.client.login(username='profiletestuser', password='profiletestpass')
        self.assertFalse(resp2)
        
        resp3 = self.client.login(username='profiletestuser', password='johndoepass')
        self.assertTrue(resp3)
        self.client.logout()


class CheckUserNameTestCase(TestCase):

    def initialise(self):
        self.username = "checktestuser"
        self.password ="checktestpass"
        self.credentials = {'username':self.username,'password':self.password }
        User.objects.create_user(**self.credentials)

    def test_check_username(self):
        resp = self.client.post(reverse("check-username"),{"username":"spdx"},follow=True,secure=True)
        self.assertEqual(resp.status_code,200)
        
        resp2 = self.client.post(reverse("check-username"),{"randomkey":"randomvalue"},follow=True,secure=True)
        self.assertEqual(resp2.status_code,400)
        
        self.initialise()
        resp3 = self.client.post(reverse("check-username"),{"username":"checktestuser"},follow=True,secure=True)
        self.assertEqual(resp3.status_code,404)
