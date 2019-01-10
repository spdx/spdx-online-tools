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

from app.models import UserID

OSI_CHOICES = (
    (0, "-"),
    ("yes", "Yes"),
    ("no", "No"),
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
    fullname = forms.CharField(label='Fullname', max_length=70)
    shortIdentifier = forms.CharField(label='Short identifier', max_length=25)
    sourceUrl = forms.CharField(label='Source / URL', required=False)
    osiApproved = forms.CharField(label="OSI Approved", widget=forms.Select(choices=OSI_CHOICES))
    notes = forms.CharField(label='Notes', widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), required=False)
    licenseHeader = forms.CharField(label='Standard License Header', widget=forms.Textarea(attrs={'rows': 3, 'cols': 40}), required=False)
    text = forms.CharField(label='Text', widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}))
    userEmail = forms.EmailField(label='Email', max_length=35)
