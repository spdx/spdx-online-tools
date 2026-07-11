# -*- coding: utf-8 -*-
"""
Tests for cron jobs and cleanup scripts.
"""

import datetime
import os
import shutil
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from app.scripts.cleanup import clean_media


class TestCronJob(TestCase):
    def test_clean_media_deletes_only_expired_files(self):
        """Check if the files older than 10 days are getting deleted"""
        test_dir = os.path.join(settings.MEDIA_ROOT, "AnonymousUser")
        os.makedirs(test_dir, exist_ok=True)
        self.addCleanup(shutil.rmtree, test_dir, True)
        for i in range(1, 11):
            file_path = os.path.join(test_dir, f"test_file_{i}.txt")
            with open(file_path, "w") as f:
                f.write("test")
            # set file creation time to 11 days ago
            if i <= 5:
                creation_time = datetime.datetime.now() - datetime.timedelta(days=11)
                os.utime(
                    file_path, (creation_time.timestamp(), creation_time.timestamp())
                )

        # check that only files older than 10 days were deleted
        deleted_files = clean_media()

        self.assertEqual(
            [file_info["name"] for file_info in deleted_files],
            [f"test_file_{i}.txt" for i in range(1, 6)],
        )
        for file_info in deleted_files:
            self.assertIn("modified_at", file_info)

        for i in range(1, 11):
            file_path = os.path.join(test_dir, f"test_file_{i}.txt")
            if i <= 5:
                self.assertFalse(
                    os.path.exists(file_path), f"{file_path} should have been deleted"
                )
            else:
                self.assertTrue(
                    os.path.exists(file_path),
                    f"{file_path} should not have been deleted",
                )

    def test_cleanup_management_command(self):
        """cleanup_media command delegates with correct threshold values"""
        with patch(
            "app.management.commands.cleanup_media.clean_media", return_value=[]
        ) as clean_media_mock:
            call_command("cleanup_media")
            call_command("cleanup_media", "--days-threshold", "30")

        self.assertEqual(clean_media_mock.call_count, 2)
        clean_media_mock.assert_any_call(days_threshold=10)
        clean_media_mock.assert_any_call(days_threshold=30)
