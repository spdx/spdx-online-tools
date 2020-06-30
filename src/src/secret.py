from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

def getGithubKey():
    return os.environ.get(key="ONLINE_TOOL_GITHUB_KEY")

def getGithubSecret():
    return os.environ.get(key="ONLINE_TOOL_GITHUB_SECRET")

def getSecretKey():
    return os.environ.get(key="DJANGO_SECRET_KEY")

# The methods: getAccessToken, getGithubUserId and getGithubUserName
# are important for license submit tests, given that github authentication
# is necessary for such tests to be executed normally.
def getAccessToken():
    return os.environ.get(key="ACCESS_TOKEN")

def getGithubUserId():
    return os.environ.get(key="TEST_GITHUB_USER_ID")

def getGithubUserName():
    return os.environ.get(key="TEST_GITHUB_USER_NAME")

def getOauthToolKitAppID():
    return os.environ.get(key="OAUTH_APP_ID")

def getOauthToolKitAppSecret():
    return os.environ.get(key="OAUTH_APP_SECRET")

# The method: getAuthCode is important for the license submit tests, given
# that this authentication code is necessary to generate a github access token.
# Authentication code generated by client from http://github.com/login/oauth/authorize/
def getAuthCode():
    return os.environ.get(key="AUTH_CODE")
