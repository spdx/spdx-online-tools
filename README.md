[![GSoC Logo](./docs/spdx-online-tool.jpg)](https://summerofcode.withgoogle.com/projects/#5747767629578240)

# SPDX Online Tools

Source for the web server providing online access to various SPDX tools.

The server provides an easy all-in-one website to upload and parse
SPDX documents for validation, conformance check, comparison, conversion
and SPDX License List search.

*The server provides access via both web UI and REST API.*

You can find more about the working of the SPDX Online Tools
in the [wiki][gsoc2017].

[gsoc2017]: https://github.com/spdx/spdx-online-tools/wiki/Online-SPDX-Tool,-Google-Summer-of-Code-2017

## Features

* Upload and parse SPDX documents
* Validate SPDX documents
* Compare multiple SPDX RDF files
* Convert one SPDX format to another
* Compare license text to the SPDX listed Licenses
* Edit License XML
* Check for minimum elements conformance (NTIA and others)
* Edit SPDX 3 visually

## Requirements

* Python 3.12+
* Java 17+

## Installation

1. Clone or download the repository.
2. Create a new virtual environment for the project.

    ```bash
    python3 -m venv ./venv
    source venv/bin/activate
    ```

    On Windows:

    ```shell
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

5. (Optional) If you want use license-xml-editor with licenses/exceptions from [SPDX License List](https://github.com/spdx/license-list-data/), download the license name database.

    ```bash
    python src/populate.py
    ```

6. (Optional) If you want to use the license submittal feature or check license feature, follow the below step(s):
    * Install Valkey server on your local machine.

        **For Linux users**

        * Use the command `sudo apt-get install valkey-server` to install the Valkey server.

        **For Mac users**

        * Install Valkey by running the command

            ```bash
            brew install valkey
            ```

        * If you want to run Valkey whenever your computer starts, run

            ```bash
            brew services start valkey
            ```

        * To test if Valkey is working, run

            ```bash
            valkey-cli ping
            ```

            If it returns `PONG` then you are good to go.

        * To stop the Valkey server, run

            ```bash
            brew services stop valkey
            ```

        **For Windows users**

        * Valkey is not officially supported natively on Windows, but can be run using [Windows Subsystem for Linux (WSL)](https://valkey.io/topics/installation/#windows):
            * Install WSL2 (e.g., `wsl --install`) with a Linux distribution such as Ubuntu.
            * In the WSL terminal, install Valkey using the package manager (e.g., `sudo apt-get install valkey-server`) or from source following the [Valkey installation guide](https://valkey.io/topics/installation/#windows).
            * Start the Valkey service in WSL and test with `valkey-cli ping`.

    * Make sure Valkey server is running and keep it running until you are done using the license submittal or check license feature.

        *Valkey is used to store the license text of licenses present on the SPDX License List. For the very first time it may take a while to build the license on the Valkey server.*

        *SPDX License Matcher matches the license text input by the user (via license submittal form) against the data present in Valkey to check for duplicate and near matches.*

7. Start the application.

    ```bash
    python src/manage.py runserver
    ```

8. Open `localhost:8000/` in the browser.

9. Register and login to use the tools.

## How to Run Tests

Tests live under `src/tests/`, split into an `api` package and an `app`
package (mirrored by CI as two workflows, `test-api.yml` and `test-app.yml`).

Run everything:

```bash
python src/manage.py test tests
```

Run only the API or only the app tests (as CI does):

```bash
python src/manage.py test tests.api
python src/manage.py test tests.app
```

Some tests are gated and skip automatically when their dependency isn't
available: Valkey-backed API tests need a local Valkey server (see step 6
above), and `@tag("selenium")` app tests need a Firefox or Chrome browser
on `PATH`.

## Running with Docker

You need to have [Docker Desktop](https://docs.docker.com/desktop/) installed
on your machine for the container environment.

Prior to starting the Docker image, you will need to create a file to set the
environment variables described below.

Create a file `.env` with the following content:

```bash
DIFF_REPO_GIT_TOKEN=XXXX
DIFF_REPO_WITH_OWNER=XXXX
ONLINE_TOOL_GITHUB_KEY=XXXX
ONLINE_TOOL_GITHUB_SECRET=XXXX
```

You can bring up the Docker image with the following docker-compose command:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

For the production environment,
see the [README-PRODUCTION.md](README-PRODUCTION.md) file.

## GitHub Developer Sensitive Data

The `src/config/settings.py` file uses sensitive data to work with the GitHub API. For that reason, sensitive data is maintained as environment variables. Due to that lack of data, some features of SPDX Online Tools and its API won't be able to run as they require the user credentials in order to access the GitHub API. So, the user is supposed to either maintain a `.env` file in the `src/config/` folder or create environment variables in their OSes with their credentials in order to ensure proper functioning of the tool.

The `src/config/secret.py` file contains the following lines along with some methods required to run the tests properly. These include:

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
# The DIFF_REPO_GIT_TOKEN is a personal access token created in GitHub with access to the repo DIFF_REPO_WITH_OWNER
    
def getDiffRepoGitToken():
    return os.environ.get(key="DIFF_REPO_GIT_TOKEN")
    
def getDiffRepoWithOwner():
    return os.environ.get(key="DIFF_REPO_WITH_OWNER", default="spdx/licenseRequestImages")
```

where:

* ONLINE_TOOL_GITHUB_KEY is the Client ID for the GitHub OAuth Apps (To create your OAuth application see [this](https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app))
* ONLINE_TOOL_GITHUB_SECRET is the Client secret for the GitHub OAuth Apps
* DJANGO_SECRET_KEY is the Django secret
* OAUTH_APP_ID is the client ID of the Django OAuth Toolkit app (To create a Django OAuth Toolkit app see instructions below)
* OAUTH_APP_SECRET is the client secret of the Django OAuth Toolkit app
* DIFF_REPO_GIT_TOKEN is the GitHub user's Personal Access Token which has write access to DIFF_REPO_WITH_OWNER (Follow [this](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token) to create your GitHub Personal access token with full repo and user scope access)
* DIFF_REPO_WITH_OWNER is the repo where images related to license submittable process are uploaded

**Note:** While setting up the GitHub OAuth App, set the `Homepage URL` to `http://localhost:8000/` and the `Authorization callback URL` to `http://localhost:8000/oauth/complete/github/` (ensure the trailing slash is included).

## How to Use API

The exhaustive list of request and response fields of different API tools
can be found in the [wiki][rest-api].

[rest-api]: https://github.com/spdx/spdx-online-tools/wiki/REST-API-Fields-Request-and-Response

1. Start the server.

    ```bash
    python src/manage.py runserver
    ```

2. Send the request to the URL with the form input values accordingly. Curl examples are given below.

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

7. For the license submittal API, first create a Django OAuth Toolkit application and follow the steps given below:

    **Django OAuth Toolkit App**

    * Go to admin page and login(if you don't have an admin account then create one using `python src/manage.py createsuperuser`).
    * Create a new application by going to the `Applications` section.
    * Copy the client ID and client secret of the app and paste it in `src/config/secret.py` file under getOauthToolKitAppID and secret and fill the other details of the app as follows:
        * `User`: `<admin you created>`
        * `client type`: `confidential`
        * `authorization grant type`: `resource owner password based`

        and SAVE the app.

   **Authorize OAuth app with GitHub to get code and send a request to the license submittal API**

    * Visit `http://github.com/login/oauth/authorize/?client_id=<github-client-id>` it will then redirect you to a URL, copy the `code` query string present in the URL and send it via curl command if you want to use the API. If you want to run tests and test the API then paste the `code` in the `src/config/secret.py` file in the `getAuthCode` method.

        **Note** You can only use your code once. If you want to use the license submittal API again, you can generate a new code by following the above point. The code is valid for 10 minutes only.

    * Send the request to `/api/submit_license/`.

        ```bash
        curl -X POST http://localhost:8000/api/submit_license/ -F 'fullname=<your-fullname>' -F 'shortIdentifier=<your-identifier>' -F 'licenseAuthorName=<license-author>' -F 'userEmail=<your-email>' -F 'text=<text>' -F 'osiApproved=<osi>' -F 'sourceUrl=<url>' -F 'code=<your-code-here>'
        ```

## Developer notes

### Redis serialization protocol version

All `valkey.StrictRedis(...)` connections in this codebase explicitly
pass `protocol=2` (RESP2) instead of relying on the client's default.
RESP2 is chosen for backward compatibility.
The serialization protocol version ensures consistent behavior across servers,
as mismatches can fail silently with features like "check license" returning
"no license found," with no error or warning in the logs.

See [issue #712](https://github.com/spdx/spdx-online-tools/issues/712)
and the fixes in
[PR #713](https://github.com/spdx/spdx-online-tools/pull/713) and
[PR #716](https://github.com/spdx/spdx-online-tools/pull/716).

When adding any new `valkey.StrictRedis(...)` call, always include
`protocol=2` to avoid reintroducing this issue.

More details at [serialization protocol specification][RESP].

[RESP]: https://valkey.io/topics/protocol/

## Dependencies

* [SPDX Java Tools](https://github.com/spdx/tools-java)
  for validation, comparison, and conversion functions
* [SPDX License Matcher](https://github.com/spdx/spdx-license-matcher)
  for license match function
* [NTIA Conformance Checker](https://github.com/spdx/ntia-conformance-checker)
  for conformance check function
