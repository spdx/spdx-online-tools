# -*- coding: utf-8 -*-

# Copyright (c) 2017 Rohit Lodha
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import unicode_literals

from django.contrib.auth.models import User, Group
from rest_framework import serializers
from models import ValidateFileUpload,ConvertFileUpload,CompareFileUpload
 

class ValidateSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id'
    )
    class Meta:
        model = ValidateFileUpload
        fields = ('created', 'file', 'owner')

class ValidateSerializerReturn(serializers.ModelSerializer):
    class Meta:
        model = ValidateFileUpload
        fields = ('created', 'file', 'owner','result')

class ConvertSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id'
    )
    class Meta:
        model = ConvertFileUpload
        fields = ('created', 'file', 'owner','cfilename','from_format','to_format')

class ConvertSerializerReturn(serializers.ModelSerializer):
    class Meta:
        model = ConvertFileUpload
        fields = ('created', 'file', 'owner','result','from_format','to_format','cfilename','message')

class CompareSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id'
    )
    class Meta:
        model = CompareFileUpload
        fields = ('created', 'file1','file2', 'owner','rfilename')

class CompareSerializerReturn(serializers.ModelSerializer):
    class Meta:
        model = CompareFileUpload
        fields = ('created', 'file1','file2', 'owner','result','rfilename','message')
