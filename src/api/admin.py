# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2017 Rohit Lodha
# Copyright (c) 2017 Rohit Lodha
# SPDX-License-Identifier: Apache-2.0

from django.contrib import admin

from api.models import ValidateFileUpload,ConvertFileUpload,CompareFileUpload,SubmitLicenseModel


admin.site.register(ValidateFileUpload)
admin.site.register(CompareFileUpload)
admin.site.register(ConvertFileUpload)
admin.site.register(SubmitLicenseModel)
