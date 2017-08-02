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
from serializers import ValidateSerializer,ConvertSerializer,CompareSerializer


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