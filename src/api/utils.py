from rest_framework import status


def get_json_response_data(response):
    """
    To get all the json data from response.
    """
    httpStatus = response.get('status', None)
    contextDict = response.get('context', None)
    result = response.get('response', None)
    message = response.get('message', 'Success')
    
    if contextDict:
        medialink = contextDict.get('medialink', None)
        error = contextDict.get('error', None)
        outputs = [medialink, result, error]
        result = next(output for output in outputs if output is not None)
    return httpStatus, result, message


def get_return_code(statusCode):
    """
    To get the return status code from http status code.
    """
    if statusCode == 200:
        returnStatus = status.HTTP_200_OK
    elif statusCode == 400:
        returnStatus = status.HTTP_400_BAD_REQUEST
    else:
        returnStatus = status.HTTP_404_NOT_FOUND
    
    return returnStatus


def validate_license_fields(licenseName, licenseIdentifier):
    """ Validate the licenseName and licenseIdentifier
    when submitting a new license
    """
    no_comma_match = bool(re.compile(r'^((?!,).)*$').match(licenseName))
    no_version_match = bool(re.compile(r'^((?!version).)*$').match(licenseName))
    lower_v_match = bool(re.compile(r'^((?!v\.|v\s).)*$').match(licenseName))
    the_match = bool(re.compile(r'^(?!the|The.*$).*$').match(licenseName))

    if not no_comma_match:
        return 'No commas allowed in the fullname of license or exception.'
    elif not no_version_match:
        return 'The word "version" is not spelled out. Use "v" instead of "version".'
    elif not lower_v_match:
        return 'For version, use lower case v and no period or space between v and the version number.'
    elif not the_match:
        return 'The fullname must omit certain words such as "the " for alphabetical sorting purposes.'
    else:
        return '1'
