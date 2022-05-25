# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2017 Rohit Lodha
# Copyright (c) 2017 Rohit Lodha
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.contrib.auth.models import User
from django.db import models
from time import time

OSI_CHOICES = (
    (0, "-"),
    ("Approved", "Approved"),
    ("Not Submitted", "Not Submitted"),
    ("Pending", "Submitted, but pending"),
    ("Rejected", "Rejected"),
    ("Unknown", "Don't know")
)

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<username>/<filename>
    return 'apifiles/{0}/{1}/{2}'.format(instance.owner.username, int(time()), filename)

class ValidateFileUpload(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path)
    result = models.CharField(max_length=128,null=False,blank=False)
    status = models.IntegerField(default=200,blank=False)

class ConvertFileUpload(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE)
    from_format = models.CharField(max_length=16,null=False,blank=False)
    to_format = models.CharField(max_length=16,null=False,blank=False)
    tagToRdfFormat = models.CharField(max_length=16,null=True,blank=True)
    cfilename = models.CharField(max_length=32,null=False,blank=False)
    result = models.CharField(max_length=32,null=False,blank=False)
    message = models.CharField(max_length=64,null=False,blank=False)
    file = models.FileField(upload_to=user_directory_path)
    status = models.IntegerField(default=200,blank=False)

class CompareFileUpload(models.Model):
    
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE)
    result = models.CharField(max_length=32,null=False,blank=False)
    message = models.CharField(max_length=64,null=False,blank=False)
    file1 = models.FileField(upload_to=user_directory_path)
    file2 = models.FileField(upload_to=user_directory_path)
    rfilename = models.CharField(max_length=32,null=False,blank=False)
    status = models.IntegerField(default=200,blank=False)

class CheckLicenseFileUpload(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path)
    result = models.CharField(max_length=128,null=False,blank=False)
    status = models.IntegerField(default=200,blank=False)

class SubmitLicenseModel(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, to_field='id', on_delete=models.CASCADE)
    licenseAuthorName = models.CharField(max_length=100, default="", blank=True, null=True)
    fullname = models.CharField(max_length=70)
    shortIdentifier = models.CharField(max_length=25)
    userEmail = models.EmailField(max_length=35)
    #notes = models.CharField(max_length=255, default="")
    result = models.CharField(max_length=128, blank=True, null=True)
    status = models.IntegerField(default=200,  blank=False)
    sourceUrl = models.CharField(max_length=255, default="", blank=True, null=True)
    osiApproved = models.CharField(max_length=15, choices=OSI_CHOICES, default=0)
    comments = models.TextField(default="", blank=True, null=True)
    licenseHeader = models.CharField(max_length=25, default="", blank=True, null=True)
    text = models.TextField(default="")
    xml = models.TextField(default="")
