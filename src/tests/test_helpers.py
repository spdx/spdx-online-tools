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

import logging
import os
import shutil

import redis as redis_lib
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from social_django.models import UserSocialAuth
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from src.secret import getAccessToken, getGithubUserId, getGithubUserName, getRedisHost

os.environ.setdefault("WDM_PROGRESS_BAR", "0")
os.environ.setdefault("WDM_LOG", "0")


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
    except (redis_lib.exceptions.ConnectionError, Exception):
        return False


def github_creds_available():
    """Return True when all three GitHub secrets are set in secret.py."""
    return bool(getAccessToken() and getGithubUserId() and getGithubUserName())


# ---------------------------------------------------------------------------
# Selenium driver detection (runs once at import time)
# ---------------------------------------------------------------------------


def _init_selenium():
    # Attempt Firefox
    try:
        driver_path = shutil.which("geckodriver") or GeckoDriverManager().install()
        if (
            driver_path
            and os.path.isfile(driver_path)
            and os.access(driver_path, os.X_OK)
        ):
            return "firefox", driver_path
    except Exception as e:
        logging.warning(f"Firefox initialization failed or geckodriver not found: {e}")

    # Attempt Chrome
    try:
        driver_path = shutil.which("chromedriver") or ChromeDriverManager().install()
        if (
            driver_path
            and os.path.isfile(driver_path)
            and os.access(driver_path, os.X_OK)
        ):
            return "chrome", driver_path
    except Exception as e:
        logging.warning(f"Chrome initialization failed or chromedriver not found: {e}")

    return None, None


DRIVER_TYPE, DRIVER_PATH = _init_selenium()
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
                self.selenium = webdriver.Firefox(
                    service=FirefoxService(DRIVER_PATH), options=options
                )
            elif DRIVER_TYPE == "chrome":
                options = ChromeOptions()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                self.selenium = webdriver.Chrome(
                    service=ChromeService(DRIVER_PATH), options=options
                )

            self.selenium.set_window_size(1920, 1080)
        except Exception as e:
            self.skipTest(f"Failed to initialize {DRIVER_TYPE} driver: {e}")

        super(BaseSeleniumTestCase, self).setUp()

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
