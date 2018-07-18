import requests
import json
import base64

def makePullRequest(username, token, branchName, fileName, commitMessage, prTitle, prBody, xmlText):
    url = "https://api.github.com/"
    headers = {
        "Accept":"application/vnd.github.machine-man-preview+json",
        "Authorization":"bearer "+token,
        "Content-Type":"application/json",
    }

    """ Making a fork """
    fork_url = url+"repos/spdx/license-list-XML/forks"
    response = requests.post(fork_url, headers=headers)
    if response.status_code != 202:
        return {
            "type":"error",
            "message":"Error occured while creating a fork of the repo. You might have not given required permissions to the app. Please contact the SPDX Team."
        }

    """ Getting ref of master branch """
    ref_url = url + "repos/%s/license-list-XML/git/refs/heads/master"%(username)
    response = requests.get(ref_url, headers=headers)
    if response.status_code != 200:
        return {
            "type":"error",
            "message":"Some error occured while getting the ref of master branch. Please contact the SPDX Team."
        }
    data = json.loads(response.text)
    sha = str(data["object"]["sha"])

    """ Getting names of all branches """
    branch_url = url + "repos/%s/license-list-XML/branches"%(username)
    response = requests.get(branch_url, headers=headers)
    if response.status_code != 200:
        return {
            "type":"error",
            "message":"Some error occured while getting branch names. Please contact the SPDX Team."
        }
    data = json.loads(response.text)
    branch_names = [i["name"] for i in data]
    
    """ Creating branch """
    i=1
    while True:
        if(branchName in branch_names):
            branchName += str(i)
            i+=1 
        else:
            break
    create_branch_url = url + "repos/%s/license-list-XML/git/refs"%(username)
    body = {
        "ref":"refs/heads/"+branchName,
        "sha":sha,
    }
    response = requests.post(create_branch_url, headers=headers, data=json.dumps(body))
    if response.status_code != 201:
        return {
            "type":"error",
            "message":"Some error occured while creating the branch. Please contact the SPDX Team."
        }
    data = json.loads(response.text)
    branch_sha = data["object"]["sha"]

    """ Creating Commit """
    commit_url = url + "repos/%s/license-list-XML/contents/src/%s"%(username, fileName)
    fileContent = base64.b64encode(xmlText)
    body = {
        "path":"src/"+fileName+".xml",
        "message":commitMessage,
        "content":fileContent,
        "branch":branchName,
    }
    response = requests.put(commit_url, headers=headers, data=json.dumps(body))
    if response.status_code != 201:
        return {
            "type":"error",
            "message":"Some error occured while making commit. Please contact the SPDX Team."
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
        return {
            "type":"error",
            "message":"Some error occured while making the pull request. Please contact the SPDX Team."
        }
    data = json.loads(response.text)
    return {
        "type":"success",
        "pr_url": data["html_url"],
    }
