# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""
Regression test for https://github.com/spdx/spdx-online-tools/issues/602

``issue()`` (app/views.py) reads every field required for a new-license
GitHub issue straight out of ``request.POST[...]``. A missing field raises
an uncaught ``KeyError``, which the outer ``except Exception:`` in the view
turns into an HTTP 500 whose body is the *raw Python traceback*
(``format_exc()``), exposing internal file paths and line numbers to the
browser instead of telling the submitter what went wrong. A well-formed
request that is merely missing one field should get a clean 400 naming the
missing field instead of an unhandled server error with a stack trace.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from social_django.models import UserSocialAuth


class IssueMissingFieldTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="issue602-test-user", is_active=True)
        UserSocialAuth.objects.create(
            provider="github",
            uid="issue602-uid",
            extra_data={"access_token": "fake-token", "login": "issue602-test-user"},
            user=self.user,
        )
        self.client.force_login(self.user)

    def _full_payload(self):
        return {
            "licenseAuthorName": "Test Author",
            "licenseName": "Test License",
            "licenseIdentifier": "TEST-1.0",
            "licenseOsi": "false",
            "licenseSourceUrls": ["http://example.com/license"],
            "exampleUrl": [],
            "licenseHeader": "",
            "comments": "test comment",
            "inputLicenseText": "<text/>",
            "licenseNotes": "",
            "listVersionAdded": "",
            "matchIds": "",
            "diffUrl": "",
        }

    def test_missing_field_returns_clean_400_not_a_raw_traceback_500(self):
        """POST without 'licenseAuthorName' must fail with a clean 400, not a
        500 dumping a Python stack trace into the response body."""
        payload = self._full_payload()
        del payload["licenseAuthorName"]

        resp = self.client.post(reverse("issue"), payload, secure=True)

        body = resp.content.decode(errors="replace")
        self.assertEqual(
            resp.status_code, 400,
            "a missing POST field must be reported as a 400, not surface as "
            "an unhandled 500 (got status {0}, body starts: {1!r})".format(
                resp.status_code, body[:200]),
        )
        self.assertIn("licenseAuthorName", body)
        self.assertNotIn("Traceback (most recent call last)", body)

    def test_all_fields_present_still_reaches_normal_flow(self):
        """Sanity check: with every field present, the view must get past the
        new validation block (it will then fail trying to reach the real
        GitHub API with a fake token, which is expected and out of scope
        here -- it must NOT fail as a 400 'missing field' response)."""
        resp = self.client.post(reverse("issue"), self._full_payload(), secure=True)
        self.assertNotEqual(resp.status_code, 400)
