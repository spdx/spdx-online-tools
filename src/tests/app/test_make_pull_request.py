# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Regression test for https://github.com/spdx/spdx-online-tools/issues/430

``makePullRequest`` (app/utils/__init__.py) assumed that a contributor's fork
of the license-list-XML repo is always named exactly ``settings.LICENSE_REPO_NAME``
(or ``settings.NAMESPACE_REPO_NAME`` for namespaces). If the user renamed their
fork -- which GitHub itself does automatically when the default name already
exists in their account -- every API call addressing ``repos/{username}/{repo}``
pointed at a repository that does not exist, and the submission failed with a
generic "Please try again later or contact the SPDX Team" error.
"""

import json
from unittest.mock import Mock, patch

from django.conf import settings
from django.test import TestCase

from app import utils


class MakePullRequestForkNameTestCase(TestCase):

    ACTUAL_FORK_NAME = "my-renamed-fork"
    USERNAME = "forktestuser"

    def _forks_list_response(self):
        return Mock(status_code=200, text=json.dumps([
            {"owner": {"login": self.USERNAME}, "name": self.ACTUAL_FORK_NAME},
        ]))

    def _fake_get(self, url, headers=None, **kwargs):
        if url.endswith("/forks"):
            return self._forks_list_response()
        if "repos/{0}/".format(self.USERNAME) in url:
            # Only requests addressed to the fork's REAL name should succeed.
            if self.ACTUAL_FORK_NAME not in url:
                return Mock(status_code=404, text=json.dumps({"message": "Not Found"}))
            if url.endswith("/branches"):
                return Mock(status_code=200, text=json.dumps([]))
            return Mock(status_code=200, text=json.dumps({"object": {"sha": "deadbeef"}}))
        return Mock(status_code=404, text=json.dumps({"message": "Not Found"}))

    def _fake_post(self, url, headers=None, data=None, **kwargs):
        # Same rule as GET: only the real fork name is a valid target.
        if "repos/{0}/".format(self.USERNAME) in url and self.ACTUAL_FORK_NAME not in url:
            return Mock(status_code=404, text=json.dumps({"message": "Not Found"}))
        # Stop the flow right after branch creation succeeds/fails; we only
        # need to observe which URLs were addressed, not complete a real PR.
        return Mock(status_code=404, text=json.dumps({"message": "stopped by test double"}))

    def test_uses_actual_fork_name_not_hardcoded_settings_name(self):
        with patch("app.utils.requests.get", side_effect=self._fake_get) as mock_get, \
             patch("app.utils.requests.post", side_effect=self._fake_post) as mock_post:
            utils.makePullRequest(
                username=self.USERNAME,
                token="test-token",
                branchName="add-0BSD",
                updateUpstream="false",
                fileName="0BSD.xml",
                commitMessage="Add 0BSD",
                prTitle="Add 0BSD",
                prBody="body",
                xmlText="<xml/>",
                plainText="text",
                isException=False,
                is_ns=False,
            )

        own_repo_calls = [
            c.args[0] for c in (mock_get.call_args_list + mock_post.call_args_list)
            if "repos/{0}/".format(self.USERNAME) in c.args[0]
        ]
        self.assertTrue(own_repo_calls, "expected at least one request against the user's fork")

        wrong_name_calls = [
            u for u in own_repo_calls
            if settings.LICENSE_REPO_NAME in u and self.ACTUAL_FORK_NAME not in u
        ]
        self.assertEqual(
            wrong_name_calls, [],
            "makePullRequest addressed the fork using settings.LICENSE_REPO_NAME "
            "instead of the fork's actual name ({0}): {1}".format(
                self.ACTUAL_FORK_NAME, wrong_name_calls),
        )
