# -*- coding: utf-8 -*-


from django.test import TestCase
from django.conf import settings

import datetime

from django.conf import settings
import os

from app.scripts.cleanup import cleanMedia



class TestCronJob(TestCase):
    def test_delete_old_files(self):
        """Check if the files older than 10 days are getting deleted or not"""
        # create a test directory with some files
        test_dir = os.path.join(settings.MEDIA_ROOT, 'AnonymousUser')
        os.makedirs(test_dir, exist_ok=True)
        for i in range(1, 11):
            file_path = os.path.join(test_dir, f'test_file_{i}.txt')
            with open(file_path, 'w') as f:
                f.write('test')
            # set file creation time to 11 days ago
            if i<=5: 
                creation_time = datetime.datetime.now() - datetime.timedelta(days=11)
                os.utime(file_path, (creation_time.timestamp(), creation_time.timestamp()))
        
        cleanMedia()

        # check that only files older than 10 days were deleted
        for i in range(1, 11):
            file_path = os.path.join(test_dir, f'test_file_{i}.txt')
            if i <= 5:
                self.assertFalse(os.path.exists(file_path), f'{file_path} should have been deleted')
            else:
                self.assertTrue(os.path.exists(file_path), f'{file_path} should not have been deleted')
            