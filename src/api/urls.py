# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2017 Rohit Lodha
# Copyright (c) 2017 Rohit Lodha
# SPDX-License-Identifier: Apache-2.0

from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from api import views

schema_view = get_schema_view(
   openapi.Info(
      title="API docs",
      default_version='v1',
      description="SPDX API API",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path('validate/', views.validate, name='validate-api'),
    path('convert/', views.convert, name='convert-api'),
    path('compare/', views.compare, name='compare-api'),
    path('check_license/', views.check_license, name='check_license-api'),
    path('submit_license/', views.submit_license, name='submit_license-api'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui')
]
