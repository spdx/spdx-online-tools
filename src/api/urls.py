# SPDX-FileCopyrightText: 2017 Rohit Lodha
# SPDX-FileCopyrightText: 2026-present SPDX Contributors
# SPDX-License-Identifier: Apache-2.0

from django.urls import path

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from api import views

urlpatterns = [
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('validate/', views.validate, name='validate-api'),
    path('convert/', views.convert, name='convert-api'),
    path('compare/', views.compare, name='compare-api'),
    path('check_license/', views.check_license, name='check_license-api'),
    path('submit_license/', views.submit_license, name='submit_license-api'),
]
