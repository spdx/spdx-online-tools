"""This file contains the core logic used in the SPDX Online Tools' APP and API"""

import json

from django.http.response import JsonResponse
import jpype
import os
import sys
import unicodedata

from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from json import dumps, loads
from time import time
from traceback import format_exc
from urllib.parse import urljoin

import app.utils as utils
from ntia_conformance_checker import SbomChecker
from io import StringIO



def initialise_jpype():
    """Start JVM if not already started, attach a Thread and start processing the request"""
    
    # Check is the JVM is already running or not. If not, start JVM.
    if not jpype.isJVMStarted():
        classpath = settings.JAR_ABSOLUTE_PATH
        jpype.startJVM(jpype.getDefaultJVMPath(), "-ea", "-Djava.class.path=%s"%classpath)
            
    # Attach a thread to JVM and start processing
    jpype.attachThreadToJVM()


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
            rfilename = request.POST["rfilename"]+".xlsx"
            folder = str(request.user)+"/"+ str(int(time()))
            callfunc = [settings.MEDIA_ROOT+"/"+folder + "/" +rfilename]
            erroroccurred = False
            warningoccurred = False
            if (len(request.FILES.getlist("files")) < 2):
                context_dict["error"] = "Please select atleast 2 files"
                result['status'] = 404
                result['context'] = context_dict
                return result
            """Loop through the list of files"""
            folder = str(request.user) + "/" + str(int(time()))
            fs = FileSystemStorage(location=settings.MEDIA_ROOT + "/" + folder,
                base_url=urljoin(settings.MEDIA_URL, folder+'/')
                )
            for myfile in request.FILES.getlist("files"):
                filename = fs.save(myfile.name, myfile)
                uploaded_file_url = fs.url(filename).replace("%20", " ")
                callfunc.append(settings.APP_DIR+uploaded_file_url)
                nameoffile, fileext = os.path.splitext(filename)
                if (nameoffile.endswith(".rdf") and fileext == ".xml") or fileext == ".rdf":
                    fileext = ".rdfxml"
                elif fileext == ".spdx":
                    fileext = ".tag"
                try:
                    filetype = helperclass.strToFileType(fileext[1:])
                    try :
                        """Call the java function to verify for valid SPDX Files."""
                        retval = verifyclass.verify(settings.APP_DIR+uploaded_file_url, filetype)
                        if (len(retval) > 0):
                            """If warnings raised"""
                            warningoccurred = True
                            filelist.append(myfile.name)
                            errorlist.append(str(retval))
                        else :
                            filelist.append(myfile.name)
                            errorlist.append("No errors found")
                    except jpype.JavaException as ex :
                        """ Error raised by verifyclass.verifyRDFFile without exiting the application"""
                        erroroccurred = True
                        filelist.append(myfile.name)
                        errorlist.append(jpype.JavaException.message(ex))
                    except :
                        """ Other Exceptions"""
                        erroroccurred = True
                        filelist.append(myfile.name)
                        errorlist.append(format_exc())
                except :
                    """Invalid file extension"""
                    erroroccurred = True
                    filelist.append(myfile.name)
                    errorlist.append("Invalid file extension for "+filename+".  Must be .xls, .xlsx, .xml, .json, .yaml, .spdx, .rdfxml")
            if (erroroccurred==False):
                """ If no errors in any of the file,call the java function with parameters as list"""
                try :
                    compareclass.onlineFunction(callfunc)
                except Exception as ex:
                    """Error raised by onlineFunction"""
                    if (request.is_ajax()):
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
                if (warningoccurred==False):
                    """If no warning raised """
                    if (request.is_ajax()):
                        ajaxdict["medialink"] = settings.MEDIA_URL + folder + "/"+ rfilename
                        response = dumps(ajaxdict)
                        result['response'] = response
                        return result
                    context_dict["Content-Type"] = "application/vnd.ms-excel"
                    context_dict['Content-Disposition'] = 'attachment; filename="{}"'.format(rfilename)
                    context_dict["medialink"] = settings.MEDIA_URL + folder + "/" + rfilename
                    result['status'] = 200
                    result['context'] = context_dict
                    return result
                else :
                    if (request.is_ajax()):
                        ajaxdict["type"] = "warning"
                        ajaxdict["files"] = filelist
                        ajaxdict["errors"] = errorlist
                        ajaxdict["medialink"] = settings.MEDIA_URL + folder + "/" + rfilename
                        response = dumps(ajaxdict)
                        result['status'] = 406
                        result['response'] = response
                        return result
                    context_dict["Content-Type"] = "application/vnd.ms-excel"
                    context_dict['Content-Disposition'] = 'attachment; filename="{}"'.format(rfilename)
                    context_dict["type"] = "warning"
                    context_dict["medialink"] = settings.MEDIA_URL + folder + "/" + rfilename
                    result['status'] = 406
                    result['context'] = context_dict
                    return result
            else :
                if (request.is_ajax()):
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
            context_dict["error"]= "File Not Uploaded"
            context_dict["type"] = "error"
            result['status'] = 404
            result['context'] = context_dict
            return result

    except MultiValueDictKeyError:
        """ If no files uploaded"""
        if (request.is_ajax()):
            filelist.append("Files not selected.")
            errorlist.append("Please select atleast 2 files.")
            ajaxdict["files"] = filelist
            ajaxdict["type"] = "error"
            ajaxdict["errors"] = errorlist
            response = dumps(ajaxdict)
            result['status'] = 404
            result['response'] = response
            return result
        context_dict["error"] = "Select atleast two files"
        context_dict["type"] = "error"
        result['status'] = 404
        result['context'] = context_dict
        return result

def ntia_check_helper(request):
    """
       A helper function to check the ntia elements in a given file in various formats.
    """
    ajaxdict = dict()
    context_dict = {}
    result = {}
    try:
        if request.FILES["file"]:
            """ Saving file to the media directory """
            myfile = request.FILES['file']
            folder = str(request.user) + "/" + str(int(time()))
            fs = FileSystemStorage(location=settings.MEDIA_ROOT + "/" + folder,
                                   base_url=urljoin(settings.MEDIA_URL, folder + '/')
                                   )
            filename = fs.save(myfile.name, myfile)
            uploaded_file_url = fs.url(filename).replace("%20", " ")
            """ Call the python SBOM Checker """
            schecker = SbomChecker(str(settings.APP_DIR + uploaded_file_url))
            oldStdout = sys.stdout
            tempstdout = StringIO()
            sys.stdout = tempstdout
            schecker.print_components_missing_info()
            schecker.print_table_output()
            sys.stdout = oldStdout
            retval = tempstdout.getvalue().replace(",",", ").replace("\n","<br/>")
            if not retval.startswith("No components with missing information."):
                """ If any warnings are returned """
                if (request.is_ajax()):
                    ajaxdict["type"] = "warning"
                    ajaxdict["data"] = "The following warning(s) were raised:\n" + str(retval)
                    response = dumps(ajaxdict)
                    result['response'] = response
                    result['status'] = 400
                    return result
                context_dict["error"] = retval
                result['context'] = context_dict
                result['status'] = 400
                return result
            if (request.is_ajax()):
                """ Valid SPDX Document """
                ajaxdict["data"] = "This SPDX Document is valid:\n" + retval
                response = dumps(ajaxdict)
                result['response'] = response
                result['status'] = 200
                return result
            message = "This SPDX Document is valid."
            result['message'] = message
            result['status'] = 200
            return result
        else:
            """ If no file uploaded."""
            if (request.is_ajax()):
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
    except jpype.JException as ex:
        """ Error raised by check_anything.check_minimum_elements without exiting the application"""
        if (request.is_ajax()):
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
        """ If no files selected"""
        if (request.is_ajax()):
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
    except:
        """ Other error raised """
        if (request.is_ajax()):
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
            """ Saving file to the media directory """
            myfile = request.FILES['file']
            folder = str(request.user) + "/" + str(int(time()))
            fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,
                base_url=urljoin(settings.MEDIA_URL, folder+'/')
                )
            filename = fs.save(unicodedata.normalize('NFKD', myfile.name).encode('ASCII', 'ignore').decode('ASCII'), myfile)
            uploaded_file_url = fs.url(filename).replace("%20", " ")
            formatstr = request.POST["format"]
            serFileTypeEnum = jpype.JClass("org.spdx.tools.SpdxToolsHelper$SerFileType")
            fileformat = serFileTypeEnum.valueOf(formatstr)
            """ Call the java function with parameters """
            retval = verifyclass.verify(str(settings.APP_DIR+uploaded_file_url), fileformat)
            if (len(retval) > 0):
                """ If any warnings are returned """
                if (request.is_ajax()):
                    ajaxdict["type"] = "warning"
                    ajaxdict["data"] = "The following warning(s) were raised: " + str(retval)
                    response = dumps(ajaxdict)
                    result['response'] = response
                    result['status'] = 400
                    return result
                context_dict["error"] = retval
                result['context'] = context_dict
                result['status'] = 400
                return result
            if (request.is_ajax()):
                """ Valid SPDX Document """
                ajaxdict["data"] = "This SPDX Document is valid."
                response = dumps(ajaxdict)
                result['response'] = response
                result['status'] = 200
                return result
            message = "This SPDX Document is valid."
            result['message'] = message
            result['status'] = 200
            return result
        else :
            """ If no file uploaded."""
            if (request.is_ajax()):
                ajaxdict=dict()
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
        """ Error raised by verifyclass.verify without exiting the application"""
        if (request.is_ajax()):
            ajaxdict=dict()
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
        """ If no files selected"""
        if (request.is_ajax()):
            ajaxdict=dict()
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
    except :
        """ Other error raised """
        if (request.is_ajax()):
            ajaxdict=dict()
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
            if (request.is_ajax()):
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
            matching_str = matchingType + " found! The following license ID(s) match: "
            if isinstance(matchingId, list):
                matchingId = ",".join(matchingId)
            matching_str += matchingId
            if request.is_ajax():
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
        """ Java exception raised without exiting the application """
        if request.is_ajax():
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
    except :
        """ Other exception raised """
        if request.is_ajax():
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

    try :
        if request.FILES["file"]:
            """ Saving file to media directory """
            folder = str(request.user) + "/" + str(int(time()))
            myfile = request.FILES['file']
            fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,base_url=urljoin(settings.MEDIA_URL, folder+'/'))
            filename = fs.save(myfile.name, myfile)
            uploaded_file_url = fs.url(filename).replace("%20", " ")
            option1 = request.POST["from_format"]
            option2 = request.POST["to_format"]
            content_type = utils.formatToContentType(option2)
            if "cfileformat" in request.POST :
                cfileformat = request.POST["cfileformat"]
            else :
                cfileformat = utils.getFileFormat(option2)
            convertfile =  request.POST["cfilename"] + cfileformat
            fromFileFormat = serFileTypeEnum.valueOf(option1);\
            toFileFormat = serFileTypeEnum.valueOf(option2)
            """ Call the java function with parameters as list """
            spdxConverter.convert(str(settings.APP_DIR+uploaded_file_url),str(settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile), fromFileFormat, toFileFormat)
            warnings = verifyclass.verify(str(settings.MEDIA_ROOT+"/"+folder+"/"+"/"+convertfile), toFileFormat)
            if (len(warnings) == 0) :
                """ If no warnings raised """
                if (request.is_ajax()):
                    ajaxdict["medialink"] = settings.MEDIA_URL + folder + "/"+ convertfile
                    response = dumps(ajaxdict)
                    result['response'] = response
                    return result
                context_dict['Content-Disposition'] = 'attachment; filename="{}"'.format(convertfile)
                context_dict["medialink"] = settings.MEDIA_URL + folder + "/"+ convertfile
                context_dict["Content-Type"] = content_type
                result['context'] = context_dict
                result['status'] = 200
                return result
            else :
                if (request.is_ajax()):
                    ajaxdict["type"] = "warning"
                    ajaxdict["data"] = "The following warning(s) were raised by "+ myfile.name + ": " + str(warnings)
                    ajaxdict["medialink"] = settings.MEDIA_URL + folder + "/"+ convertfile
                    response = dumps(ajaxdict)
                    result['response'] = response
                    result['status'] = 406
                    return result
                context_dict["error"] = str(warnings)
                context_dict["type"] = "warning"
                context_dict['Content-Disposition'] = 'attachment; filename="{}"'.format(convertfile)
                context_dict["Content-Type"] = content_type
                context_dict["medialink"] = settings.MEDIA_URL + folder + "/"+ convertfile
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
        """ Java exception raised without exiting the application"""
        if (request.is_ajax()):
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
        """ If no files uploaded"""
        if (request.is_ajax()):
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
    except :
        """ Other error raised """
        if (request.is_ajax()):
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
            originalLicenseText = utils.get_spdx_license_text(matchingIds)
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
        """ Java exception raised without exiting the application """
        if (request.is_ajax()):
            ajaxdict=dict()
            ajaxdict["data"] = jpype.JException.message(ex)
            response = dumps(ajaxdict)
            data['response'] = response
            data['status'] = 404
            return data
        data["error"] = jpype.JException.message(ex)
        data['context'] = data
        data['status'] = 404
        return data
    except :
        """ Other exception raised """
        if (request.is_ajax()):
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
