# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User, Group
from rest_framework import viewsets
#from serializers import UserSerializer, GroupSerializer
from rest_framework.views import APIView
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
            mainclass = package.Main
            result="default"
            try :
                if (request.FILES["file1"] and request.FILES["file2"]):
                    rfilename = request.POST["rfilename"]+".xlsx"
                    callfunc = ["CompareMultipleSpdxDocs",settings.MEDIA_ROOT+"/"+rfilename]
                    file1 = request.FILES["file1"]
                    file2 = request.FILES["file2"]
                    fs = FileSystemStorage()
                    filename1 = fs.save(file1.name, file1)
                    uploaded_file_url1 = fs.url(filename1)
                    filename2 = fs.save(file2.name, file2)
                    uploaded_file_url2 = fs.url(filename2)
                    verifyclass.verifyRDFFile(settings.APP_DIR+uploaded_file_url1)
                    verifyclass.verifyRDFFile(settings.APP_DIR+uploaded_file_url2)
                    callfunc.append(settings.APP_DIR+uploaded_file_url1)
                    callfunc.append(settings.APP_DIR+uploaded_file_url2)
                    """ Call the java function with parameters as list"""
                    mainclass.main(callfunc)
                    jpype.detachThreadFromJVM()
                    result = "/media/"+rfilename
                else :
                    jpype.detachThreadFromJVM()
                    result = "File Not Uploaded"
            except jpype.JavaException,ex :
                """ Error raised by verifyclass.verify without exiting the application"""
                result = jpype.JavaException.message(ex) #+ "This SPDX Document is not a valid RDF/XML or tag/value format"
                jpype.detachThreadFromJVM()
            except :
                traceback.print_exc()
                result = "Other Exception Raised."
                jpype.detachThreadFromJVM()
            query = CompareFileUpload.objects.create(owner=request.user,file1=request.data.get('file1'),file2=request.data.get('file2'),rfilename = rfilename, result=result)
            serial = CompareSerializerReturn(instance=query)
            return Response(serial.data, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomBrowsableAPIRenderer(BrowsableAPIRenderer):
    def get_default_renderer(self, view):
        return JSONRenderer()

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
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    """ Call the java function with parameters as list"""
                    lis = verifyclass.verify(settings.APP_DIR+uploaded_file_url)
                    print (lis)
                    verifyclass.main([settings.APP_DIR+uploaded_file_url])
                    jpype.detachThreadFromJVM()
                    result = "This SPDX Document is valid."
                else :
                    jpype.detachThreadFromJVM()
                    result = "File Not Uploaded"
            except jpype.JavaException,ex :
                """ Error raised by verifyclass.verify without exiting the application"""
                result = jpype.JavaException.message(ex) #+ "This SPDX Document is not a valid RDF/XML or tag/value format"
                jpype.detachThreadFromJVM()
            except :
                traceback.print_exc()
                result = "Other Exception Raised." 
                jpype.detachThreadFromJVM()    
            query = ValidateFileUpload.objects.create(owner=request.user,file=request.data.get('file'),result=result)
            #serializer.save(owner=request.user,
            #           file=request.data.get('file'),result=result)
            serial = ValidateSerializerReturn(instance=query)
            return Response(serial.data, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            mainclass = package.Main
            try :
                if request.FILES["file"]:
                    """ Saving file to the media directory """
                    myfile = request.FILES['file']
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    convertfile =  request.POST["cfilename"]
                    option1 = request.POST["from_format"]
                    option2 = request.POST["to_format"]
                    functiontocall = option1 + "To" + option2
                    if (option1=="Tag"):
                        print ("Verifing for Tag/Value Document")
                        verifyclass = package.Verify
                        verifyclass.verifyTagFile(settings.APP_DIR+uploaded_file_url)
                    elif (option1=="RDF"):
                        print ("Verifing for RDF Document")
                        verifyclass = package.Verify
                        verifyclass.verifyRDFFile(settings.APP_DIR+uploaded_file_url)
                    """ Call the java function with parameters as list"""
                    mainclass.main([functiontocall,settings.APP_DIR+uploaded_file_url,settings.MEDIA_ROOT+"/"+convertfile])
                    jpype.detachThreadFromJVM()
                    result = "/media/" + convertfile
                else :
                    jpype.detachThreadFromJVM()
                    result = "File Not Found"
            except jpype.JavaException,ex :
                result = jpype.JavaException.message(ex)
                jpype.detachThreadFromJVM()
            except :
                traceback.print_exc()
                result = "Other Exception Raised."
                jpype.detachThreadFromJVM() 
            query = ConvertFileUpload.objects.create(owner=request.user,file=request.data.get('file'),result=result,from_format=option1,to_format=option2,cfilename=convertfile)
            #serializer.save(owner=request.user,
            #           file=request.data.get('file'),result=result)
            serial = ConvertSerializerReturn(instance=query)
            return Response(serial.data, status=status.HTTP_400_BAD_REQUEST)   
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

