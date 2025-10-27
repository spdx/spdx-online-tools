import os
import time
import datetime
from django.conf import settings
import logging

logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(os.path.join(os.getcwd(), "deletedFiles.log"))
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

def cleanMedia():
    MEDIA_DIR = os.path.join(settings.MEDIA_ROOT, "AnonymousUser")
    DAYS_THRESHOLD = 10

    now = time.time()

    # log the time of the cron job
    logger.info('Cron job ran at %s', now)
    
    for filename in os.listdir(MEDIA_DIR):
        filepath = os.path.join(MEDIA_DIR, filename)
        if os.path.isfile(filepath) and (now - os.stat(filepath).st_mtime) > (DAYS_THRESHOLD * 86400):
            # log the file being deleted and the date of the file
            file_date = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
            logger.info('Deleting file %s with date %s', filename, file_date)
            os.remove(filepath)
            