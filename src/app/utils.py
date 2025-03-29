# SPDX-FileCopyrightText: 2018 Tushar Mittal
# SPDX-FileCopyrightText: 2025 SPDX Contributors
# SPDX-License-Identifier: Apache-2.0

import base64
import json
import logging
import re
import xml.etree.cElementTree as ET

import redis
import requests
from django.conf import settings
from spdx_license_matcher.build_licenses import build_spdx_licenses
from spdx_license_matcher.computation import (checkTextStandardLicense,
                                              get_close_matches,
                                              getListedLicense)

from app.models import User, UserID, LicenseRequest

from src.secret import getRedisHost

NORMAL = "normal"
TESTS = "tests"
PROD = "prod"

TYPE_TO_URL_LICENSE = {
NORMAL:  settings.REPO_URL,
PROD:  settings.PROD_REPO_URL,
TESTS: settings.DEV_REPO_URL,
}

TYPE_TO_URL_NAMESPACE = {
NORMAL:  settings.NAMESPACE_REPO_URL,
TESTS: settings.NAMESPACE_DEV_REPO_URL,
}

logging.basicConfig(filename="error.log", format="%(levelname)s : %(asctime)s : %(message)s")
logger = logging.getLogger()

# For license namespace utils
def licenseNamespaceUtils():
    return {
    "licenseListRepoUrl": "https://github.com/spdx/license-list-data",
    "internetConnectionUrl": "www.google.com",
    }
def checkPermission(user):
    """ Getting user info for submitting github issue """
    github_login = user.social_auth.get(provider='github')
    token = github_login.extra_data["access_token"]
    username = github_login.extra_data["login"]
    test = requests.get('https://api.github.com/repos/spdx/license-list-XML/collaborators/'+username , headers={'Authorization': 'token {}'.format(token) })
    if((test.status_code == 200) or (test.status_code == 204)):
        return True
    else:
        logger.error("Permission denied while accessing the github api.")
        return False
    
def utilForPullRequestFileCheckIfExists(file_url, headers, body, username, commit_url):
    """ Check if file already exists """
    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        """ Creating Commit by updating the file """
        data = json.loads(response.text)
        file_sha = data["sha"]
        body["sha"] = file_sha
    response = requests.put(commit_url, headers=headers, data=json.dumps(body))
    if not (response.status_code==201 or response.status_code==200):
        logger.error("[Pull Request] Error occured while making commit, for {0} user. {1}".format(username, response.text))
        return {
            "type":"error",
            "message":"Some error occured while making commit. Please try again later or contact the SPDX Team."
            }
    return response

def makePullRequest(username, token, branchName, updateUpstream, fileName, commitMessage, prTitle, prBody, xmlText, plainText, isException, is_ns):

    if not xmlText:
        logger.error("Error occurred while getting xml text. The xml text is empty")
        return {
            "type":"error",
            "message":"Some error occurred while getting the xml text."
        }
    url = "https://api.github.com/"
    headers = {
        "Accept":"application/vnd.github.machine-man-preview+json",
        "Authorization":"bearer "+token,
        "Content-Type":"application/json",
    }

    """ Making a fork """

    fork_url = "{0}/forks".format(TYPE_TO_URL_NAMESPACE[NORMAL] if is_ns else TYPE_TO_URL_LICENSE[NORMAL])
    response = requests.get(fork_url, headers=headers)
    data = json.loads(response.text)
    forks = [fork["owner"]["login"] for fork in data]
    if not username in forks:
        """ If user has not forked the repo """
        response = requests.post(fork_url, headers=headers)
        if response.status_code != 202:
            logger.error("[Pull Request] Error occured while creating fork, for {0} user. {1}".format(username, response.text))
            return {
                "type":"error",
                "message":"Error occured while creating a fork of the repo. Please try again later or contact the SPDX Team."
            }
    else:
        if(updateUpstream=="true"):
            """ If user wants to update the forked repo with upstream main """
            update_url = "{0}/git/refs/heads/main".format(TYPE_TO_URL_NAMESPACE[NORMAL] if is_ns else TYPE_TO_URL_LICENSE[NORMAL])
            response = requests.get(update_url, headers=headers)
            data = json.loads(response.text)
            sha = data["object"]["sha"]
            body = {
                "sha":sha,
                "force": True
            }
            update_url = "{0}repos/{1}/{2}/git/refs/heads/main".format(url, username, settings.NAMESPACE_REPO_NAME if is_ns else settings.LICENSE_REPO_NAME)
            response = requests.patch(update_url, headers=headers, data=json.dumps(body))
            if response.status_code!=200:
                logger.error("[Pull Request] Error occured while updating fork, for {0} user. {1}".format(username, response.text))
                return {
                    "type":"error",
                    "message":"Error occured while updating fork with the upstream main. Please try again later or contact the SPDX Team."
                }


    """ Getting ref of main branch """
    ref_url = "{0}repos/{1}/{2}/git/refs/heads/main".format(url, username, settings.NAMESPACE_REPO_NAME if is_ns else settings.LICENSE_REPO_NAME)
    response = requests.get(ref_url, headers=headers)
    if response.status_code != 200:
        logger.error("[Pull Request] Error occured while getting ref of main branch, for {0} user. {1}".format(username, response.text))
        return {
            "type":"error",
            "message":"Some error occured while getting the ref of main branch. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    sha = str(data["object"]["sha"])

    """ Getting names of all branches """
    branch_url = url + "repos/{0}/{1}/branches".format(username, settings.NAMESPACE_REPO_NAME if is_ns else settings.LICENSE_REPO_NAME)
    response = requests.get(branch_url, headers=headers)
    if response.status_code != 200:
        logger.error("[Pull Request] Error occured while getting branch names, for {0} user. {1}".format(username, response.text))
        return {
            "type":"error",
            "message":"Some error occured while getting branch names. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    branch_names = [i["name"] for i in data]

    """ Creating branch """
    if branchName in branch_names:
        count=1
        while True:
            if((branchName+str(count)) in branch_names):
                count+=1
            else:
                branchName = branchName+str(count)
                break
    create_branch_url = "{0}repos/{1}/{2}/git/refs".format(url, username, settings.NAMESPACE_REPO_NAME if is_ns else settings.LICENSE_REPO_NAME)
    body = {
        "ref":"refs/heads/{0}".format(branchName),
        "sha":sha,
    }
    response = requests.post(create_branch_url, headers=headers, data=json.dumps(body))
    if response.status_code != 201:
        logger.error("[Pull Request] Error occured while creating branch, for {0} user. {1}".format(username, response.text))
        return {
            "type":"error",
            "message":"Some error occured while creating the branch. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    branch_sha = data["object"]["sha"]

    """ Creating Commit """
    if fileName[-4:] == ".xml":
        fileName = fileName[:-4]
    if isException:
        textFileName = fileName + "-exception.txt"
        fileName += "-exception.xml"
    else:
        textFileName = fileName + ".txt"
        fileName += ".xml"
    if isException:
        commit_url = "{0}repos/{1}/{2}/contents/src/exceptions/{3}".format(url, username, settings.NAMESPACE_REPO_NAME if is_ns else settings.LICENSE_REPO_NAME, fileName)
    else:
        commit_url = "{0}repos/{1}/{2}/contents/src/{3}".format(url, username, settings.NAMESPACE_REPO_NAME if is_ns else settings.LICENSE_REPO_NAME, fileName)        
    text_commit_url = "{0}repos/{1}/{2}/contents/test/simpleTestForGenerator/{3}".format(url, username, settings.NAMESPACE_REPO_NAME if is_ns else settings.LICENSE_REPO_NAME, textFileName)
    xmlText = xmlText.encode('utf-8') if isinstance(xmlText, str) else xmlText
    fileContent = base64.b64encode(xmlText).decode()
    plainText = plainText.encode('utf-8') if isinstance(plainText, str) else plainText
    textFileContent = base64.b64encode(plainText).decode()
    body = {
        "path":"src/"+fileName,
        "message":commitMessage,
        "content":fileContent,
        "branch":branchName,
    }
    text_file_body = {
        "path":"src/"+ textFileName,
        "message":commitMessage,
        "content":textFileContent,
        "branch":branchName,
    }
    """ Check if file already exists """
    if isException:
        file_url = "{0}/contents/src/exceptions/{1}".format(TYPE_TO_URL_NAMESPACE[NORMAL] if is_ns else TYPE_TO_URL_LICENSE[NORMAL], fileName)
    else:
        file_url = "{0}/contents/src/{1}".format(TYPE_TO_URL_NAMESPACE[NORMAL] if is_ns else TYPE_TO_URL_LICENSE[NORMAL], fileName)      
    response = utilForPullRequestFileCheckIfExists(file_url, headers, body, username, commit_url)
    text_file_url = "{0}/contents/test/simpleTestForGenerator/{1}".format(TYPE_TO_URL_NAMESPACE[NORMAL] if is_ns else TYPE_TO_URL_LICENSE[NORMAL], textFileName)
    text_response = utilForPullRequestFileCheckIfExists(text_file_url, headers, text_file_body, username, text_commit_url)

    """ Making Pull Request """
    pr_url = "{0}/pulls".format(TYPE_TO_URL_NAMESPACE[NORMAL] if is_ns else TYPE_TO_URL_LICENSE[NORMAL])
    body = {
        "title": prTitle,
        "body": prBody,
        "head": "%s:%s"%(username, branchName),
        "base": "main",
    }
    response = requests.post(pr_url, headers=headers, data=json.dumps(body))
    if response.status_code != 201:
        logger.error("[Pull Request] Error occured while making pull request, for {0} user. {1}".format(username, response.text))
        return {
            "type":"error",
            "message":"Some error occured while making the pull request. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    return {
        "type":"success",
        "pr_url": data["html_url"],
}

def save_profile(backend, user, response, *args, **kwargs):
    """ Pipeline for saving user's info in UserID model when register using GitHub """
    if backend.name == 'github':
        try:
            profile = UserID()
            username = response.get('login')
            user = User.objects.filter(username=username)[0]
            profile.user_id=user.id
            profile.organisation='none'
            profile.save()
        except:
            pass

def check_license_name(name):
    """ Check if a license name exists """
    license_json = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"
    data = requests.get(license_json).text
    data = json.loads(data)
    url= "https://raw.githubusercontent.com/spdx/license-list-XML/main/src/"
    for license in data["licenses"]:
        if(license["licenseId"] == name):
            url+=name
            return [url, name]
        elif(license["name"] == name):
            url+=license["licenseId"]
            return [url, license["licenseId"]]

    """ Check if an exception name exists """
    exceptions_json = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/exceptions.json"
    data = requests.get(exceptions_json).text
    data = json.loads(data)
    url= "https://raw.githubusercontent.com/spdx/license-list-XML/main/src/exceptions/"
    for exception in data["exceptions"]:
        if(exception["licenseExceptionId"] == name):
            url += name
            return [url, name]
        elif(exception["name"] == name):
            url += exception["licenseExceptionId"]
            return [url, exception["licenseExceptionId"]]

    return [False]


def isConnected():
    import requests
    try:
        response = requests.get("http://www.google.com")
        return True
    except requests.ConnectionError:
        return False


def getLicenseList(token):
    url = "https://api.github.com/"
    headers = {
        "Accept":"application/vnd.github.v3.raw+json",
        "Authorization":"bearer "+token,
        "Content-Type":"application/json",
    }
    license_list_url = "{0}repos/spdx/license-list-data/contents/json/licenses.json".format(url)
    response = requests.get(license_list_url, headers=headers)
    data = json.loads(response.text)
    return data


def licenseInList(namespace, namespaceId, token):
    license_list = getLicenseList(token)
    return_dict = {
    "exists": False
    }
    for license in license_list["licenses"]:
        if namespaceId == license["licenseId"] or namespace == license["name"]:
            return_dict["licenseId"] = license["licenseId"]
            return_dict["name"] = license["name"]
            return_dict["referenceNumber"] = license["referenceNumber"]
            return_dict["isDeprecatedLicenseId"] = license["isDeprecatedLicenseId"]
            return_dict["exists"] = True
    return return_dict


def licenseExists(namespace, namespaceId, token):
    # Check if a license exists on the SPDX License List
    # check internet connection
    if isConnected():
        licenseInListDict = licenseInList(namespace, namespaceId, token)
        return licenseInListDict
    return {"exists": False}


def createLicenseNamespaceIssue(licenseNamespace, token, urlType):
    """ View for creating an GitbHub issue
    when submitting a new license namespace
    """
    body = "**1.** License namespace: {0}\n**2.** Short identifier: {1}\n **3.** License author or steward: {2}\n**4.** Description: {3}\n **5.** Submitter name: {4}\n **6.** SPDX doc URL:  {5}\n **7.** Submitter email: {6}\n **8.** License list URL: {7}\n **9.** GitHub repo URL: {8}".format(licenseNamespace.namespace, licenseNamespace.shortIdentifier, licenseNamespace.licenseAuthorName, licenseNamespace.description, licenseNamespace.fullname, licenseNamespace.url, licenseNamespace.userEmail, licenseNamespace.license_list_url, licenseNamespace.github_repo_url)
    title = "New license namespace request: {0} [SPDX-Online-Tools]".format(licenseNamespace.shortIdentifier)
    payload = {'title' : title, 'body': body, 'labels': ['new license namespace/exception request']}
    headers = {'Authorization': 'token ' + token}
    url = "{0}/issues".format(TYPE_TO_URL_NAMESPACE[urlType])
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    return r.status_code



def createIssue(licenseAuthorName, licenseName, licenseIdentifier, licenseComments, licenseSourceUrls, licenseHeader, licenseOsi, licenseExamples, licenseRequestUrl, token, urlType, matchId=None, diffUrl=None, msg=None):
    """ View for creating an GitHub issue
    when submitting a new license request
    """
    licenseUrls = ""
    if licenseSourceUrls != None and len(licenseSourceUrls) > 0:
        licenseUrls = licenseSourceUrls[0]
        for i in range(1, len(licenseSourceUrls)):
            licenseUrls += ', '
            licenseUrls += licenseSourceUrls[i]
            
    licenseExampleUrls = ""
    if licenseExamples != None and len(licenseExamples) > 0:
        licenseExampleUrls = licenseExamples[0]
        for i in range(1, len(licenseExamples)):
            licenseExampleUrls += ', '
            licenseExampleUrls += licenseExamples[i]
  
    body = "**1.** License name: {0}\n**2.** Short identifier: {1}\n**3.** License author or steward: {2}\n**4.** Comments: {3}\n**5.** License request Url: {4}\n**6.** URL(s): {5}\n**7.** OSI status: {6}\n**8.** Example projects: {7}".format(licenseName, licenseIdentifier, licenseAuthorName, licenseComments, licenseRequestUrl, licenseUrls, licenseOsi, licenseExampleUrls)
    if diffUrl:
        body = body + "\n**8.** License text diff: {0}".format(diffUrl)
    if matchId:
        body = body + "\n\n**Note:**\nThe license closely matched with the following license ID(s): " + matchId
    if msg:
        title = msg
    else:
        title = "New license request: {0} [SPDX-Online-Tools]".format(licenseIdentifier)
    payload = {'title' : title, 'body': body, 'labels': ['new license/exception request']}
    headers = {'Authorization': 'token ' + token}
    url = "{0}/issues".format(TYPE_TO_URL_LICENSE[urlType])
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    status_code = r.status_code
    response_json = {}
    issue_id = ""

    if status_code in [200, 201]:
        try:
            response_json = r.json()
        except ValueError:
            # Handle JSON parsing error
            return None, None
            

    if status_code in [200, 201] and "number" in response_json:
        issue_id = response_json["number"]
    else:
        issue_id = None

    return status_code, issue_id


def postToGithub(message, encodedContent, filename):
    """ Function to create a new file on with encodedContent
    """
    token = settings.DIFF_REPO_GIT_TOKEN
    repo = settings.DIFF_REPO_WITH_OWNER
    payload = {'message' : message, 'content': encodedContent}
    headers = {'Authorization': 'token ' + token}
    url = "https://api.github.com/repos/{0}/contents/{1}".format(repo, filename)
    r = requests.put(url, data=json.dumps(payload), headers=headers)
    return r.status_code, r.json()


def removeSpecialCharacters(filename):
    return re.sub(r'[#%&{}<>*?/$!\'":@+`|=]', "-", filename)

def parseXmlString(xmlString):
    """ View for generating a spdx license xml
    returns a dictionary with the xmlString license fields values
    """
    data = {}
    tree = ET.ElementTree(ET.fromstring(xmlString))
    try:
        root = tree.getroot()
    except Exception as e:
        return
    try:
        if(len(root) > 0 and 'isOsiApproved' in root[0].attrib):
            data['osiApproved'] = root[0].attrib['isOsiApproved']
        else:
            data['osiApproved'] = '-'
    except Exception as e:
        data['osiApproved'] = '-'
    data['crossRefs'] = []
    try:
        if(len(tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}crossRefs')) > 0):
            crossRefs = tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}crossRefs')[0]
            for crossRef in crossRefs:
                data['crossRefs'].append(crossRef.text)
    except Exception as e:
        data['crossRefs'] = []
    try:
        if(len(tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}notes')) > 0):
            data['notes'] = tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}notes')[0].text
        else:
            data['notes'] = ''
    except Exception as e:
        data['notes'] = ''
    try:
        if(len(tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}standardLicenseHeader')) > 0):
            data['standardLicenseHeader'] = tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}standardLicenseHeader')[0].text
        else:
            data['standardLicenseHeader'] = ''
    except Exception as e:
        data['standardLicenseHeader'] = ''
    try:
        if(len(tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}text')) > 0):
            textElem = tree.findall('{http://www.spdx.org/license}license/{http://www.spdx.org/license}text')[0]
            ET.register_namespace('', "http://www.spdx.org/license")
            textStr = ET.tostring(textElem, encoding='unicode').strip()
            if(len(textStr) >= 49 and textStr[:42] == '<text xmlns="http://www.spdx.org/license">' and textStr[-7:] == '</text>'):
                textStr = textStr[42:]
                textStr = textStr[:-7].strip().replace('&lt;', '<').replace('&gt;', '>').strip()
            data['text'] = textStr.strip()
        else:
            data['text'] = ''
    except Exception as e:
        data['text'] = ''
    return data


def clean(text):
    """ Clean the XML tags from license text after parsing the XML string.
    """
    tags = re.compile('<.*?>')
    cleanedText = re.sub(tags, '', text)
    return cleanedText


def get_rejected_licenses_issues(urlType):
    """ Get all the issues that are already rejected by the legal team.
    """
    payload = {'state': 'closed', 'labels': 'new license/exception: Not Accepted'}
    url = TYPE_TO_URL_LICENSE[urlType] + '/issues'
    res = requests.get(url, params=payload)
    issues = res.json()
    return issues


def get_yet_not_approved_licenses_issues(urlType):
    """ Get all the issues that are yet to be approved by the legal team by sorting them with labels.
    """
    payload = {'state': 'open', 'labels': 'new license/exception request'}
    url = TYPE_TO_URL_LICENSE[urlType] + '/issues'
    response = requests.get(url, params=payload)
    issues = response.json()
    newRequestIssues = []
    # Remove issues with Accepted labels
    for issue in issues:
        for label in issue.get('labels'):
            if "new license/exception: Accepted" in label.get('name'):
                break
        else:
            newRequestIssues.append(issue)
    return newRequestIssues


def get_license_data(issues):
    """ Get license data returns a dictionary with key as license IDs and value as the
    corresponding license text of these IDs.
    """
    licenseIds = []
    licenseTexts = []
    for issue in issues:
        if not issue.get('pull_request'):
            licenseInfo = issue.get('body')
            if '[SPDX-Online-Tools]' in issue.get('title'):
                try:
                    licenseIdentifier = re.search(r'(?im)short identifier:\s([a-zA-Z0-9|.|-]+)', licenseInfo).group(1)
                    dbId = re.search(r'License Request Url:.+/app/license_requests/([0-9]+)', licenseInfo).group(1)
                    licenseXml = LicenseRequest.objects.get(id=dbId, shortIdentifier=licenseIdentifier).xml
                    licenseXml = licenseXml.decode('utf-8') if not isinstance(licenseXml, str) else licenseXml
                    licenseText = parseXmlString(licenseXml)['text']
                    licenseTexts.append(clean(licenseText))
                    licenseIds.append(licenseIdentifier)
                except LicenseRequest.DoesNotExist:
                    pass
                except AttributeError:
                    pass
    licenseData = dict(list(zip(licenseIds, licenseTexts)))
    return licenseData


def get_issue_url_by_id(licenseId, issues):
    """ Get the github issue url of the license by license ID and the issues instance.
    Returns None if no matching issue is found.
    """
    matching_urls = [issue.get('html_url') for issue in issues if issue.get('pull_request') is None if licenseId in issue.get('title', '')]
    if matching_urls:
        return matching_urls[0]
    else:
        return None


def check_new_licenses_and_rejected_licenses(inputLicenseText, urlType):
    """ Check  if the license text matches with that of a license that is either
    a not yet approved license or a rejected license.
    returns the close matches of license text along with the license issue URL.
    """
    issues = get_rejected_licenses_issues(urlType)
    issues.extend(get_yet_not_approved_licenses_issues(urlType))
    licenseData = get_license_data(issues)
    matches = get_close_matches(inputLicenseText, licenseData)
    matches = list(matches.keys())
    if not matches:
        return matches, ''
    issueUrl = get_issue_url_by_id(matches[0], issues)
    return matches, issueUrl


def check_spdx_license(licenseText):
    """Check the license text against the SPDX License List.
    """
    r = redis.StrictRedis(host=getRedisHost(), port=6379, db=0)
    
    # if redis is empty build the SPDX License List in the redis database
    if r.keys('*') == []:
        build_spdx_licenses()
    spdxLicenseIds = list(r.keys())
    spdxLicenseTexts = r.mget(spdxLicenseIds)
    licenseData = dict(list(zip(spdxLicenseIds, spdxLicenseTexts)))
    matches = get_close_matches(licenseText, licenseData)
    if not matches:
        matchedLicenseIds = None
        matchType = 'No match'
    else:
        matchedLicenseIds = max(matches, key=matches.get)
        if matches[matchedLicenseIds] == 1.0:
            matchType = 'Perfect match'
        else:
            matchType = 'Close match'
            for licenseID in matches:
                listedLicense = getListedLicense(licenseID)
                isTextDifferent = checkTextStandardLicense(listedLicense, licenseText)
                if not isTextDifferent:
                    matchedLicenseIds = licenseID
                    matchType = 'Standard License match'
    return matchedLicenseIds, matchType, matches


def getFileFormat(to_format):
    if (to_format=="TAG"):
        return ".spdx"
    elif (to_format=="RDFXML"):
        return ".rdf.xml"
    elif (to_format=="XLS"):
        return ".xls"
    elif (to_format=="XLSX"):
        return ".xlsx"
    elif (to_format=="JSON"):
        return ".json"
    elif (to_format=="YAML"):
        return ".yaml"
    elif (to_format=="XML"):
        return ".xml"
    else :
        return ".invalid"


def formatToContentType(to_format):
    if (to_format=="TAG"):
        return "text/tag-value"
    elif (to_format=="RDFXML"):
        return "application/rdf+xml"
    elif (to_format=="XLS"):
        return "application/vnd.ms-excel"
    elif (to_format=="XLSX"):
        return "application/vnd.ms-excel"
    elif (to_format=="JSON" or to_format=="JSONLD"):
        return "application/json"
    elif (to_format=="YAML"):
        return "text/yaml"
    elif (to_format=="XML"):
        return "application/xml"
    else :
        return ".invalid"

def is_ajax(request):
    """Determine if the request is an AJAX request."""
    try:
        xrw = request.headers.get("x-requested-with", "")
    except AttributeError:
        # Some Django versions / WSGI servers may not populate request.headers
        xrw = request.META.get("HTTP_X_REQUESTED_WITH", "")
    accept = (
        request.headers.get("accept", "")
        if hasattr(request, "headers")
        else request.META.get("HTTP_ACCEPT", "")
    )
    return (str(xrw).lower() == "xmlhttprequest") or ("application/json" in str(accept))
