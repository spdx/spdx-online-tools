[![GSoC Logo](./title_img/spdx-online-tool.jpg)](https://summerofcode.withgoogle.com/projects/#5747767629578240)

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

Either the Sun/Oracle JDK/JRE Variant or OpenJDK. Python 3.7+.

Debian/Ubuntu users will have to install g++ and python-dev first:  

```bash
sudo apt-get install g++ python-dev
```

## Requirements (Windows)  

Windows users need a Python installation and C++ compiler:

* Install Python 3.7 version, e.g., [Anaconda](https://www.anaconda.com/distribution/) is a good choice for users not yet familiar with the language
* Install a [Windows C++ Compiler](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

## Installation

1. Clone or download the repository.
2. Create a new virtual environment for the project.
    ```bash
    python3 -m venv ./venv
    source venv/bin/activate
    ```
	
	On Windows:
	```
	py -m venv venv
	venv\Scripts\activate
	```
3. Install the required python libraries given in the requirements.txt file.
    ```bash
    cd spdx-online-tools
    pip install -r requirements.txt
    ```
4. Run Django migrate.

    ```bash
    python src/manage.py migrate
    ```
5. (Optional) If you want use license-xml-editor with licenses/exceptions from [spdx license list](https://github.com/spdx/license-list-data/), download the license name database.
    ```bash
    python src/populate.py
    ```
6. (Optional) If you want to use the license submittal feature or check license feature, follow the below step(s):
    * Install redis server on your local machine.

        **For linux users**
        
        * Use the command `sudo apt-get install redis-server` to install the redis server.

        **For Mac users**

        * Install the redis by running the command

            `brew install redis`.
        * If you want to run redis whenever your computer starts then run

            `ln -sfv /usr/local/opt/redis/*.plist ~/Library/LaunchAgents`.

        * To run the redis server use

            `launchctl load ~/Library/LaunchAgents/homebrew.mxcl.redis.plist`.
        * To test if the redis is working run the command `redis-cli ping`. If it returns `Pong` then you are good to go.

        **For Windows users**

        * Download the redis server from [here](https://github.com/microsoftarchive/redis/releases) and install it.
    * Make sure redis server is running and keep it running until you are done using the license submittal or check license feature.

        *The redis is used to store the license text of license present on the SPDX license list. For the very first time it may take a while to build the license on the redis server.*

        *SPDX License Matcher matches the license text input by the user(via license submittal form) against the data present on the redis to find for duplicate and near matches.*

7. Start the application.
    ```bash
    python src/manage.py runserver
    ```
8. Open `localhost:8000/` in the browser.

9. Register and login to use the tools.

## How to Run Tests

```bash
python src/manage.py test
```

## Running with Docker

You need to have [docker desktop](https://docs.docker.com/desktop/) installed on your machine for the container environment. 

Prior to starting the docker image, you will need to create a file to set the environment variables described below.

Create a file ".env" with the following content:

```
DIFF_REPO_GIT_TOKEN=XXXX
DIFF_REPO_WITH_OWNER=XXXX
ONLINE_TOOL_GITHUB_KEY=XXXX
ONLINE_TOOL_GITHUB_SECRET=XXXX
```

You can bring up the Docker image with the following docker-compose command:

```
docker-compose -f docker-compose.dev.yml up --build
```

For the production environment, see the [README-PRODUCTION.md](README-PRODUCTION.md) file.

## GitHub Developer Sensitive Data

The `src/src/settings.py` file uses sensitive data to work with the GitHub API. For that reason, sensitive data is maintained as environment variables. Due to that lack of data, some features of SPDX Online Tools and its API won't be able to run as they require the user credentials in order to access the GitHub API. So, the user is supposed to either maintain a `.env` file in the `src/src/` folder or create environment variables in their os with their credentials in order to ensure proper functioning of the tool.

The `src/src/secret.py` file contains the following lines along with some methods required to run the tests properly. These include:

```python
def getGithubKey():
    return os.environ.get(key="ONLINE_TOOL_GITHUB_KEY")

def getGithubSecret():
    return os.environ.get(key="ONLINE_TOOL_GITHUB_SECRET")

def getSecretKey():
    return os.environ.get(key="DJANGO_SECRET_KEY")

def getOauthToolKitAppID():
    return os.environ.get(key="OAUTH_APP_ID")

def getOauthToolKitAppSecret():
    return os.environ.get(key="OAUTH_APP_SECRET")
	
# The methods getDiffRepoGitToken and getDiffRepoWithOwner are used to configure the repository used for storing license diffs created during the license submittal process
# The DIFF_REPO_GIT_TOKEN is a personal access token created in Github with access to the repo DIFF_REPO_WITH_OWNER
    
def getDiffRepoGitToken():
    return os.environ.get(key="DIFF_REPO_GIT_TOKEN")
    
def getDiffRepoWithOwner():
    return os.environ.get(key="DIFF_REPO_WITH_OWNER", default="spdx/licenseRequestImages")
```

where:

* ONLINE_TOOL_GITHUB_KEY is the Client ID for the Github Oauth Apps (To create your Oauth application see [this](https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app))
* ONLINE_TOOL_GITHUB_SECRET is the Client secret for the Github Oauth Apps
* DJANGO_SECRET_KEY is the Django secret
* OAUTH_APP_ID is the client ID of the django oauth toolkit app (To create your application see [this](#django-oauth-toolkit-app))
* OAUTH_APP_SECRET is the client secret of the django oauth toolkit app (To create your application see [this](#django-oauth-toolkit-app))
* DIFF_REPO_GIT_TOKEN is the Github user's Personal Access Token which has write access to DIFF_REPO_WITH_OWNER (Follow [this](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token) to create your Github Personal access token with full repo and user scope access)
* DIFF_REPO_WITH_OWNER is the repo where images related to license submittable process are uploaded

**Note:** While setting up the GitHub OAuth App, set the `Homepage URL` to `http://localhost:8000/` and the `Authorization callback URL` to `http://localhost:8000/oauth/complete/github`

## How to Use API

**[Here](https://github.com/spdx/spdx-online-tools/wiki/REST-API-Fields-Request-and-Response) is the exhaustive list of request and response fields of different api tools.**

1. Start the server.
    ```bash
    python src/manage.py runserver
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
7. For the license submittal API, first create a a django oauth toolkit application and follow the steps given below:
    #### Django Oauth Toolkit App
    * Go to admin page and login(if you don't have an admin account then create one using `python src/manage.py createsuperuser`).
    * Create a new application by going to the `Applications` section.
    * Copy the client id and client secret of the app and paste it in `src/src/secret.py` file under   getOauthToolKitAppID and secret and fill the other details of the app as follows:
        * `User`: `<admin you created>`
        * `client type`: `confidential`
        * `authorization grant type`: `resource owner password based`
    
        and SAVE the app.
    #### Authorize oauth app with github to get code and send a request to the license submittal API
    * Visit `http://github.com/login/oauth/authorize/?client_id=<github-client-id>` it will then redirect you to a url, copy the `code` query string present in the url and send it via curl command if you want to use the API. if you want to run tests and test the API then paste the `code` in the `src/src/secret.py` file in the `getAuthCode` method.

        **Note** You can only use your code once. If you want to use the license submittal API again, you can generate a new code by following the above point. The code is valid for 10 minutes only.

    * Send the request to `/api/submit-license/`.
        ```bash
        curl -X POST http://localhost:8000/api/ submit_license/ -F 'fullname=<your-fullname>' -F 'shortIdentifier=<your-identifier>' -F 'licenseAuthorName=<license-author>' -F 'userEmail=<your-email>' -F 'text=<text>' -F 'osiApproved=<osi>' -F 'sourceUrl=<url>' -F 'code=<your-code-here>'
        ```

## Dependencies

The project uses [spdx java tools](https://github.com/spdx/tools/) for various tools of the website.
