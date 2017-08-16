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

from django.contrib.auth.models import User
from django.db import models

class ValidateFileUpload(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, to_field='id')
    file = models.FileField()
    result = models.CharField(max_length=128,null=False,blank=False)

class ConvertFileUpload(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, to_field='id')
    from_format = models.CharField(max_length=16,null=False,blank=False)
    to_format = models.CharField(max_length=16,null=False,blank=False)
    cfilename = models.CharField(max_length=32,null=False,blank=False)
    result = models.CharField(max_length=32,null=False,blank=False)
    file = models.FileField()

class CompareFileUpload(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, to_field='id')
    result = models.CharField(max_length=32,null=False,blank=False)
    file1 = models.FileField()
    file2 = models.FileField()
    rfilename = models.CharField(max_length=32,null=False,blank=False)
