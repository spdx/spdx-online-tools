# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.viewsets import ModelViewSet
from models import ValidateFileUpload,ConvertFileUpload,CompareFileUpload
from serializers import ValidateSerializer,ConvertSerializer,CompareSerializer,ValidateSerializerReturn,ConvertSerializerReturn,CompareSerializerReturn
from rest_framework import status
from rest_framework.decorators import api_view,renderer_classes
from rest_framework.renderers import BrowsableAPIRenderer,JSONRenderer
from django.core.files.storage import FileSystemStorage
from django.conf import settings

import jpype
import traceback
import os

class ValidateViewSet(ModelViewSet):
    
    queryset = ValidateFileUpload.objects.all()
    serializer_class = ValidateSerializerReturn
    parser_classes = (MultiPartParser, FormParser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user,
                       file=self.request.data.get('file'))

class ConvertViewSet(ModelViewSet):
    
    queryset = ConvertFileUpload.objects.all()
    serializer_class = ConvertSerializerReturn
    parser_classes = (MultiPartParser, FormParser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user,
                       file=self.request.data.get('file'),type=self.request.data.get('type'),result=self.request.data.get('result'))

class CompareViewSet(ModelViewSet):
    
    queryset = CompareFileUpload.objects.all()
    serializer_class = CompareSerializerReturn
    parser_classes = (MultiPartParser, FormParser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user,
                       file1=self.request.data.get('file1'),file2=self.request.data.get('file2'),result=self.request.data.get('result'))


@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def validate(request):
    if request.method == 'GET':
        query = ValidateFileUpload.objects.all()
        serializer = ValidateSerializer(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ValidateSerializer(data=request.data)
        if serializer.is_valid():
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =os.path.abspath(".")+"/tool.jar"
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ If JVM started, attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            verifyclass = package.Verify
            try :
                if request.FILES["file"]:
                    """ Saving file to the media directory """
                    myfile = request.FILES['file']
                    folder = "api/"+str(request.user) +"/"+ str(int(time())
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,base_url=urljoin(settings.MEDIA_URL, folder+'/'))
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    """ Call the java function with parameters as list"""
                    retval = verifyclass.verify(settings.APP_DIR+uploaded_file_url)
                    if (len(retval) > 0):
                        result = "The following error(s)/warning(s) were raised: " + str(retval)
                        returnstatus = status.HTTP_400_BAD_REQUEST
                        jpype.detachThreadFromJVM()
                    else :
                        result = "This SPDX Document is valid."
                        returnstatus = status.HTTP_201_CREATED
                        jpype.detachThreadFromJVM()
                else :
                    result = "File Not Uploaded"
                    returnstatus = status.HTTP_400_BAD_REQUEST
                    jpype.detachThreadFromJVM()
            except jpype.JavaException,ex :
                """ Error raised by verifyclass.verify without exiting the application"""
                result = jpype.JavaException.message(ex) #+ "This SPDX Document is not a valid RDF/XML or tag/value format"
                returnstatus = status.HTTP_400_BAD_REQUEST
                jpype.detachThreadFromJVM()
            except :
                traceback.print_exc()
                result = "Other Exception Raised."
                returnstatus = status.HTTP_400_BAD_REQUEST
                jpype.detachThreadFromJVM()
            query = ValidateFileUpload.objects.create(owner=request.user,file=request.data.get('file'),result=result)
            serial = ValidateSerializerReturn(instance=query)
            return Response(serial.data, status=returnstatus)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def convert(request):
    if request.method == 'GET':
        query = ConvertFileUpload.objects.all()
        serializer = ConvertSerializer(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ConvertSerializer(data=request.data)
        if serializer.is_valid():
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =os.path.abspath(".")+"/tool.jar"
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ If JVM started, attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            result = ""
            try :
                if request.FILES["file"]:
                    """ Saving file to the media directory """
                    myfile = request.FILES['file']
                    folder = "api/"+str(request.user) +"/"+ str(int(time())
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,base_url=urljoin(settings.MEDIA_URL, folder+'/'))
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    convertfile =  request.POST["cfilename"]
                    option1 = request.POST["from_format"]
                    option2 = request.POST["to_format"]
                    """ Call the java function with parameters as list"""
                    if (option1=="Tag"):
                        print ("Verifing for Tag/Value Document")
                        if (option2=="RDF"):
                            tagtordfclass = package.TagToRDF
                            retval = tagtordfclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile])
                            if (len(retval) > 0):
                                result = "The following error(s)/warning(s) were raised: " + str(retval)
                                returnstatus = status.HTTP_400_BAD_REQUEST
                                jpype.detachThreadFromJVM()
                            else :
                                result = "/media/" + convertfile
                                returnstatus = status.HTTP_201_CREATED
                                jpype.detachThreadFromJVM()
                        elif (option2=="Spreadsheet"):
                            tagtosprdclass = package.TagToSpreadsheet
                            retval = tagtosprdclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile])
                            if (len(retval) > 0):
                                result = "The following error(s)/warning(s) were raised: " + str(retval)
                                returnstatus = status.HTTP_400_BAD_REQUEST
                                jpype.detachThreadFromJVM()
                            else :
                                result = "/media/" + convertfile
                                returnstatus = status.HTTP_201_CREATED
                                jpype.detachThreadFromJVM()
                        else :
                            result = "Select valid conversion types."
                            returnstatus = status.HTTP_400_BAD_REQUEST
                            jpype.detachThreadFromJVM()
                    elif (option1=="RDF"):
                        print ("Verifing for RDF Document")
                        if (option2=="Tag"):
                            rdftotagclass = package.RdfToTag
                            retval = rdftotagclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile])
                            if (len(retval) > 0):
                                result = "The following error(s)/warning(s) were raised: " + str(retval)
                                returnstatus = status.HTTP_400_BAD_REQUEST
                                jpype.detachThreadFromJVM()
                            else :
                                result = "/media/" + convertfile
                                returnstatus = status.HTTP_201_CREATED
                                jpype.detachThreadFromJVM()
                        elif (option2=="Spreadsheet"):
                            rdftosprdclass = package.RdfToSpreadsheet
                            retval = rdftosprdclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile])
                            if (len(retval) > 0):
                                result = "The following error(s)/warning(s) were raised: " + str(retval)
                                returnstatus = status.HTTP_400_BAD_REQUEST
                                jpype.detachThreadFromJVM()
                            else :
                                result = "/media/" + convertfile
                                returnstatus = status.HTTP_201_CREATED
                                jpype.detachThreadFromJVM()
                        elif (option2=="HTML"):
                            rdftohtmlclass = package.RdfToHtml
                            retval = rdftohtmlclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile])
                            if (len(retval) > 0):
                                result = "The following error(s)/warning(s) were raised: " + str(retval)
                                returnstatus = status.HTTP_400_BAD_REQUEST
                                jpype.detachThreadFromJVM()
                            else :
                                result = "/media/" + convertfile
                                returnstatus = status.HTTP_201_CREATED
                                jpype.detachThreadFromJVM()
                        else :
                            result = "Select valid conversion types."
                            returnstatus = status.HTTP_400_BAD_REQUEST
                            jpype.detachThreadFromJVM()
                    elif (option1=="Spreadsheet"):
                        print ("Verifing for Spreadsheet Document")
                        if (option2=="Tag"):
                            sprdtotagclass = package.SpreadsheetToTag
                            retval = sprdtotagclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile])
                            if (len(retval) > 0):
                                result = "The following error(s)/warning(s) were raised: " + str(retval)
                                returnstatus = status.HTTP_400_BAD_REQUEST
                                jpype.detachThreadFromJVM()
                            else :
                                result = "/media/" + convertfile
                                returnstatus = status.HTTP_201_CREATED
                                jpype.detachThreadFromJVM()
                        elif (option2=="RDF"):
                            sprdtordfclass = package.SpreadsheetToRDF
                            retval = sprdtordfclass.onlineFunction([settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile])
                            if (len(retval) > 0):
                                result = "The following error(s)/warning(s) were raised: " + str(retval)
                                returnstatus = status.HTTP_400_BAD_REQUEST
                                jpype.detachThreadFromJVM()
                            else :
                                result = "/media/" + convertfile
                                returnstatus = status.HTTP_201_CREATED
                                jpype.detachThreadFromJVM()
                        else :
                            result = "Select valid conversion types."
                            returnstatus = status.HTTP_400_BAD_REQUEST
                            jpype.detachThreadFromJVM()
                else :
                    result = "File Not Found"
                    returnstatus = status.HTTP_400_BAD_REQUEST
                    jpype.detachThreadFromJVM()
            except jpype.JavaException,ex :
                result = jpype.JavaException.message(ex)
                returnstatus = status.HTTP_400_BAD_REQUEST
                jpype.detachThreadFromJVM() 
            except :
                traceback.print_exc()
                result = "Other Exception Raised."
                returnstatus = status.HTTP_400_BAD_REQUEST
                jpype.detachThreadFromJVM() 
            query = ConvertFileUpload.objects.create(owner=request.user,file=request.data.get('file'),result=result,from_format=request.POST["from_format"],to_format=request.POST["to_format"],cfilename=request.POST["cfilename"])
            serial = ConvertSerializerReturn(instance=query)
            return Response(serial.data, status=returnstatus)   
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def compare(request):
    if request.method == 'GET':
        query = CompareFileUpload.objects.all()
        serializer = CompareSerializerReturn(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CompareSerializer(data=request.data)
        if serializer.is_valid():
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =os.path.abspath(".")+"/tool.jar"
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ If JVM started, attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            verifyclass = package.Verify
            compareclass = package.CompareMultpleSpdxDocs
            result=""
            erroroccurred = False
            try :
                if (request.FILES["file1"] and request.FILES["file2"]):
                    rfilename = request.POST["rfilename"]+".xlsx"
                    folder = "api/"+str(request.user) +"/"+ str(int(time())
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,base_url=urljoin(settings.MEDIA_URL, folder+'/'))
                    callfunc = [settings.MEDIA_ROOT+"/"+ folder+"/"+rfilename]
                    file1 = request.FILES["file1"]
                    file2 = request.FILES["file2"]
                    filename1 = fs.save(file1.name, file1)
                    uploaded_file_url1 = fs.url(filename1)
                    filename2 = fs.save(file2.name, file2)
                    uploaded_file_url2 = fs.url(filename2)
                    callfunc.append(settings.APP_DIR+uploaded_file_url1)
                    callfunc.append(settings.APP_DIR+uploaded_file_url2)
                    retval1 = verifyclass.verifyRDFFile(settings.APP_DIR+uploaded_file_url1)
                    if (len(retval1) > 0):
                        erroroccurred = True
                        result = "The following error(s)/warning(s) were raised by " + str(file1.name) + ": " +str(retval1)
                        returnstatus = status.HTTP_400_BAD_REQUEST
                    retval2 = verifyclass.verifyRDFFile(settings.APP_DIR+uploaded_file_url2)
                    if (len(retval2) > 0):
                        erroroccurred = True
                        result += "The following error(s)/warning(s) were raised by " + str(file1.name) + ": " +str(retval2)
                        returnstatus = status.HTTP_400_BAD_REQUEST
                    if (erroroccurred == False):
                        compareclass.onlineFunction(callfunc)
                        result = "/media/" + rfilename
                        returnstatus = status.HTTP_201_CREATED
                    jpype.detachThreadFromJVM()
                else :
                    result = "File Not Uploaded"
                    returnstatus = status.HTTP_400_BAD_REQUEST
                    jpype.detachThreadFromJVM()
            except jpype.JavaException,ex :
                """ Error raised by verifyclass.verify without exiting the application"""
                result = jpype.JavaException.message(ex) #+ "This SPDX Document is not a valid RDF/XML or tag/value format"
                returnstatus = status.HTTP_400_BAD_REQUEST
                jpype.detachThreadFromJVM()
            except :
                traceback.print_exc()
                result = "Other Exception Raised."
                returnstatus = status.HTTP_400_BAD_REQUEST
                jpype.detachThreadFromJVM()
            query = CompareFileUpload.objects.create(owner=request.user,file1=request.data.get('file1'),file2=request.data.get('file2'),rfilename = rfilename, result=result)
            serial = CompareSerializerReturn(instance=query)
            return Response(serial.data, status=returnstatus)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)