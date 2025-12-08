# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2017 Rohit Lodha
# Copyright (c) 2017 Rohit Lodha
# SPDX-License-Identifier: Apache-2.0

from rest_framework import serializers

from api.models import ValidateFileUpload, ConvertFileUpload, CompareFileUpload, SubmitLicenseModel
 

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


class CheckLicenseSerializer(serializers.Serializer):
    """POST validate API request fields"""
    file = serializers.FileField()

    class Meta:
        fields = ('file', )


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
