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
from serializers import ValidateSerializer,ConvertSerializer,CompareSerializer,ValidateSerializer2
from rest_framework import status
from rest_framework.decorators import api_view,renderer_classes
from rest_framework.renderers import BrowsableAPIRenderer,JSONRenderer
from django.core.files.storage import FileSystemStorage
from django.conf import settings

import jpype
import traceback
import os
# class UserViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint that allows users to be viewed or edited.
#     """
#     queryset = User.objects.all().order_by('-date_joined')
#     serializer_class = UserSerializer


# class GroupViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint that allows groups to be viewed or edited.
#     """
#     queryset = Group.objects.all()
#     serializer_class = GroupSerializer
    
    
# class FileUploadView(APIView):
#     parser_classes = (FileUploadParser, )
#     def post(self, request, format='jpg'):
#         up_file = request.FILES['file']
#         destination = open(up_file.name,'wb+')
#         for chunk in up_file.chunks():
#             destination.write(chunk)
#             destination.close()

#         # ...
#         # do some stuff with uploaded file
#         # ...
#         return Response(up_file.name, status=201)

class CustomBrowsableAPIRenderer(BrowsableAPIRenderer):
    def get_default_renderer(self, view):
        return JSONRenderer()

class ValidateViewSet(ModelViewSet):
    
    queryset = ValidateFileUpload.objects.all()
    serializer_class = ValidateSerializer
    parser_classes = (MultiPartParser, FormParser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user,
                       file=self.request.data.get('file'))

class ConvertViewSet(ModelViewSet):
    
    queryset = ConvertFileUpload.objects.all()
    serializer_class = ConvertSerializer
    parser_classes = (MultiPartParser, FormParser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user,
                       file=self.request.data.get('file'),type=self.request.data.get('type'),result=self.request.data.get('result'))

class CompareViewSet(ModelViewSet):
    
    queryset = CompareFileUpload.objects.all()
    serializer_class = CompareSerializer
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
                    verifyclass.verify(settings.APP_DIR+uploaded_file_url)
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
            serial = ValidateSerializer2(instance=query)
            return Response(serial.data, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)
