import os
import django
import requests
import json

def populate(url, type):
    data = requests.get(url).text
    data = json.loads(data)
    total_count = 0
    new_count = 0
    for i in data[type]:
        total_count += 1
        response = LicenseNames.objects.get_or_create(name=i["name"])[1]
        if(response==True):
            new_count += 1
        if type=="licenses":
            LicenseNames.objects.get_or_create(name=i["licenseId"])
        else:
            LicenseNames.objects.get_or_create(name=i["licenseExceptionId"])
    return (total_count, new_count)

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
    django.setup()
    from app.models import LicenseNames
    license_url = "https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json"
    exception_url = "https://raw.githubusercontent.com/spdx/license-list-data/master/json/exceptions.json"
    
    print("Adding License names (this might take some time if running for first time)")
    total_count, new_count = populate(license_url, "licenses")
    print("Total Licenses Found: %d\nNew Licenses added to database: %d"%(total_count, new_count))
    
    print("Adding Exception names")
    total_count, new_count = populate(exception_url, "exceptions")
    print("Total Exceptions Found: %d\nNew Exceptions added to database: %d"%(total_count, new_count))
