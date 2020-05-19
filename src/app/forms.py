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

from django import forms
from django.contrib.auth.models import User
from django.contrib.admin import widgets

from app.models import UserID, LicenseNamespace, OrganisationName
from app.widgets import RelatedFieldWidgetCanAdd
from .constants import (FULL_NAME_HELP_TEXT, SHORT_IDENTIFIER_HELP_TEXT,
                        SOURCE_URL_HELP_TEXT, LICENSE_HEADER_INFO_HELP_TEXT,
                        COMMENTS_INFO_HELP_TEXT, LICENSE_TEXT_HELP_TEXT,
                        LIC_NS_SUB_FULLNAME_HELP_TEXT, LIC_NS_NSINFO_HELP_TEXT,
                        LIC_NS_NSID_HELP_TEXT, LIC_NS_URL_INFO_HELP_TEXT,
                        LIC_NS_LIC_LIST_URL_HELP_TEXT, LIC_NS_GH_REPO_URL_HELP_TEXT,
                        LIC_NS_ORG_HELP_TEXT, LIC_NS_DESC_HELP_TEXT)

OSI_CHOICES = (
    (0, "-"),
    ("Approved", "Approved"),
    ("Not Submitted", "Not Submitted"),
    ("Pending", "Submitted, but pending"),
    ("Rejected", "Rejected")
)

class UserRegisterForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    def clean_username(self):
        users = self.cleaned_data["username"]
        if User.objects.filter(username=users).count() > 0:
            raise forms.ValidationError("This username already exists.")
        return users
    def clean(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match.")
        return self.cleaned_data
    class Meta:
        model = User
        fields = ('first_name','last_name','email','username','password','confirm_password')

class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserID
        fields = ('organisation',)

class InfoForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name','last_name','email')

class OrgInfoForm(forms.ModelForm):

    class Meta:
        model = UserID
        fields = ('organisation',)

class LicenseRequestForm(forms.Form):

    def __init__(self, *args, **kwargs):
        if 'email' in kwargs:
            self.email = kwargs.pop('email')
        else:
            self.email = ""
        super(LicenseRequestForm, self).__init__(*args,**kwargs)
        self.fields["userEmail"] = forms.EmailField(label='Email', initial=self.email)

    licenseAuthorName = forms.CharField(label="License Author name", max_length=100, required=False)
    fullname = forms.CharField(label="Fullname", max_length=70, help_text=FULL_NAME_HELP_TEXT)
    shortIdentifier = forms.CharField(label='Short identifier', max_length=25, help_text=SHORT_IDENTIFIER_HELP_TEXT)
    sourceUrl = forms.CharField(label='Source / URL', required=False, help_text=SOURCE_URL_HELP_TEXT)
    osiApproved = forms.CharField(label="OSI Status", widget=forms.Select(choices=OSI_CHOICES))
    comments = forms.CharField(label='Comments', required=False, widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), help_text=COMMENTS_INFO_HELP_TEXT)
    licenseHeader = forms.CharField(label='Standard License Header', widget=forms.Textarea(attrs={'rows': 3, 'cols': 40}), required=False, help_text=LICENSE_HEADER_INFO_HELP_TEXT)
    text = forms.CharField(label='Text', widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), help_text=LICENSE_TEXT_HELP_TEXT)


class LicenseNamespaceRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if 'email' in kwargs:
            self.email = kwargs.pop('email')
        else:
            self.email = ""
        super(LicenseNamespaceRequestForm, self).__init__(*args, **kwargs)
        self.fields['shortIdentifier'].required = False
        self.fields['shortIdentifier'].help_text = LIC_NS_NSID_HELP_TEXT
        self.fields['namespace'].help_text = LIC_NS_NSINFO_HELP_TEXT
        self.fields['fullname'].help_text = LIC_NS_SUB_FULLNAME_HELP_TEXT
        self.fields['url'].required = True
        self.fields['url'].help_text = LIC_NS_URL_INFO_HELP_TEXT
        self.fields['description'].help_text = LIC_NS_DESC_HELP_TEXT
        self.fields['license_list_url'].required = False
        self.fields['license_list_url'].help_text = LIC_NS_LIC_LIST_URL_HELP_TEXT
        self.fields['github_repo_url'].required = False
        self.fields['github_repo_url'].help_text = LIC_NS_GH_REPO_URL_HELP_TEXT
        self.fields['organisation'].required = False
        self.fields["userEmail"] = forms.EmailField(label='Email', initial=self.email)

    organisation = forms.ModelChoiceField(
       required=False,
       queryset=OrganisationName.objects.all(),
       widget=RelatedFieldWidgetCanAdd(OrganisationName),
       help_text=LIC_NS_ORG_HELP_TEXT)

    class Meta:
        model = LicenseNamespace
        fields = ('organisation', 'licenseAuthorName',
                  'fullname', 'userEmail', 'url',
                  'license_list_url', 'github_repo_url',
                  'publiclyShared', 'namespace',
                  'description', 'archive', 'shortIdentifier')
