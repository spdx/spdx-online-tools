[![GSoC Logo](https://developers.google.com/open-source/gsoc/resources/downloads/GSoC-logo-horizontal.svg)](https://summerofcode.withgoogle.com/projects/#5747767629578240)
# spdx-online-tools
Source for the website providing online SPDX tools.
The tool provides an easy all-in-one website to upload and parse SPDX documents for validation, comparison and conversion and search SPDX license list.
[Here](https://github.com/spdx/spdx-online-tools/wiki/Online-SPDX-Tool,-Google-Summer-of-Code-2017) you can find more about the working of the tool.

## Features
* Upload and parse SPDX Documents
* Validate SPDX Documents
* Compare Multiple SPDX Rdf Files
* Convert one SPDX format to another
* Compare License text to the SPDX listed Licenses

## Requirements (Linux/Debian/Ubuntu)  

Either the Sun/Oracle JDK/JRE Variant or OpenJDK. Python 2.6+. 

Debian/Ubuntu users will have to install g++ and python-dev first:  
```
sudo apt-get install g++ python-dev
```

## Requirements (Windows)  

Windows users need a Python installation and C++ compiler:

* Install some version of Python (2.7 or higher), e.g., [Anaconda](https://www.continuum.io/downloads) is a good choice for users not yet familiar with the language
* Install a [Windows C++ Compiler](http://landinghub.visualstudio.com/visual-cpp-build-tools)


## Installation
1. Clone or download the repository. 
2. Create a new virtual environment for the project. To download virtual environment run ```pip install virtualenv```
    ```bash
    virtualenv venv
    source venv/bin/activate
    ```
3. Install the required python libraries given in the requirements.txt file.
    ```bash
    cd spdx-online-tools
    pip install -r requirements.txt

4. Create Github API configuration according to [GitHub Developer Sensitive Data](#github-developer-sensitive-data).

5. Run Django migrate.
    
    ```bash
    cd src
    python manage.py migrate
    ```
6. (Optional) If you want use xml-editor with licenses/exceptions from [spdx license list](https://github.com/spdx/license-list-data/), download the license name database.
    ```bash
    python src/populate.py
    ```
7. Start the application.
    ```bash
    python manage.py runserver
    ```
8. Open `localhost:8000/` in the browser.

9. Register and login to use the tools.
    
## How to Run Tests
    
```
python manage.py test
```

## GitHub Developer Sensitive Data
The `views.py` file uses sensitive data to work with the GitHub API. For that reason, sensitive data is not checked into source. Due to that lack of data, the following error could rise when running the app:

> from app.github_utils import getGithubToken
> ImportError: No module named github_utils

To avoid this error and allow the tool to use the GitHub API, the file `src/app/github_utils.py` should be included into the source. The file should contain the following lines:

```
def getGithubToken():	
    return 'XXXX'
```

where, **XXXX** is a GitHub Developer token.


## How to Use API

**[Here](https://github.com/spdx/spdx-online-tools/wiki/REST-API-Fields-Request-and-Response) is the exhaustive list of request and response fields of different api tools.**

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
6. For license check tool, send the request to `/api/check_license/`.
    ```bash
    curl -X POST -u <admin>:<password> -F "file=@<fileInput>" -H "Accept: application/json" http://localhost:8000/api/check_license/ | json_pp
    ```    

## Dependencies
The project uses [spdx java tools](https://github.com/spdx/tools/) for various tools of the website.
