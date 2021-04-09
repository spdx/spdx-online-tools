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



from django.contrib.auth.models import User, Group          

from rest_framework import serializers

from api.models import ValidateFileUpload,ConvertFileUpload,CompareFileUpload,CheckLicenseFileUpload,SubmitLicenseModel
 

class ValidateSerializer(serializers.HyperlinkedModelSerializer):
    """POST validate API request fields"""
    owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id'
    )
    class Meta:
        model = ValidateFileUpload
        fields = ('created', 'file', 'owner')

class ValidateSerializerReturn(serializers.ModelSerializer):
    """Response Fields to be returned to the user"""
    class Meta:
        model = ValidateFileUpload
        fields = ('created', 'file', 'owner','result','status')

class ConvertSerializer(serializers.HyperlinkedModelSerializer):
    """POST convert API request fields"""
    owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id'
    )
    class Meta:
        model = ConvertFileUpload
        fields = ('created', 'file', 'owner','cfilename','from_format','to_format','tagToRdfFormat')

class ConvertSerializerReturn(serializers.ModelSerializer):
    """Response Fields to be returned to the user"""
    class Meta:
        model = ConvertFileUpload
        fields = ('created', 'file', 'owner','result','from_format','to_format','tagToRdfFormat','cfilename','message','status')

class CompareSerializer(serializers.HyperlinkedModelSerializer):
    """POST compare API request fields"""
    owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id'
    )
    class Meta:
        model = CompareFileUpload
        fields = ('created', 'file1','file2', 'owner','rfilename')

class CompareSerializerReturn(serializers.ModelSerializer):
    """Response Fields to be returned to the user"""
    class Meta:
        model = CompareFileUpload
        fields = ('created', 'file1','file2', 'owner','result','rfilename','message','status')

class CheckLicenseSerializer(serializers.HyperlinkedModelSerializer):
    """POST validate API request fields"""
    owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id'
    )
    class Meta:
        model = CheckLicenseFileUpload
        fields = ('created', 'file', 'owner')

class CheckLicenseSerializerReturn(serializers.ModelSerializer):
    """Response Fields to be returned to the user"""
    class Meta:
        model = CheckLicenseFileUpload
        fields = ('created', 'file', 'owner','result','status')

class SubmitLicenseSerializer(serializers.HyperlinkedModelSerializer):
    """POST license submit API request fields"""
    owner = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id'
    )
    class Meta:
        model = SubmitLicenseModel
        fields = ('created','owner','fullname','shortIdentifier','licenseAuthorName','userEmail','sourceUrl','osiApproved','comments','licenseHeader','text','result','status')

class SubmitLicenseSerializerReturn(serializers.ModelSerializer):
    """Response Fields to be returned to the user"""
    class Meta:
        model = SubmitLicenseModel
        fields = ('created','owner','result','status')
