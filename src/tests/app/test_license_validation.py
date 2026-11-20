# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""Validate license matcher candidates independently of the matcher database."""

import gzip
import time
from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.test import SimpleTestCase
from spdx_license_matcher.computation import get_close_matches
from spdx_license_matcher.normalize import normalize

from app import utils


class LicenseValidationTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.db = Mock()
        self.db.keys.return_value = [b"MIT"]
        self.db.mget.return_value = [b"text"]
        self.start_patch("valkey.StrictRedis", return_value=self.db)
        self.start_patch("_ensure_license_db_current")
        self.response = Mock()
        self.response.json.return_value = {
            "licenses": [{"licenseId": "MIT"}, {"licenseId": "Apache-2.0"}]
        }
        self.get = self.start_patch("requests.get", return_value=self.response)
        self.matcher = self.start_patch("get_close_matches", return_value={"MIT": 1.0})
        self.listed = self.start_patch("getListedLicense")
        self.standard = self.start_patch("checkTextStandardLicense", return_value=True)

    def start_patch(self, name, **kwargs):
        patcher = patch("app.utils." + name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def test_unlisted_perfect_match_is_rejected(self):
        self.db.keys.return_value = [b"CIArtistic"]
        self.matcher.return_value = {"CIArtistic": 1.0}
        self.assertEqual(utils.check_spdx_license("text"), (None, "No match", {}))
        self.listed.assert_not_called()

    def test_invalid_id_syntax_is_rejected(self):
        for license_id in ("", "MIT_", "MIT\n", "MIT OR Apache-2.0", "MİT", "LicenseRef:MIT"):
            with self.subTest(license_id=license_id):
                cache.clear()
                self.db.keys.return_value = [license_id.encode()]
                # Syntax is required even if corrupt upstream data contains this ID.
                self.response.json.return_value = {"licenses": [{"licenseId": license_id}]}
                self.matcher.return_value = {license_id: 1.0}
                self.assertEqual(utils.check_spdx_license("text"), (None, "No match", {}))

    def test_listed_perfect_match_preserves_result(self):
        self.assertEqual(utils.check_spdx_license("text"), ("MIT", "Perfect match", {"MIT": 1.0}))
        self.response.raise_for_status.assert_called_once()

    def test_listed_ids_are_case_insensitive(self):
        self.db.keys.return_value = [b"mIt"]
        self.matcher.return_value = {"mIt": 1.0}
        self.assertEqual(utils.check_spdx_license("text")[0], "mIt")

    def test_unlisted_close_match_never_reaches_java_lookup(self):
        self.matcher.return_value = {"CIArtistic": 0.99, "MIT": 0.95}
        self.assertEqual(utils.check_spdx_license("text"), ("MIT", "Close match", {"MIT": 0.95}))
        self.listed.assert_called_once_with("MIT")

    def test_standard_match_preserves_result(self):
        self.matcher.return_value = {"MIT": 0.95}
        self.standard.return_value = False
        self.assertEqual(utils.check_spdx_license("text"), ("MIT", "Standard License match", {"MIT": 0.95}))

    def test_filtered_input_does_not_hide_valid_close_match(self):
        text = "Permission is hereby granted to use this software without restriction."
        close = text.replace("restriction", "restrictions")
        self.db.keys.return_value = [b"CIArtistic", b"MIT"]
        self.db.mget.return_value = [
            gzip.compress(normalize(text).encode()),
            gzip.compress(normalize(close).encode()),
        ]
        # The real matcher drops all close matches when any perfect match exists.
        self.matcher.side_effect = get_close_matches
        result = utils.check_spdx_license(text)
        self.assertEqual(result[0], "MIT")
        self.assertEqual(result[1], "Close match")
        self.assertEqual(list(result[2]), ["MIT"])

    def test_list_is_cached_but_refetched_after_expiration(self):
        utils.check_spdx_license("text")
        utils.check_spdx_license("text")
        self.get.assert_called_once_with("https://spdx.org/licenses/licenses.json", timeout=30)
        with patch("time.time", return_value=time.time() + 3601):
            utils.check_spdx_license("text")
        self.assertEqual(self.get.call_count, 2)

    def test_non_ascii_or_non_string_ids_are_rejected(self):
        for value in (None, 123, b"\xff", "MIT_", "MİT", "MIT\n"):
            with self.subTest(value=value):
                self.db.keys.return_value = [value]
                self.assertEqual(utils.check_spdx_license("text"), (None, "No match", {}))

    def test_listed_deprecated_id_is_not_excluded(self):
        cache.clear()
        self.db.keys.return_value = [b"GPL-2.0"]
        self.response.json.return_value = {
            "licenses": [{"licenseId": "GPL-2.0", "isDeprecatedLicenseId": True}]
        }
        self.matcher.return_value = {"GPL-2.0": 1.0}
        self.assertEqual(utils.check_spdx_license("text")[0], "GPL-2.0")

    def test_fetch_failure_is_not_reported_as_no_match_or_cached(self):
        self.get.side_effect = requests.Timeout("license list unavailable")
        with self.assertRaises(requests.Timeout):
            utils.check_spdx_license("text")
        self.get.side_effect = None
        self.assertEqual(utils.check_spdx_license("text")[0], "MIT")
        self.assertEqual(self.get.call_count, 2)

    def test_http_error_is_not_reported_as_no_match(self):
        self.response.raise_for_status.side_effect = requests.HTTPError("server error")
        with self.assertRaises(requests.HTTPError):
            utils.check_spdx_license("text")

    def test_malformed_list_is_not_reported_as_no_match(self):
        for data in ({}, {"licenses": []}, {"licenses": [{"name": "MIT"}]}):
            with self.subTest(data=data):
                cache.clear()
                self.response.json.return_value = data
                with self.assertRaises((KeyError, ValueError)):
                    utils.check_spdx_license("text")

    def test_empty_database_remains_no_match(self):
        self.db.keys.return_value = []
        self.db.mget.return_value = []
        self.matcher.return_value = {}
        self.assertEqual(utils.check_spdx_license("text"), (None, "No match", {}))
