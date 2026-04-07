import argparse
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from app.scripts.cleanup import clean_media


def _non_negative_int(value):
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("days-threshold must be non-negative")
    return parsed


class Command(BaseCommand):
    help = "Delete AnonymousUser media files older than the retention threshold."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days-threshold",
            type=_non_negative_int,
            default=10,
            help="Delete files older than this many days.",
        )

    def handle(self, *args, **options):
        started_at = datetime.now(tz=timezone.utc).isoformat()
        self.stdout.write(f"Cleanup started at {started_at}")

        deleted_files = clean_media(days_threshold=options["days_threshold"])
        for file_info in deleted_files:
            self.stdout.write(
                f"Deleted file: {file_info['name']} (modified at {file_info['modified_at']})"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Cleanup completed; deleted {len(deleted_files)} file(s)."
            )
        )
