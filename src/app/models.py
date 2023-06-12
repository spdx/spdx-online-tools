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

from django.db import models
from datetime import datetime
from django import forms
from django.contrib.auth.models import User

class UserID(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.CharField("Organisation",max_length=64, null=False, blank=False)
    lastlogin = models.DateField("Last Login",default=datetime.now,blank=True)
    def __str__(self):
        return self.user.username

class LicenseNames(models.Model):
    name = models.CharField(max_length=200)

class License(models.Model):
    licenseAuthorName = models.CharField(max_length=100, default="", blank=True, null=True)
    fullname = models.CharField(max_length=70)
    shortIdentifier = models.CharField(max_length=25)
    submissionDatetime = models.DateTimeField(auto_now_add=True)
    userEmail = models.EmailField(max_length=35)
    notes = models.CharField(max_length=255, default="")
    xml = models.TextField()
    archive = models.BooleanField(default=False)

    class Meta:
        abstract = True

class LicenseRequest(License):
    issueId = models.TextField(default='')

    def __unicode__(self):
        return "%s" % (self.fullname)
    def __str__(self):
        return "%s" % (self.fullname)

    class Meta:
        verbose_name = "LicenseRequest"
        verbose_name_plural = "LicenseRequests"


class OrganisationName(models.Model):
    name = models.CharField(max_length=250)
    orgId = models.CharField(max_length=25)

    def __unicode__(self):
        return "%s" % (self.name)

    def __str__(self):
        return "{0} [{1}]".format(self.name, self.orgId)

    class Meta:
        verbose_name = "OrganisationName"
        verbose_name_plural = "OrganisationNames"


class LicenseNamespace(License):
    organisation = models.ForeignKey(OrganisationName, null=True, blank=True, on_delete=models.CASCADE)
    publiclyShared = models.BooleanField(default=True)
    description = models.TextField()
    namespace = models.CharField(max_length=200)
    url = models.CharField(max_length=200)
    license_list_url= models.URLField(max_length=250)
    github_repo_url= models.URLField(max_length=250)
    promoted = models.BooleanField(default=False)
    license_request = models.ForeignKey(LicenseRequest, null=True, blank=True, on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s" % (self.namespace)

    def __str__(self):
        return "%s" % (self.namespace)

    class Meta:
        verbose_name = "LicenseNamespace"
        verbose_name_plural = "LicenseNamespaces"
