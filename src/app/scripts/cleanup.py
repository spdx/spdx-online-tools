from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import time

from django.conf import settings

ANONYMOUS_MEDIA_SUBDIR = "AnonymousUser"
DEFAULT_DAYS_THRESHOLD = 10
SECONDS_PER_DAY = int(timedelta(days=1).total_seconds())


def clean_media(days_threshold=DEFAULT_DAYS_THRESHOLD, media_root=None):
    if days_threshold < 0:
        raise ValueError("days_threshold must be non-negative")

    media_dir = Path(media_root or settings.MEDIA_ROOT) / ANONYMOUS_MEDIA_SUBDIR
    deleted_files = []
    now = time()
    cutoff_seconds = days_threshold * SECONDS_PER_DAY

    if not media_dir.is_dir():
        return deleted_files

    for filepath in sorted(media_dir.iterdir()):
        if not filepath.is_file():
            continue

        modified_at = filepath.stat().st_mtime
        if (now - modified_at) <= cutoff_seconds:
            continue

        filepath.unlink()
        deleted_files.append(
            {
                "name": filepath.name,
                "modified_at": datetime.fromtimestamp(modified_at, tz=timezone.utc).isoformat(),
            }
        )

    return deleted_files
