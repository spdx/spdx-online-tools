# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2017 Rohit Lodha
# Copyright (c) 2017 Rohit Lodha
# SPDX-License-Identifier: Apache-2.0

from django.contrib import admin

from app.models import UserID
from app.models import LicenseRequest, OrganisationName, LicenseNamespace

admin.site.register(UserID)
admin.site.register(LicenseRequest)
admin.site.register(OrganisationName)
admin.site.register(LicenseNamespace)
