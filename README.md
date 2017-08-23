![GSoC Logo](https://developers.google.com/open-source/gsoc/resources/downloads/GSoC-logo-horizontal.svg)](https://summerofcode.withgoogle.com/projects/#5747767629578240)

# spdx-online-tools
Source for the website providing online SPDX tools.
The tool would provide an an easy all-in-one website to upload, parse, validate, compare, convert and search SPDX license list and documents.

## Features
* Upload and parse SPDX Documents
* Validate SPDX Documents
* Compare Multiple SPDX Rdf Files
* Convert one SPDX format to another
* Compare License text to the SPDX listed Licenses

## Installation
1. Clone or download the repository. 
2. Create a new virtual environment for the project.
    ```bash
    virtualenv venv
    source venv/bin/activate
    ```
3. Install the required python libraries given in the requirements.txt file.
    ```bash
    pip install -r requirements.txt
    ```
4. Run Django migrate.
    
    ```bash
    python manage.py migrate
    ```
5. Start the application.
    ```bash
    python manage.py runserver
    ```
6. Open `localhost:8000/` in the browser.

7. Register and login to use the tools.
    
## How to Run Tests
    
    ```bash
    python manage.py test
    ```

## How to Use API
1. Start the server.
    ```bash
    python manage.py runserver
    ```
2. Send the request to the url with the form input values accordingly. Curl examples are given below.

3. For validation tool, send the request to `/api/validate/`.
    ```bash
    curl -X POST -u <admin>:<password> -F "file=@<fileInput>" -H "Accept: application/json" http://localhost:8000/api/validate/ | json_pp
    ```
4. For compare tool, send the request to `/api/compare/`.
    ```bash
    curl -X POST -u <admin>:<password> -F "file1=@<fileInput1>" -F "file2=<fileInput2>" -F "rfilename=<resultFileName>" -H "Accept: application/json" http://localhost:8000/api/compare/ | json_pp
    ```
5. For convert tool, send the request to `/api/convert/`.
    ```bash
    curl -X POST -u <admin>:<password> -F "file=@<fileInput>" -F "cfilename=<resultFileNameWithExtension>" -F "from_format=<convertFrom>" -F "to_format=<convertTo>" -H "Accept: application/json" http://localhost:8000/api/convert/ | json_pp
    ```

## Dependencies
The project uses [spdx java tools](https://github.com/spdx/tools/) for various tools of the website.
