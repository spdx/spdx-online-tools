# SPDX-FileCopyrightText: 2026-present SPDX contributors
# SPDX-License-Identifier: Apache-2.0

"""Django management command for cleaning up old media files."""

from argparse import ArgumentTypeError

from django.core.management.base import BaseCommand

from app.scripts.cleanup import clean_media


def _non_negative_int(value):
    parsed = int(value)
    if parsed < 0:
        raise ArgumentTypeError("days-threshold must be non-negative")
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
        clean_media(days_threshold=options["days_threshold"])
