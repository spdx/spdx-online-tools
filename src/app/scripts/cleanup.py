import os
import time
from django.conf import settings

def cleanMedia():
    MEDIA_DIR = settings.MEDIA_ROOT + "/AnonymousUser"
    DAYS_THRESHOLD = 10

    now = time.time()

    for filename in os.listdir(MEDIA_DIR):
        filepath = os.path.join(MEDIA_DIR, filename)
        if os.path.isfile(filepath) and (now - os.stat(filepath).st_mtime) > (DAYS_THRESHOLD * 86400):
            os.remove(filepath)
            