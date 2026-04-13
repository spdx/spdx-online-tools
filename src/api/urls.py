# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2017 Rohit Lodha
# Copyright (c) 2017 Rohit Lodha
# SPDX-License-Identifier: Apache-2.0

from django.urls import path

from api import views

urlpatterns = [
    path('validate/', views.validate, name='validate-api'),
    path('convert/', views.convert, name='convert-api'),
    path('compare/', views.compare, name='compare-api'),
    path('check_license/', views.check_license, name='check_license-api'),
    path('submit_license/', views.submit_license, name='submit_license-api'),
]
