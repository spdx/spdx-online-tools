# SPDX-FileCopyrightText: 2017-present SPDX contributors
# SPDX-License-Identifier: Apache-2.0

"""
Cleanup script for removing old files from the media directory.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from time import time

from django.conf import settings

ANONYMOUS_MEDIA_SUBDIR = "AnonymousUser"
DEFAULT_DAYS_THRESHOLD = 10
SECONDS_PER_DAY = 86400  # 1 day
logger = logging.getLogger("app.cleanup")
logger.setLevel(logging.INFO)


def _setup_logger():
    log_file = Path(settings.PROJECT_ROOT) / "container_logs" / "deletedFiles.log"

    if not any(
        isinstance(handler, logging.FileHandler)
        and Path(handler.baseFilename).resolve() == log_file.resolve()
        for handler in logger.handlers
    ):
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)


def clean_media(days_threshold=DEFAULT_DAYS_THRESHOLD, media_root=None):
    _setup_logger()
    if days_threshold < 0:
        raise ValueError("days_threshold must be non-negative")

    media_dir = Path(media_root or settings.MEDIA_ROOT) / ANONYMOUS_MEDIA_SUBDIR
    deleted_files = []
    now = time()
    cutoff_seconds = days_threshold * SECONDS_PER_DAY
    logger.info(
        "Cleanup job started at %s",
        datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
    )

    if not media_dir.is_dir():
        logger.info("Cleanup skipped because directory does not exist: %s", media_dir)
        return deleted_files

    for filepath in sorted(media_dir.iterdir()):
        if not filepath.is_file():
            continue

        modified_at = filepath.stat().st_mtime
        if (now - modified_at) <= cutoff_seconds:
            continue

        try:
            filepath.unlink()
        except OSError:
            logger.exception("Failed to delete %s", filepath.name)
            continue
        logger.info(
            "Deleted file %s with modified date %s",
            filepath.name,
            datetime.fromtimestamp(modified_at, tz=timezone.utc).strftime("%Y-%m-%d"),
        )
        deleted_files.append(
            {
                "name": filepath.name,
                "modified_at": datetime.fromtimestamp(
                    modified_at, tz=timezone.utc
                ).isoformat(),
            }
        )

    return deleted_files
