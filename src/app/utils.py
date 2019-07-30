# coding=utf-8

# Copyright (c) 2018 Tushar Mittal
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import json
import logging
import re
import socket
import xml.etree.cElementTree as ET

import requests
from django.conf import settings
from spdx_license_matcher.computation import get_close_matches

from app.models import User, UserID

from .models import LicenseRequest

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

# For license namespace utils
def licenseNamespaceUtils():
    return {
    "licenseListRepoUrl": "https://github.com/spdx/license-list-data",
    "internetConnectionUrl": "www.google.com",
    }


def makePullRequest(username, token, branchName, updateUpstream, fileName, commitMessage, prTitle, prBody, xmlText):
    logging.basicConfig(filename="error.log", format="%(levelname)s : %(asctime)s : %(message)s")
    logger = logging.getLogger()

    url = "https://api.github.com/"
    headers = {
        "Accept":"application/vnd.github.machine-man-preview+json",
        "Authorization":"bearer "+token,
        "Content-Type":"application/json",
    }

    """ Making a fork """
    fork_url = "{0}/forks".format(TYPE_TO_URL_LICENSE[PROD])
    response = requests.get(fork_url, headers=headers)
    data = json.loads(response.text)
    forks = [fork["owner"]["login"] for fork in data]
    if not username in forks:
        """ If user has not forked the repo """
        response = requests.post(fork_url, headers=headers)
        if response.status_code != 202:
            logger.error("[Pull Request] Error occured while creating fork, for %s user. "%(username)+response.text)
            return {
                "type":"error",
                "message":"Error occured while creating a fork of the repo. Please try again later or contact the SPDX Team."
            }
    else:
        if(updateUpstream=="true"):
            """ If user wants to update the forked repo with upstream master """
            update_url = "{0}/git/refs/heads/master".format(TYPE_TO_URL_LICENSE[PROD])
            response = requests.get(update_url, headers=headers)
            data = json.loads(response.text)
            sha = data["object"]["sha"]
            body = {
                "sha":sha,
                "force": True
            }
            update_url = url+"repos/%s/"+settings.LICENSE_REPO_NAME+"/git/refs/heads/master"%(username)
            response = requests.patch(update_url, headers=headers, data=json.dumps(body))
            if response.status_code!=200:
                logger.error("[Pull Request] Error occured while updating fork, for %s user. "%(username)+response.text)
                return {
                    "type":"error",
                    "message":"Error occured while updating fork with the upstream master. Please try again later or contact the SPDX Team."
                }


    """ Getting ref of master branch """
    ref_url = url + "repos/%s/"+settings.LICENSE_REPO_NAME+"/git/refs/heads/master"%(username)
    response = requests.get(ref_url, headers=headers)
    if response.status_code != 200:
        logger.error("[Pull Request] Error occured while getting ref of master branch, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while getting the ref of master branch. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    sha = str(data["object"]["sha"])

    """ Getting names of all branches """
    branch_url = url + "repos/%s/"+settings.LICENSE_REPO_NAME+"/branches"%(username)
    response = requests.get(branch_url, headers=headers)
    if response.status_code != 200:
        logger.error("[Pull Request] Error occured while getting branch names, for %s user. "%(username)+response.text)
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
    create_branch_url = url + "repos/%s/"+settings.LICENSE_REPO_NAME+"/git/refs"%(username)
    body = {
        "ref":"refs/heads/"+branchName,
        "sha":sha,
    }
    response = requests.post(create_branch_url, headers=headers, data=json.dumps(body))
    if response.status_code != 201:
        logger.error("[Pull Request] Error occured while creating branch, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while creating the branch. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    branch_sha = data["object"]["sha"]

    """ Creating Commit """
    if fileName[-4:] == ".xml":
        fileName = fileName[:-4]
    fileName += ".xml"
    commit_url = url + "repos/%s/"+settings.LICENSE_REPO_NAME+"/contents/src/%s"%(username, fileName)
    xmlText = xmlText.encode('utf-8')
    fileContent = base64.b64encode(xmlText)
    body = {
        "path":"src/"+fileName,
        "message":commitMessage,
        "content":fileContent,
        "branch":branchName,
    }
    """ Check if file already exists """
    file_url = "{0}/contents/src/{1}".format(TYPE_TO_URL_LICENSE[PROD], fileName)
    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        """ Creating Commit by updating the file """
        data = json.loads(response.text)
        file_sha = data["sha"]
        body["sha"] = file_sha
    response = requests.put(commit_url, headers=headers, data=json.dumps(body))
    if not (response.status_code==201 or response.status_code==200):
        logger.error("[Pull Request] Error occured while making commit, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while making commit. Please try again later or contact the SPDX Team."
        }

    """ Making Pull Request """
    pr_url = "{0}/pulls".format(TYPE_TO_URL_LICENSE[PROD])
    body = {
        "title": prTitle,
        "body": prBody,
        "head": "%s:%s"%(username, branchName),
        "base": "master",
    }
    response = requests.post(pr_url, headers=headers, data=json.dumps(body))
    if response.status_code != 201:
        logger.error("[Pull Request] Error occured while making pull request, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while making the pull request. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    return {
        "type":"success",
        "pr_url": data["html_url"],
    }


def makeNsPullRequest(username, token, branchName, updateUpstream, fileName, commitMessage, prTitle, prBody, xmlText):
    logging.basicConfig(filename="error.log", format="%(levelname)s : %(asctime)s : %(message)s")
    logger = logging.getLogger()

    url = "https://api.github.com/"
    headers = {
        "Accept":"application/vnd.github.machine-man-preview+json",
        "Authorization":"bearer "+token,
        "Content-Type":"application/json",
    }

    """ Making a fork """

    fork_url = "{0}/forks".format(TYPE_TO_URL_NAMESPACE[NORMAL])
    response = requests.get(fork_url, headers=headers)
    data = json.loads(response.text)
    forks = [fork["owner"]["login"] for fork in data]
    if not username in forks:
        """ If user has not forked the repo """
        response = requests.post(fork_url, headers=headers)
        if response.status_code != 202:
            logger.error("[Pull Request] Error occured while creating fork, for %s user. "%(username)+response.text)
            return {
                "type":"error",
                "message":"Error occured while creating a fork of the repo. Please try again later or contact the SPDX Team."
            }
    else:
        if(updateUpstream=="true"):
            """ If user wants to update the forked repo with upstream master """
            update_url = "{0}/git/refs/heads/master".format(TYPE_TO_URL_NAMESPACE[NORMAL])
            response = requests.get(update_url, headers=headers)
            data = json.loads(response.text)
            sha = data["object"]["sha"]
            body = {
                "sha":sha,
                "force": True
            }
            update_url = url+"repos/%s/"+settings.NAMESPACE_REPO_NAME+"/git/refs/heads/master"%(username)
            response = requests.patch(update_url, headers=headers, data=json.dumps(body))
            if response.status_code!=200:
                logger.error("[Pull Request] Error occured while updating fork, for %s user. "%(username)+response.text)
                return {
                    "type":"error",
                    "message":"Error occured while updating fork with the upstream master. Please try again later or contact the SPDX Team."
                }


    """ Getting ref of master branch """
    ref_url = url + "repos/%s/"+settings.NAMESPACE_REPO_NAME+"/git/refs/heads/master"%(username)
    response = requests.get(ref_url, headers=headers)
    if response.status_code != 200:
        logger.error("[Pull Request] Error occured while getting ref of master branch, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while getting the ref of master branch. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    sha = str(data["object"]["sha"])

    """ Getting names of all branches """
    branch_url = url + "repos/%s/"+settings.NAMESPACE_REPO_NAME+"/branches"%(username)
    response = requests.get(branch_url, headers=headers)
    if response.status_code != 200:
        logger.error("[Pull Request] Error occured while getting branch names, for %s user. "%(username)+response.text)
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
    create_branch_url = url + "repos/%s/"+settings.NAMESPACE_REPO_NAME+"/git/refs"%(username)
    body = {
        "ref":"refs/heads/"+branchName,
        "sha":sha,
    }
    response = requests.post(create_branch_url, headers=headers, data=json.dumps(body))
    if response.status_code != 201:
        logger.error("[Pull Request] Error occured while creating branch, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while creating the branch. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    branch_sha = data["object"]["sha"]

    """ Creating Commit """
    if fileName[-4:] == ".xml":
        fileName = fileName[:-4]
    fileName += ".xml"
    commit_url = url + "repos/%s/"+settings.NAMESPACE_REPO_NAME+"/contents/src/%s"%(username, fileName)
    xmlText = xmlText.encode('utf-8')
    fileContent = base64.b64encode(xmlText)
    body = {
        "path":"src/"+fileName,
        "message":commitMessage,
        "content":fileContent,
        "branch":branchName,
    }
    """ Check if file already exists """
    file_url = "{0}//contents/src/{1}".format(TYPE_TO_URL_NAMESPACE[NORMAL], fileName)
    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        """ Creating Commit by updating the file """
        data = json.loads(response.text)
        file_sha = data["sha"]
        body["sha"] = file_sha
    response = requests.put(commit_url, headers=headers, data=json.dumps(body))
    if not (response.status_code==201 or response.status_code==200):
        logger.error("[Pull Request] Error occured while making commit, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while making commit. Please try again later or contact the SPDX Team."
        }

    """ Making Pull Request """
    pr_url = "{0}/pulls".format(TYPE_TO_URL_NAMESPACE[NORMAL])
    body = {
        "title": prTitle,
        "body": prBody,
        "head": "%s:%s"%(username, branchName),
        "base": "master",
    }
    response = requests.post(pr_url, headers=headers, data=json.dumps(body))
    if response.status_code != 201:
        logger.error("[Pull Request] Error occured while making pull request, for %s user. "%(username)+response.text)
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
    license_json = "https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json"
    data = requests.get(license_json).text
    data = json.loads(data)
    url= "https://raw.githubusercontent.com/spdx/license-list-XML/master/src/"
    for license in data["licenses"]:
        if(license["licenseId"] == name):
            url+=name
            return [url, name]
        elif(license["name"] == name):
            url+=license["licenseId"]
            return [url, license["licenseId"]]

    """ Check if an exception name exists """
    exceptions_json = "https://raw.githubusercontent.com/spdx/license-list-data/master/json/exceptions.json"
    data = requests.get(exceptions_json).text
    data = json.loads(data)
    url= "https://raw.githubusercontent.com/spdx/license-list-XML/master/src/exceptions/"
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
    license_list_url = url+"repos/spdx/license-list-data/contents/json/licenses.json"
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
    # Check if a license exists on the SPDX license list
    # check internet connection
    if isConnected():
        licenseInListDict = licenseInList(namespace, namespaceId, token)
        return licenseInListDict
    return {"exists": False}


def createLicenseNamespaceIssue(licenseNamespace, token, urlType):
    """ View for creating an GitbHub issue
    when submitting a new license namespace
    """
    body = '**1.** License Namespace: ' + licenseNamespace.namespace + '\n**2.** Short identifier: ' + licenseNamespace.shortIdentifier + '\n**3.** License Author or steward: ' + licenseNamespace.licenseAuthorName + '\n**4.** Description: ' + licenseNamespace.description + '\n**5.** Submitter name: ' + licenseNamespace.fullname + '\n**6.** URL: ' + licenseNamespace.url
    title = 'New license namespace request: ' + licenseNamespace.shortIdentifier + ' [SPDX-Online-Tools]'
    payload = {'title' : title, 'body': body, 'labels': ['new license namespace/exception request']}
    headers = {'Authorization': 'token ' + token}
    url = "{0}/issues".format(TYPE_TO_URL_NAMESPACE[urlType])
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    return r.status_code


def generateLicenseXml(licenseOsi, licenseIdentifier, licenseName, listVersionAdded, licenseSourceUrls, licenseHeader, licenseNotes, licenseText):
    """ View for generating a spdx license xml
    returns the license xml as a string
    """
    root = ET.Element("SPDXLicenseCollection", xmlns="http://www.spdx.org/license")
    if licenseOsi=="Approved":
        licenseOsi = "true"
    else:
        licenseOsi = "false"
    license = ET.SubElement(root, "license", isOsiApproved=licenseOsi, licenseId=licenseIdentifier, name=licenseName, listVersionAdded=listVersionAdded)
    crossRefs = ET.SubElement(license, "crossRefs")
    for sourceUrl in licenseSourceUrls:
        ET.SubElement(crossRefs, "crossRef").text = sourceUrl
    ET.SubElement(license, "standardLicenseHeader").text = licenseHeader
    ET.SubElement(license, "notes").text = licenseNotes
    licenseTextElement = ET.SubElement(license, "text")
    licenseLines = licenseText.replace('\r','').split('\n')
    for licenseLine in licenseLines:
        ET.SubElement(licenseTextElement, "p").text = licenseLine
    xmlString = ET.tostring(root, method='xml').replace('>','>\n')
    return xmlString


def createIssue(licenseAuthorName, licenseName, licenseIdentifier, licenseComments, licenseSourceUrls, licenseHeader, licenseOsi, licenseRequestUrl, token, urlType):
    """ View for creating an GitHub issue
    when submitting a new license request
    """
    body = '**1.** License Name: ' + licenseName + '\n**2.** Short identifier: ' + licenseIdentifier + '\n**3.** License Author or steward: ' + licenseAuthorName + '\n**4.** Comments: ' + licenseComments + '\n**5.** Standard License Header: ' + licenseHeader + '\n**6.** License Request Url: ' + licenseRequestUrl + '\n**7.** URL: '
    for url in licenseSourceUrls:
        body += url
        body += '\n'
    body += '**8.** OSI Status: ' + licenseOsi
    title = 'New license request: ' + licenseIdentifier + ' [SPDX-Online-Tools]'
    payload = {'title' : title, 'body': body, 'labels': ['new license/exception request']}
    headers = {'Authorization': 'token ' + token}
    url = TYPE_TO_URL_LICENSE[urlType]
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    return r.status_code


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
        if(len(('{http://www.spdx.org/license}license/{http://www.spdx.org/license}crossRefs')) > 0):
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
            textStr = ET.tostring(textElem).strip()
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
    url = TYPE_TO_URL_LICENSE[urlType]
    res = requests.get(url, params=payload)
    issues = res.json()
    return issues


def get_yet_not_approved_licenses_issues(urlType):
    """ Get all the issues that are yet to be approved by the legal team by sorting them with labels.
    """
    payload = {'state': 'open', 'labels': 'new license/exception request'}
    url = TYPE_TO_URL_LICENSE[urlType]
    response = requests.get(url, params=payload)
    issues = response.json()
    newRequestIssues = []

    # Remove issues with Accepted labels
    for issue in issues:
        if issue is not None and not isinstance(issue, unicode):
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
        if not isinstance(issue, unicode):
            if issue.get('pull_request') is None:
                licenseInfo = issue.get('body')
                if '[SPDX-Online-Tools]' in issue.get('title'):
                    licenseIdentifier = re.search(r'(?im)short identifier:\s([a-zA-Z0-9|.|-]+)', licenseInfo).group(1)
                    licenseIds.append(licenseIdentifier)
                    try:
                        licenseXml = str(LicenseRequest.objects.get(shortIdentifier=licenseIdentifier).xml)
                        licenseText = parseXmlString(licenseXml)['text']
                        licenseTexts.append(clean(licenseText))
                    except LicenseRequest.DoesNotExist:
                        pass
    licenseData = dict(zip(licenseIds, licenseTexts))
    return licenseData


def get_issue_url_by_id(licenseId, issues):
    """ Get the github issue url of the license by license ID and the issues instance.
    """
    return [issue.get('html_url') for issue in issues if issue.get('pull_request') is None if licenseId in issue.get('title')][0]


def check_new_licenses_and_rejected_licenses(inputLicenseText, urlType):
    """ Check  if the license text matches with that of a license that is either
    a not yet approved license or a rejected license.
    returns the close matches of license text along with the license issue URL.
    """
    issues = get_rejected_licenses_issues(urlType)
    notApproved = get_yet_not_approved_licenses_issues(urlType)
    if isinstance(issues, list):
        issues.extend(notApproved)
    licenseData = get_license_data(issues)
    matches = get_close_matches(inputLicenseText, licenseData)
    matches = matches.keys()
    if not matches:
        return matches, ''
    issueUrl = get_issue_url_by_id(matches[0], issues)
    return matches, issueUrl
