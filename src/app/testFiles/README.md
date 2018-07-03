# Test Files

This folder contains files used for general testing purposes.

## License Requests

The file [licenseRequests.json](licenseRequests.json) contains LicenseRequest model records. This file is used to load data and test functionalities that use license requests data that have been already submitted to the tool.

### Loading data

To load the LicenseRequest records you can run: 

```
python manage.py loaddata ./app/testFiles/licenseRequests.json
```
