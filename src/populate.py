import json
import os

import django
import requests


def populate(url, _type):
    data = requests.get(url).text
    data = json.loads(data)
    _total_count = 0
    _new_count = 0
    for i in data[_type]:
        _total_count += 1
        response = LicenseNames.objects.get_or_create(name=i["name"])[1]
        if response:
            _new_count += 1
        if _type == "licenses":
            LicenseNames.objects.get_or_create(name=i["licenseId"])
        else:
            LicenseNames.objects.get_or_create(name=i["licenseExceptionId"])
    return _total_count, _new_count


if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
    django.setup()
    from app.models import LicenseNames

    license_url = "https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json"
    exception_url = "https://raw.githubusercontent.com/spdx/license-list-data/master/json/exceptions.json"

    print("Adding License names (this might take some time if running for first time)")
    total_count, new_count = populate(license_url, "licenses")
    print("Total Licenses Found: %d\nNew Licenses added to database: %d" % (total_count, new_count))

    print("Adding Exception names")
    total_count, new_count = populate(exception_url, "exceptions")
    print("Total Exceptions Found: %d\nNew Exceptions added to database: %d" % (total_count, new_count))
