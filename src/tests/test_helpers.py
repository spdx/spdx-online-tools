# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Shared test infrastructure for app and API test suites.

Provides:
  - getExamplePath()           path helper for example SPDX files
  - isRedisAvailable()         skip predicate for Redis-dependent tests
  - github_creds_available()   skip predicate for GitHub-token tests
  - SELENIUM_AVAILABLE         bool; True when a webdriver is found
  - DRIVER_TYPE / DRIVER_PATH  detected webdriver info
  - BaseSeleniumTestCase       base class for Selenium tests
  - GitHubLoginMixin           logs a test client in via GitHub credentials

Import pattern (mirrors src.secret):
    from tests.test_helpers import (
        getExamplePath, BaseSeleniumTestCase, GitHubLoginMixin,
        github_creds_available, SELENIUM_AVAILABLE,
    )
"""

import os
import shutil

import redis as redis_lib
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    SELENIUM_IMPORTED = True
except ImportError:
    SELENIUM_IMPORTED = False
from social_django.models import UserSocialAuth

from src.secret import getAccessToken, getGithubUserId, getGithubUserName, getRedisHost


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def getExamplePath(filename):
    return os.path.join(settings.EXAMPLES_DIR, filename)


# ---------------------------------------------------------------------------
# Skip predicates
# ---------------------------------------------------------------------------


def isRedisAvailable():
    try:
        r = redis_lib.StrictRedis(host=getRedisHost(), port=6379, db=0)
        r.ping()
        return True
    except redis_lib.exceptions.RedisError:
        return False


def github_creds_available():
    """Return True when all three GitHub secrets are set in secret.py."""
    return bool(getAccessToken() and getGithubUserId() and getGithubUserName())


# ---------------------------------------------------------------------------
# Selenium driver detection (runs once at import time)
# ---------------------------------------------------------------------------


def _detect_browser():
    # 1. Try resolving via PATH (works on Linux/macOS, and Windows if on PATH)
    for browser in ["chrome", "google-chrome", "chromium", "chrome.exe", "google-chrome.exe", "chromium.exe"]:
        if shutil.which(browser):
            return "chrome"
    for browser in ["firefox", "firefox.exe"]:
        if shutil.which(browser):
            return "firefox"

    # 2. Try standard macOS paths
    if os.path.exists("/Applications/Google Chrome.app"):
        return "chrome"
    if os.path.exists("/Applications/Firefox.app"):
        return "firefox"

    # 3. Try standard Windows paths
    if os.name == "nt":
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        local_app_data = os.environ.get("LocalAppData", os.path.expanduser("~\\AppData\\Local"))
        
        chrome_paths = [
            os.path.join(program_files, "Google\\Chrome\\Application\\chrome.exe"),
            os.path.join(program_files_x86, "Google\\Chrome\\Application\\chrome.exe"),
            os.path.join(local_app_data, "Google\\Chrome\\Application\\chrome.exe"),
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                return "chrome"
                
        firefox_paths = [
            os.path.join(program_files, "Mozilla Firefox\\firefox.exe"),
            os.path.join(program_files_x86, "Mozilla Firefox\\firefox.exe"),
        ]
        for path in firefox_paths:
            if os.path.exists(path):
                return "firefox"

    return None


DRIVER_TYPE = _detect_browser() if SELENIUM_IMPORTED else None
SELENIUM_AVAILABLE = DRIVER_TYPE is not None


# ---------------------------------------------------------------------------
# Base classes
# ---------------------------------------------------------------------------


class BaseSeleniumTestCase(StaticLiveServerTestCase):
    # @skipIf is intentionally kept alongside this setUp check to skip
    # the class before any fixtures are set up, which is faster.
    def setUp(self):
        if not SELENIUM_AVAILABLE:
            self.skipTest("No supported webdriver (Firefox or Chrome) available")

        try:
            if DRIVER_TYPE == "firefox":
                options = FirefoxOptions()
                options.add_argument("-headless")
                self.selenium = webdriver.Firefox(options=options)
            elif DRIVER_TYPE == "chrome":
                options = ChromeOptions()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                self.selenium = webdriver.Chrome(options=options)

            self.selenium.set_window_size(1920, 1080)
        except Exception as e:
            self.skipTest(f"Failed to initialize {DRIVER_TYPE} driver: {e}")

        super(BaseSeleniumTestCase, self).setUp()

    def disable_animations(self):
        """Disable CSS transitions, animations, and jQuery effects to prevent timing flakes."""
        disable_effects = """
        if (window.jQuery) {
            jQuery.fx.off = true;
            jQuery('.fade').removeClass('fade');
        }
        var style = document.createElement('style');
        style.type = 'text/css';
        style.innerHTML = '* { transition: none !important; animation: none !important; }';
        document.head.appendChild(style);
        """
        try:
            self.selenium.execute_script(disable_effects)
        except Exception:
            pass

    def tearDown(self):
        if hasattr(self, "selenium"):
            self.selenium.quit()
        super(BaseSeleniumTestCase, self).tearDown()


class GitHubLoginMixin:
    """Mixin for test cases that need a GitHub-authenticated session.

    Call self.githubLogin() in setUp or in individual tests that require it.
    The test class must also inherit from TestCase (or a subclass).
    """

    def githubLogin(self):
        TEST_LOGIN_INFO = {
            "provider": "github",
            "uid": str(getGithubUserId()),
            "access_token": getAccessToken(),
            "login": getGithubUserName(),
            "id": getGithubUserId(),
            "password": "pass",
        }
        self.user = User.objects.create(
            username=TEST_LOGIN_INFO["login"], is_active=True, is_superuser=True
        )
        self.user.set_password(TEST_LOGIN_INFO["password"])
        self.user.save()
        UserSocialAuth.objects.create(
            provider=TEST_LOGIN_INFO["provider"],
            uid=TEST_LOGIN_INFO["uid"],
            extra_data=TEST_LOGIN_INFO,
            user=self.user,
        )
        self.user = authenticate(
            username=TEST_LOGIN_INFO["login"], password=TEST_LOGIN_INFO["password"]
        )
        login = self.client.login(
            username=TEST_LOGIN_INFO["login"], password=TEST_LOGIN_INFO["password"]
        )
        return login
