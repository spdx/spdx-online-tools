# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models

class ValidateFileUpload(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, to_field='id')
    file = models.FileField()

class ConvertFileUpload(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, to_field='id')
    type = models.CharField(max_length=16,null=False,blank=False)
    result = models.CharField(max_length=32,null=False,blank=False)
    file = models.FileField()

class CompareFileUpload(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, to_field='id')
    result = models.CharField(max_length=32,null=False,blank=False)
    file1 = models.FileField()
    file2 = models.FileField()