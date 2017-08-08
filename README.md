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
    
## How to Run Tests
python manage.py test
## Dependencies
The project uses [spdx java tools](https://github.com/spdx/tools/) for various tools of the website.
