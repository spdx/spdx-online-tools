# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import UserID


class LoginViewsTestCase(TestCase):

    def initialise(self):
        """Create users"""
        self.credentials = {"username": "testuser", "password": "testpass"}
        user = User.objects.create_user(**self.credentials)
        user.is_staff = True
        user.is_active = True
        user.save()
        self.credentials2 = {"username": "testuser2", "password": "testpass2"}
        user2 = User.objects.create_user(**self.credentials2)
        user2.is_staff = False
        user2.is_active = True
        user2.save()
        self.credentials3 = {"username": "testuser3", "password": "testpass3"}
        user3 = User.objects.create_user(**self.credentials3)
        user3.is_staff = True
        user3.is_active = False
        user3.save()

    def test_login(self):
        """GET Request for login"""
        resp = self.client.get(reverse("login"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain, [])
        self.assertIn("app/login.html", (i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__, "loginuser")

    def test_postlogin(self):
        """POST Request for index with different user types."""
        self.initialise()
        resp = self.client.post(
            reverse("login"), self.credentials, follow=True, secure=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.redirect_chain, [])
        self.assertIn(settings.LOGIN_REDIRECT_URL, (i[0] for i in resp.redirect_chain))
        self.assertTrue(resp.context['user'].is_active)
        self.assertTrue(resp.context['user'].is_staff)
        self.assertFalse(resp.context['user'].is_superuser)
        self.client.get(reverse("logout"))

        resp2 = self.client.post(
            reverse("login"), self.credentials2, follow=True, secure=True
        )
        self.assertEqual(resp2.status_code, 403)
        self.assertEqual(resp2.redirect_chain, [])
        self.assertFalse(resp2.context['user'].is_active)
        self.assertFalse(resp2.context['user'].is_staff)
        self.assertFalse(resp2.context['user'].is_superuser)
        self.assertTrue('invalid' in resp2.context)
        self.assertIn("app/login.html", (i.name for i in resp2.templates))
        self.client.get(reverse("logout"))

        resp3 = self.client.post(
            reverse("login"), self.credentials3, follow=True, secure=True
        )
        self.assertEqual(resp3.status_code, 403)
        self.assertEqual(resp3.redirect_chain, [])
        self.assertFalse(resp3.context['user'].is_active)
        self.assertFalse(resp3.context['user'].is_staff)
        self.assertFalse(resp3.context['user'].is_superuser)
        self.assertTrue('invalid' in resp3.context)
        self.assertIn("app/login.html", (i.name for i in resp3.templates))
        self.client.get(reverse("logout"))


class RegisterViewsTestCase(TestCase):

    def initialise(self):
        self.username = "testuser4"
        self.password = "testpass4"
        self.data = {
            "first_name": "test",
            "last_name": "test",
            "email": "test@spdx.org",
            "username": self.username,
            "password": self.password,
            "confirm_password": self.password,
            "organisation": "spdx",
        }

    def test_register(self):
        """GET Request for register"""
        resp = self.client.get(reverse("register"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('user_form' in resp.context)
        self.assertTrue('profile_form' in resp.context)
        self.assertEqual(resp.redirect_chain, [])
        self.assertIn("app/register.html", (i.name for i in resp.templates))
        self.assertEqual(resp.resolver_match.func.__name__, "register")

    def test_formregister(self):
        """POST Request for register"""
        self.initialise()
        resp = self.client.post(reverse("register"), self.data, follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.redirect_chain, [])
        self.assertIn(settings.REGISTER_REDIRECT_URL, (i[0] for i in resp.redirect_chain))

        loginresp = self.client.post(
            reverse("login"),
            {"username": self.username, "password": self.password},
            follow=True,
            secure=True,
        )
        self.assertEqual(loginresp.status_code, 200)
        self.assertTrue(loginresp.context['user'].is_active)
        self.assertTrue(loginresp.context['user'].is_staff)
        self.assertFalse(loginresp.context['user'].is_superuser)
        self.assertIn(settings.LOGIN_REDIRECT_URL, (i[0] for i in loginresp.redirect_chain))
        self.client.get(reverse("logout"))


class LogoutViewsTestCase(TestCase):

    def test_logout(self):
        self.client.force_login(User.objects.get_or_create(username='logouttestuser')[0])
        resp = self.client.get(reverse("logout"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))


class RootViewsTestCase(TestCase):

    def test_root_url(self):
        resp = self.client.get(reverse("root"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(settings.HOME_URL, (i[0] for i in resp.redirect_chain))


class ProfileViewsTestCase(TestCase):

    def initialise(self):
        self.username = "profiletestuser"
        self.password = "profiletestpass"
        self.credentials = {"first_name": "test", "last_name": "test", "email": "profiletest@spdx.org", 'username': self.username, 'password': self.password}
        self.user = User.objects.create_user(**self.credentials)
        UserID.objects.get_or_create({"user": self.user, "organisation": "spdx"})

    def test_profile(self):
        """GET Request for profile"""
        resp = self.client.get(reverse("profile"), follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.redirect_chain, [])
        self.assertIn(settings.LOGIN_URL, (i[0] for i in resp.redirect_chain))
        self.initialise()
        self.client.force_login(User.objects.get_or_create(username='profiletestuser')[0])

        resp2 = self.client.get(reverse("profile"), follow=True, secure=True)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.redirect_chain, [])
        self.assertIn("app/profile.html", (i.name for i in resp2.templates))
        self.assertEqual(resp2.resolver_match.func.__name__, "profile")
        self.assertIn("form", resp2.context)
        self.assertIn("info_form", resp2.context)
        self.assertIn("orginfo_form", resp2.context)
        self.client.logout()

    def test_saveinfo(self):
        """POST Request for saving information"""
        self.initialise()
        user = User.objects.get_or_create(username='profiletestuser')[0]
        userid = UserID.objects.get_or_create(user=user)[0]
        self.assertEqual(user.first_name, "test")
        self.assertEqual(user.last_name, "test")
        self.assertEqual(user.email, "profiletest@spdx.org")
        self.assertEqual(userid.organisation, "spdx")
        self.client.force_login(user)

        save_info_resp = self.client.post(reverse("profile"), {'saveinfo': 'saveinfo', "first_name": "john", "last_name": "doe", "email": "johndoe@spdx.org", "organisation": "Software Package Data Exchange"}, follow=True, secure=True)
        self.assertEqual(save_info_resp.status_code, 200)
        self.assertEqual(save_info_resp.redirect_chain, [])
        self.assertEqual(save_info_resp.context["success"], "Details Successfully Updated")
        user = User.objects.get_or_create(username='profiletestuser')[0]
        userid = UserID.objects.get_or_create(user=user)[0]
        self.assertEqual(user.first_name, "john")
        self.assertEqual(user.last_name, "doe")
        self.assertEqual(user.email, "johndoe@spdx.org")
        self.assertEqual(userid.organisation, "Software Package Data Exchange")
        self.client.logout()

    def test_changepwd(self):
        """POST Request for changing password"""
        self.initialise()
        resp = self.client.login(username='profiletestuser', password='profiletestpass')
        self.assertTrue(resp)
        change_pwd_resp = self.client.post(reverse("profile"), {'changepwd': 'changepwd', "old_password": self.password, "new_password1": "johndoepass", "new_password2": "johndoepass"}, follow=True, secure=True)
        self.assertEqual(change_pwd_resp.status_code, 200)
        self.assertEqual(change_pwd_resp.redirect_chain, [])
        self.assertEqual(change_pwd_resp.context["success"], "Your password was successfully updated!")
        self.client.logout()

        resp2 = self.client.login(username='profiletestuser', password='profiletestpass')
        self.assertFalse(resp2)

        resp3 = self.client.login(username='profiletestuser', password='johndoepass')
        self.assertTrue(resp3)
        self.client.logout()


class CheckUserNameTestCase(TestCase):

    def initialise(self):
        self.username = "checktestuser"
        self.password = "checktestpass"
        self.credentials = {'username': self.username, 'password': self.password}
        User.objects.create_user(**self.credentials)

    def test_check_username(self):
        """POST Request for checking username"""
        resp = self.client.post(reverse("check-username"), {"username": "spdx"}, follow=True, secure=True)
        self.assertEqual(resp.status_code, 200)

        resp2 = self.client.post(reverse("check-username"), {"randomkey": "randomvalue"}, follow=True, secure=True)
        self.assertEqual(resp2.status_code, 400)

        self.initialise()
        resp3 = self.client.post(reverse("check-username"), {"username": "checktestuser"}, follow=True, secure=True)
        self.assertEqual(resp3.status_code, 404)
