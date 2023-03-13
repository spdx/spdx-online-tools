import datetime
import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Deletes files older than 10 days'

    def handle(self, *args, **options):
        # specify the directory to clean up
        directory = os.path.join(os.getcwd(), 'test_dir')

        # get the current time
        now = datetime.datetime.now()

        # set the threshold for file age
        threshold = now - datetime.timedelta(days=10)

        # loop over all files in the directory
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                # get the file creation time
                creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                # delete the file if it's older than the threshold
                if threshold < creation_time:
                    os.remove(file_path)
                    self.stdout.write(f'Deleted file: {file_path}')
