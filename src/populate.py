# SPDX-FileCopyrightText: 2017-present SPDX Contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""Script to populate the database with license and exception names
from SPDX data."""

import json
import os

import django
import requests

# pylint: disable=line-too-long
LICENSE_URL = (
    "https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json"
)
EXCEPTION_URL = "https://raw.githubusercontent.com/spdx/license-list-data/master/json/exceptions.json"


def populate(url, item_type):
    """Fetch license or exception data from URL and populate the database."""
    from app.models import (  # pylint: disable=import-outside-toplevel
        LicenseNames,
    )

    response = requests.get(url, timeout=30)
    data = json.loads(response.text)
    total_count = 0
    new_count = 0
    for item in data[item_type]:
        total_count += 1
        created = LicenseNames.objects.get_or_create(  # pylint: disable=no-member
            name=item["name"]
        )[1]
        if created:
            new_count += 1
        if item_type == "licenses":
            LicenseNames.objects.get_or_create(  # pylint: disable=no-member
                name=item["licenseId"]
            )
        else:
            LicenseNames.objects.get_or_create(  # pylint: disable=no-member
                name=item["licenseExceptionId"]
            )
    return (total_count, new_count)


def main():
    """Setup Django environment and run population tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    print("Adding License names (this might take some time if running for first time)")
    licenses_total, licenses_new = populate(LICENSE_URL, "licenses")
    print(
        f"Total Licenses Found: {licenses_total}\n"
        f"New Licenses added to database: {licenses_new}"
    )

    print("Adding Exception names")
    exceptions_total, exceptions_new = populate(EXCEPTION_URL, "exceptions")
    print(
        f"Total Exceptions Found: {exceptions_total}\n"
        f"New Exceptions added to database: {exceptions_new}"
    )


if __name__ == "__main__":
    main()
