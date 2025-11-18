# SPDX-FileCopyrightText: 2022-2025 SPDX contributors
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: Apache-2.0

"""This file contains the core logic used in the SPDX Online Tools' APP and API"""

import os
import re
import sys
from io import StringIO
from json import dumps
from time import time
from traceback import format_exc
from urllib.parse import urljoin

import jpype
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.datastructures import MultiValueDictKeyError
from ntia_conformance_checker import SbomChecker
from spdx_license_matcher.utils import get_spdx_license_text

import app.utils as utils


def initialise_jpype():
    """Start JVM if not already started, attach a Thread and start processing the request

    The SPDX Online Tools must control the lifecycle of the JVM itself,
    since the CLASSPATH must be set to include the tool.jar file in a specifc
    location (JAR_ABSOLUTE_PATH in settings).
    If we let libraries, like spdx_license_matcher, start the JVM, they may not
    include the correct tool.jar in the CLASSPATH.
    """

    # Check is the JVM is already running or not. If not, start JVM.
    if not jpype.isJVMStarted():
        jpype.startJVM(
            "-ea", "-Djava.awt.headless=true", classpath=settings.JAR_ABSOLUTE_PATH
        )
    # Attach a thread to JVM and start processing
    jpype.attachThreadToJVM()
    jpype.JPackage("org.spdx.library").SpdxModelFactory.init()


def license_compare_helper(request):
    """
    A helper function to compare two given licenses.
    """
    package = jpype.JPackage("org.spdx.tools")
    verifyclass = package.Verify
    compareclass = package.CompareSpdxDocs
    helperclass = package.SpdxToolsHelper
    ajaxdict = dict()
    filelist = list()
    errorlist = list()
    result = {}
    context_dict = {}

    try:
        if request.FILES["files"]:
            rfilename = request.POST["rfilename"] + ".xlsx"
            # create a stable folder name and separate filesystem path vs URL
            folder = f"{request.user}/{int(time())}"
            folder_path = os.path.join(settings.MEDIA_ROOT, folder)
            folder_url = urljoin(settings.MEDIA_URL, folder + "/")
            callfunc = [os.path.join(folder_path, rfilename)]
            erroroccurred = False
            warningoccurred = False
            if (len(request.FILES.getlist("files")) < 2):
                context_dict["error"] = "Please select at least 2 files"
                result['status'] = 404
                result['context'] = context_dict
                return result
            # Loop through the list of files
            fs = FileSystemStorage(location=folder_path, base_url=folder_url)
            for myfile in request.FILES.getlist("files"):
                filename = fs.save(utils.removeSpecialCharacters(myfile.name), myfile)
                local_path = fs.path(filename)
                callfunc.append(str(local_path))
                nameoffile, fileext = os.path.splitext(filename)
                if (nameoffile.endswith(".rdf") and fileext == ".xml") or fileext == ".rdf":
                    fileext = ".rdfxml"
                elif fileext == ".spdx":
                    fileext = ".tag"
                try:
                    filetype = helperclass.strToFileType(fileext[1:])
                    try :
                        # Call the Java function to verify for valid SPDX files.
                        retval = verifyclass.verify(str(local_path), filetype)
                        if (len(retval) > 0):
                            # If warnings raised
                            warningoccurred = True
                            filelist.append(myfile.name)
                            errorlist.append(str(retval))
                        else :
                            filelist.append(myfile.name)
                            errorlist.append("No errors found")
                    except jpype.JException as ex:
                        # Error raised by verifyclass.verifyRDFFile without exiting the application
                        filelist.append(myfile.name)
                        errorlist.append(jpype.JException.message(ex))
                    except Exception:
                        # Other Exceptions
                        erroroccurred = True
                        filelist.append(myfile.name)
                        errorlist.append(format_exc())
                except Exception:
                    # Invalid file extension
                    erroroccurred = True
                    filelist.append(myfile.name)
                    errorlist.append("Invalid file extension for "+filename+".  Must be .xls, .xlsx, .xml, .json, .yaml, .spdx, .rdfxml")
                    errorlist.append(format_exc())
            if erroroccurred is False:
                # If no errors in any of the file,call the java function with parameters as list
                try :
                    compareclass.onlineFunction(callfunc)
                except Exception:
                    # Error raised by onlineFunction
                    if utils.is_ajax(request):
                        ajaxdict["type"] = "warning2"
                        ajaxdict["files"] = filelist
                        ajaxdict["errors"] = errorlist
                        ajaxdict["toolerror"] = format_exc()
                        response = dumps(ajaxdict)
                        result['status'] = 400
                        result['response'] = response
                        return result
                    context_dict["type"] = "warning2"
                    context_dict["error"]= errorlist
                    result['status'] = 400
                    result['context'] = context_dict
                    return result
                if warningoccurred is False:
                    # If no warning raised """
                    if utils.is_ajax(request):
                        ajaxdict["medialink"] = folder_url + rfilename
                        response = dumps(ajaxdict)
                        result['response'] = response
                        return result
                    context_dict["Content-Type"] = "application/vnd.ms-excel"
                    context_dict['Content-Disposition'] = 'attachment; filename="{}"'.format(rfilename)
                    context_dict["medialink"] = folder_url + rfilename
                    result['status'] = 200
                    result['context'] = context_dict
                    return result
                else :
                    if utils.is_ajax(request):
                        ajaxdict["type"] = "warning"
                        ajaxdict["files"] = filelist
                        ajaxdict["errors"] = errorlist
                        ajaxdict["medialink"] = folder_url + rfilename
                        response = dumps(ajaxdict)
                        result['status'] = 406
                        result['response'] = response
                        return result
                    context_dict["Content-Type"] = "application/vnd.ms-excel"
                    context_dict['Content-Disposition'] = 'attachment; filename="{}"'.format(rfilename)
                    context_dict["type"] = "warning"
                    context_dict["medialink"] = folder_url + rfilename
                    result['status'] = 406
                    result['context'] = context_dict
                    return result
            else :
                if utils.is_ajax(request):
                    ajaxdict["files"] = filelist
                    ajaxdict["type"] = "error"
                    ajaxdict["errors"] = errorlist
                    response = dumps(ajaxdict)
                    result['status'] = 400
                    result['response'] = response
                    return result
                context_dict["type"] = "error"
                context_dict["error"] = errorlist
                result['status'] = 400
                result['context'] = context_dict
                return result
        else :
            context_dict["error"] = "File Not Uploaded"
            context_dict["type"] = "error"
            result['status'] = 404
            result['context'] = context_dict
            return result

    except MultiValueDictKeyError:
        # If no files uploaded
        if utils.is_ajax(request):
            filelist.append("Files not selected.")
            errorlist.append("Please select at least 2 files.")
            ajaxdict["files"] = filelist
            ajaxdict["type"] = "error"
            ajaxdict["errors"] = errorlist
            response = dumps(ajaxdict)
            result['status'] = 404
            result['response'] = response
            return result
        context_dict["error"] = "Select at least two files"
        context_dict["type"] = "error"
        result['status'] = 404
        result['context'] = context_dict
        return result


def ntia_check_helper(request):
    """
    A helper function to check the NTIA minimum elements in a given file.
    """
    ajaxdict = dict()
    context_dict = {}
    result = {}
    try:
        if request.FILES["file"]:
            # Saving file to the media directory
            myfile = request.FILES["file"]
            folder = f"{request.user}/{int(time())}"
            folder_path = os.path.join(settings.MEDIA_ROOT, folder)
            folder_url = urljoin(settings.MEDIA_URL, folder + "/")
            fs = FileSystemStorage(location=folder_path, base_url=folder_url)
            filename = fs.save(utils.removeSpecialCharacters(myfile.name), myfile)
            local_path = fs.path(filename)
            # Get other request parameters
            sbom_spec = "spdx2"
            format_ = request.POST.get("format", "").strip()
            if format_.startswith("SPDX3"):
                sbom_spec = "spdx3"
            compliance = request.POST.get("compliance", "ntia")  # Default: "ntia"

            # Call the Python SBOM Checker
            schecker = SbomChecker(
                f"{str(local_path)}",
                compliance=compliance,
                sbom_spec=sbom_spec,
            )
            html = schecker.output_html()

            if "Conformant: False" in html:
                if utils.is_ajax(request):
                    ajaxdict["type"] = "warning"
                    ajaxdict["data"] = (
                        "<div class='res-container'>\n" + html + "</div>\n"
                    )
                    response = dumps(ajaxdict)
                    result["response"] = response
                    result["status"] = 400
                    return result

                context_dict["error"] = (
                    "This SPDX document does not meet conformance standards."
                )
                result["context"] = context_dict
                result["status"] = 400
                return result

            # Conformat: True
            if utils.is_ajax(request):
                ajaxdict["type"] = "success"
                ajaxdict["data"] = (
                    "<div class='res-container'>\n" + html + "</div>\n"
                )
                response = dumps(ajaxdict)
                result["response"] = response
                result["status"] = 200
                return result

            result["message"] = "This SPDX document is valid."
            result["status"] = 200
            return result
        else:
            # If no file uploaded.
            if utils.is_ajax(request):
                ajaxdict = dict()
                ajaxdict["type"] = "error"
                ajaxdict["data"] = "No file uploaded"
                response = dumps(ajaxdict)
                result['response'] = response
                result['status'] = 404
                return result
            context_dict["error"] = "No file uploaded"
            result['context'] = context_dict
            result['status'] = 404
            return result
    except MultiValueDictKeyError:
        # If no files selected
        if utils.is_ajax(request):
            ajaxdict = dict()
            ajaxdict["type"] = "error"
            ajaxdict["data"] = "No files selected."
            response = dumps(ajaxdict)
            result['response'] = response
            result['status'] = 404
            return result
        context_dict["error"] = "No files selected."
        result['context'] = context_dict
        result['status'] = 404
        return result
    except Exception:
        # Other error raised
        if utils.is_ajax(request):
            ajaxdict = dict()
            ajaxdict["type"] = "error"
            ajaxdict["data"] = (
                "<p class='error-log-lead'>Unexpected error found:</p>"
                + "<pre class='error-log'>"
                + format_exc()
                + "</pre>"
            )
            response = dumps(ajaxdict)
            result['response'] = response
            result['status'] = 400
            return result
        context_dict["error"] = format_exc()
        result['context'] = context_dict
        result['status'] = 400
        return result


def license_validate_helper(request):
    """
    A helper function to validate the given license file in various formats.
    """
    package = jpype.JPackage("org.spdx.tools")
    verifyclass = package.Verify
    ajaxdict = dict()
    context_dict = {}
    result = {}
    try :
        if request.FILES["file"]:
            # Saving file to the media directory
            myfile = request.FILES['file']
            folder = f"{request.user}/{int(time())}"
            folder_path = os.path.join(settings.MEDIA_ROOT, folder)
            folder_url = urljoin(settings.MEDIA_URL, folder + '/')
            fs = FileSystemStorage(location=folder_path, base_url=folder_url)
            filename = fs.save(utils.removeSpecialCharacters(myfile.name), myfile)
            local_path = fs.path(filename)
            formatstr = request.POST["format"]
            serFileTypeEnum = jpype.JClass("org.spdx.tools.SpdxToolsHelper$SerFileType")
            fileformat = serFileTypeEnum.valueOf(formatstr)

            # Call the Java function with parameters
            retval = verifyclass.verify(str(local_path), fileformat)

            if (len(retval) > 0):
                # If any warnings are returned
                if utils.is_ajax(request):
                    ajaxdict["type"] = "warning"
                    warnings = str(retval)
                    ajaxdict["data"] = "The following warning(s) were raised:<br />\n" + warnings.replace('\n', '<br />\n')
                    response = dumps(ajaxdict)
                    result['response'] = response
                    result['status'] = 400
                    return result
                context_dict["error"] = retval
                result['context'] = context_dict
                result['status'] = 400
                return result
            if utils.is_ajax(request):
                # Valid SPDX document
                ajaxdict["data"] = "This SPDX document is valid."
                response = dumps(ajaxdict)
                result['response'] = response
                result['status'] = 200
                return result
            message = "This SPDX document is valid."
            result['message'] = message
            result['status'] = 200
            return result
        else :
            # If no file uploaded
            if utils.is_ajax(request):
                ajaxdict = dict()
                ajaxdict["type"] = "error"
                ajaxdict["data"] = "No file uploaded"
                response = dumps(ajaxdict)
                result['response'] = response
                result['status'] = 404
                return result
            context_dict["error"] = "No file uploaded"
            result['context'] = context_dict
            result['status'] = 404
            return result
    except jpype.JException as ex :
        # Error raised by verifyclass.verify without exiting the application
        if utils.is_ajax(request):
            ajaxdict = dict()
            ajaxdict["type"] = "error"
            ajaxdict["data"] = jpype.JException.message(ex)
            response = dumps(ajaxdict)
            result['response'] = response
            result['status'] = 400
            return result
        context_dict["error"] = jpype.JException.message(ex)
        result['context'] = context_dict
        result['status'] = 400
        return result
    except MultiValueDictKeyError:
        # If no files selected
        if utils.is_ajax(request):
            ajaxdict = dict()
            ajaxdict["type"] = "error"
            ajaxdict["data"] = "No files selected."
            response = dumps(ajaxdict)
            result['response'] = response
            result['status'] = 404
            return result
        context_dict["error"] = "No files selected."
        result['context'] = context_dict
        result['status'] = 404
        return result
    except Exception:
        # Other error raised
        if utils.is_ajax(request):
            ajaxdict = dict()
            ajaxdict["type"] = "error"
            ajaxdict["data"] = format_exc()
            response = dumps(ajaxdict)
            result['response'] = response
            result['status'] = 400
            return result
        context_dict["error"] = format_exc()
        result['context'] = context_dict
        result['status'] = 400
        return result


def license_check_helper(request):
    """
    A helper function to check if the given license text is present in the SPDX License List.
    """
    result = {}
    context_dict = {}
    licensetext = request.POST.get('licensetext')
    licensetext = licensetext if licensetext else request.data.get('licensetext')
    try:
        matchingId, matchingType, _ = utils.check_spdx_license(licensetext)
        if not matchingId:
            if utils.is_ajax(request):
                ajaxdict = dict()
                ajaxdict["data"] = "There are no matching SPDX listed licenses"
                response = dumps(ajaxdict)
                result['response'] = response
                result['status'] = 400
                return result
            context_dict["error"] = "There are no matching SPDX listed licenses"
            result['context'] = context_dict
            result['status'] = 404
            return result
        else:
            matching_str = matchingType + " found.<br />The following license ID(s) match: "
            if isinstance(matchingId, list):
                matchingId = ",".join(matchingId)
            matching_str += matchingId
            if utils.is_ajax(request):
                ajaxdict = dict()
                ajaxdict["data"] = matching_str
                response = dumps(ajaxdict)
                result['response'] = response
                result['status'] = 200
                return result
            context_dict["output"] = str(matching_str)
            result['context'] = context_dict
            result['status'] = 200
            return result
    except jpype.JException as ex :
        # Java exception raised without exiting the application
        if utils.is_ajax(request):
            ajaxdict = dict()
            ajaxdict["data"] = jpype.JException.message(ex)
            response = dumps(ajaxdict)
            result['response'] = response
            result['status'] = 404
            return result
        context_dict["error"] = jpype.JException.message(ex)
        result['context'] = context_dict
        result['status'] = 404
        return result
    except Exception:
        # Other exception raised
        if utils.is_ajax(request):
            ajaxdict = dict()
            ajaxdict["data"] = format_exc()
            response = dumps(ajaxdict)
            result['response'] = response
            result['status'] = 404
            return result
        context_dict["error"] = format_exc()
        result['context'] = context_dict
        result['status'] = 404
        return result


def license_convert_helper(request):
    """
    A helper function to help in conversion of the license from one format to another.
    """
    package = jpype.JPackage("org.spdx.tools")
    serFileTypeEnum = jpype.JClass("org.spdx.tools.SpdxToolsHelper$SerFileType")
    spdxConverter = package.SpdxConverter
    verifyclass = package.Verify
    ajaxdict = dict()
    result = {}
    context_dict = {}

    try:
        if request.FILES["file"]:
            # Saving file to media directory
            folder = f"{request.user}/{int(time())}"
            folder_path = os.path.join(settings.MEDIA_ROOT, folder)
            folder_url = urljoin(settings.MEDIA_URL, folder + '/')
            myfile = request.FILES['file']
            fs = FileSystemStorage(location=folder_path, base_url=folder_url)
            filename = fs.save(utils.removeSpecialCharacters(myfile.name), myfile)
            local_path = fs.path(filename)
            option1 = request.POST["from_format"]
            option2 = request.POST["to_format"]
            content_type = utils.formatToContentType(option2)
            if "cfileformat" in request.POST :
                cfileformat = request.POST["cfileformat"]
            else :
                cfileformat = utils.getFileFormat(option2)
            convertfile = request.POST["cfilename"] + cfileformat
            fromFileFormat = serFileTypeEnum.valueOf(option1)
            toFileFormat = serFileTypeEnum.valueOf(option2)

            # Call the Java function with parameters as list
            out_path = os.path.join(folder_path, convertfile)
            spdxConverter.convert(str(local_path), str(out_path), fromFileFormat, toFileFormat)
            warnings = verifyclass.verify(str(out_path), toFileFormat)
            if (len(warnings) == 0) :
                # If no warnings raised
                if utils.is_ajax(request):
                    ajaxdict["medialink"] = folder_url + convertfile
                    response = dumps(ajaxdict)
                    result['response'] = response
                    return result
                context_dict['Content-Disposition'] = 'attachment; filename="{}"'.format(convertfile)
                context_dict["medialink"] = folder_url + convertfile
                context_dict["Content-Type"] = content_type
                result['context'] = context_dict
                result['status'] = 200
                return result
            else :
                if utils.is_ajax(request):
                    ajaxdict["type"] = "warning"
                    warnings = str(warnings)
                    ajaxdict["data"] = "The following warning(s) were raised by "+ myfile.name + ":<br />\n" + warnings.replace('\n', '<br />\n')
                    ajaxdict["medialink"] = folder_url + convertfile
                    response = dumps(ajaxdict)
                    result['response'] = response
                    result['status'] = 406
                    return result
                context_dict["error"] = str(warnings)
                context_dict["type"] = "warning"
                context_dict['Content-Disposition'] = 'attachment; filename="{}"'.format(convertfile)
                context_dict["Content-Type"] = content_type
                context_dict["medialink"] = folder_url + convertfile
                result['context'] = context_dict
                result['status'] = 406
                return result
        else :
            context_dict["error"] = "No file uploaded"
            context_dict["type"] = "error"
            result['context'] = context_dict
            result['status'] = 404
            return result
    except jpype.JException as ex :
        # Java exception raised without exiting the application
        if utils.is_ajax(request):
            ajaxdict["type"] = "error"
            ajaxdict["data"] = jpype.JException.message(ex)
            response = dumps(ajaxdict)
            result['response'] = response
            result['status'] = 400
            return result
        context_dict["type"] = "error"
        context_dict["error"] = jpype.JException.message(ex)
        result['context'] = context_dict
        result['status'] = 400
        return result
    except MultiValueDictKeyError:
        # If no files uploaded
        if utils.is_ajax(request):
            ajaxdict["type"] = "error"
            ajaxdict["data"] = "No files selected."
            response = dumps(ajaxdict)
            result['response'] = response
            result['status'] = 404
            return result
        context_dict["type"] = "error"
        context_dict["error"] = "No files selected."
        result['context'] = context_dict
        result['status'] = 404
        return result
    except Exception:
        # Other error raised
        if utils.is_ajax(request):
            ajaxdict["type"] = "error"
            ajaxdict["data"] = format_exc()
            response = dumps(ajaxdict)
            result['response'] = response
            return result
        context_dict["type"] = "error"
        context_dict["error"] = format_exc()
        result['context'] = context_dict
        result['status'] = 400
        return result


def license_diff_helper(request):
    """
    A helper function to check if the given license text is present in the SPDX License List.
    """
    data = {}
    licensetext = request.POST.get('licensetext')
    licensetext = licensetext if licensetext else request.data.get('licensetext')
    try:
        matchingIds, matchingType, _ = utils.check_spdx_license(licensetext)
        matches = ['Perfect match', 'Standard License match', 'Close match']
        if matchingType in matches:
            data['matchType'] = matchingType
            if isinstance(matchingIds, list):
                matchingIds = ", ".join(matchingIds)
            data['inputLicenseText'] = licensetext
            originalLicenseText = get_spdx_license_text(matchingIds)
            data['originalLicenseText'] = originalLicenseText
            data['matchIds'] = matchingIds
            statusCode = 200
            data['statusCode'] = str(statusCode)
            return data
        if not matchingIds:
            data["data"] = "There are no matching SPDX listed licenses"
            response = dumps(data)
            data['response'] = response
            data['status'] = 201
            return data
    except jpype.JException as ex :
        # Java exception raised without exiting the application
        if utils.is_ajax(request):
            ajaxdict = dict()
            ajaxdict["data"] = jpype.JException.message(ex)
            response = dumps(ajaxdict)
            data['response'] = response
            data['status'] = 404
            return data
        data["error"] = jpype.JException.message(ex)
        data['context'] = data
        data['status'] = 404
        return data
    except Exception:
        # Other exception raised
        if utils.is_ajax(request):
            ajaxdict = dict()
            ajaxdict["data"] = format_exc()
            response = dumps(ajaxdict)
            data['response'] = response
            data['status'] = 404
            return data
        data["error"] = format_exc()
        data['context'] = data
        data['status'] = 404
        return data
