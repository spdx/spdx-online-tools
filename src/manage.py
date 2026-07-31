#!/usr/bin/env python
# SPDX-FileCopyrightText: 2018-present SPDX Contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""Django's command-line utility for administrative tasks."""

import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        # pylint: disable=import-outside-toplevel
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing.
        try:
            # pylint: disable=import-outside-toplevel,unused-import
            import django
        except ImportError as exc_django:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            ) from exc_django
        raise exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
