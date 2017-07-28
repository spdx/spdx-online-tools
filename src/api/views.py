# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from serializers import UserSerializer, GroupSerializer
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    
    
class FileUploadView(APIView):
    parser_classes = (FileUploadParser, )

    def post(self, request, format='jpg'):
        up_file = request.FILES['file']
        destination = open(up_file.name,'wb+')
        for chunk in up_file.chunks():
            destination.write(chunk)
            destination.close()

        # ...
        # do some stuff with uploaded file
        # ...
        return Response(up_file.name, status.HTTP_201_CREATED)
