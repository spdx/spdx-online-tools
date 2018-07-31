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

import requests
import json
import base64
import logging
from app.models import UserID, User


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
    fork_url = url+"repos/spdx/license-list-XML/forks"
    response = requests.get(fork_url, headers=headers)
    data = json.loads(response.text)
    if(len(data)==0):
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
            update_url = url+"repos/spdx/license-list-XML/git/refs/heads/master"
            response = requests.get(update_url, headers=headers)
            data = json.loads(response.text)
            sha = data["object"]["sha"]
            body = {
                "sha":sha,
                "force": True
            }
            update_url = url+"repos/%s/license-list-XML/git/refs/heads/master"%(username)
            response = requests.patch(update_url, headers=headers, data=json.dumps(body))
            if response.status_code!=200:
                logger.error("[Pull Request] Error occured while updating fork, for %s user. "%(username)+response.text)
                return {
                    "type":"error",
                    "message":"Error occured while updating fork with the upstream master. Please try again later or contact the SPDX Team."
                }


    """ Getting ref of master branch """
    ref_url = url + "repos/%s/license-list-XML/git/refs/heads/master"%(username)
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
    branch_url = url + "repos/%s/license-list-XML/branches"%(username)
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
    create_branch_url = url + "repos/%s/license-list-XML/git/refs"%(username)
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
    commit_url = url + "repos/%s/license-list-XML/contents/src/%s"%(username, fileName)
    xmlText = xmlText.encode('utf-8')
    fileContent = base64.b64encode(xmlText)
    body = {
        "path":"src/"+fileName,
        "message":commitMessage,
        "content":fileContent,
        "branch":branchName,
    }
    response = requests.put(commit_url, headers=headers, data=json.dumps(body))
    if response.status_code != 201:
        logger.error("[Pull Request] Error occured while making commit, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while making commit. Please try again later or contact the SPDX Team."
        }

    """ Making Pull Request """
    pr_url = url + "repos/spdx/license-list-XML/pulls"
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
