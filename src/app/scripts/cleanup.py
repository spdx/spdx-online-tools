import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import time

from django.conf import settings

ANONYMOUS_MEDIA_SUBDIR = "AnonymousUser"
DEFAULT_DAYS_THRESHOLD = 10
SECONDS_PER_DAY = int(timedelta(days=1).total_seconds())
LOG_FILE = Path(settings.PROJECT_ROOT) / "container_logs" / "deletedFiles.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


logger = logging.getLogger("app.cleanup")
logger.setLevel(logging.INFO)

if not any(
    isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == LOG_FILE
    for handler in logger.handlers
):
    handler = logging.FileHandler(LOG_FILE)
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)


def clean_media(days_threshold=DEFAULT_DAYS_THRESHOLD, media_root=None):
    if days_threshold < 0:
        raise ValueError("days_threshold must be non-negative")

    media_dir = Path(media_root or settings.MEDIA_ROOT) / ANONYMOUS_MEDIA_SUBDIR
    deleted_files = []
    now = time()
    cutoff_seconds = days_threshold * SECONDS_PER_DAY
    logger.info("Cleanup job started at %s", datetime.fromtimestamp(now, tz=timezone.utc).isoformat())

    if not media_dir.is_dir():
        logger.info("Cleanup skipped because directory does not exist: %s", media_dir)
        return deleted_files

    for filepath in sorted(media_dir.iterdir()):
        if not filepath.is_file():
            continue

        modified_at = filepath.stat().st_mtime
        if (now - modified_at) <= cutoff_seconds:
            continue

        filepath.unlink()
        logger.info("Deleting file %s with date %s", filepath.name, datetime.fromtimestamp(modified_at, tz=timezone.utc).isoformat())
        deleted_files.append(
            {
                "name": filepath.name,
                "modified_at": datetime.fromtimestamp(modified_at, tz=timezone.utc).isoformat(),
            }
        )

    return deleted_files
