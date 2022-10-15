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

from django.urls import path, re_path
from django.conf.urls import url,handler400, handler403, handler404, handler500
from django.views.decorators.csrf import csrf_exempt

from app import views
#from django.contrib.auth import views as auth_views

handler400 = 'app.views.handler400'
handler403 = 'app.views.handler403'
handler404 = 'app.views.handler404'
handler500 = 'app.views.handler500'

urlpatterns = [
    path('', views.index, name='index'),
    path('validate/', views.validate, name='validate'),
    path('ntia_checker/', views.ntia_check, name='ntia_checker'),
    path('about/', views.about, name='about'),
    path('convert/', views.convert, name='convert'),
    path('compare/', views.compare, name='compare'),
    path('check_license/', views.check_license, name='check-license'),
    path('diff/', views.license_diff, name='license-diff'),
    path('login/', views.loginuser, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logoutuser, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('checkusername/', views.checkusername, name='check-username'),
    path('xml_upload/',views.xml_upload, name='xml-upload'),
    re_path(r'^edit/(?P<page_id>[0-9a-z]+)/$', views.license_xml_edit, name='editor'),
    re_path(r'^edit_license_xml/(?P<license_id>[0-9]+)/$', views.edit_license_xml, name='license_xml_editor'),
    path('edit_license_xml/', views.edit_license_xml, name='license_xml_editor_none'),
    path('validate_xml/', views.validate_xml, name='validate-xml'),
    path('search/',views.autocompleteModel, name='autocompleteModel'),
    path('make_issue/', views.issue, name='issue'),
    path('make_pr/', views.pull_request, name='pull-request'),
    path('beautify/', views.beautify, name='beautify'),
    path('update_session/',views.update_session_variables, name='update-session-variables'),
    path('submit_new_license/', views.submitNewLicense, name='submit-new-license'),
    path('submit_new_license_namespace/', views.submitNewLicenseNamespace, name='submit-new-license-namespace'),
    path('license_requests/', views.licenseRequests, name='license-requests'),
    re_path(r'^license_requests/(?P<licenseId>\d+)/$', views.licenseInformation, name='license-information'),
    path('archive_requests/', views.archiveRequests, name='archive-license-xml'),
    re_path(r'^archive_requests/(?P<licenseId>\d+)/$', views.licenseInformation, name='archived-license-information'),
    path('license_namespace_requests/', views.licenseNamespaceRequests, name='license-namespace-requests'),
    re_path(r'^license_namespace_requests/(?P<licenseId>\d+)/$', views.licenseNamespaceInformation, name='license-namespace-information'),
    path('archive_namespace_requests/', views.archiveNamespaceRequests, name='archive-license-namespace-xml'),
    re_path(r'^archive_namespace_requests/(?P<licenseId>\d+)/$', views.licenseNamespaceInformation, name='archived-license-namespace-information'),
    re_path(r'^edit_license_namespace_xml/(?P<license_id>[0-9]+)/$', views.edit_license_namespace_xml, name='license_namespace_xml_editor'),
    path('edit_license_namespace_xml/', views.edit_license_namespace_xml, name='license_namespace_xml_editor_none'),
    path('make_namespace_pr/', views.namespace_pull_request, name='namespace-pull-request'),
    path('promoted_namespace_requests/', views.promoteNamespaceRequests, name='promoted-license-namespace-xml'),
    re_path(r'^promoted_namespace_requests/(?P<licenseId>\d+)/$', views.licenseNamespaceInformation, name='promoted-license-namespace-information'),
    path('post_to_github/', csrf_exempt(views.post_to_github), name='post_to_github'),
    # path('password_reset/', auth_views.password_reset, name='password_reset'),
    # path('password_reset/done/', auth_views.password_reset_done, name='password_reset_done'),
    # re_path(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
    #    auth_views.password_reset_confirm, name='password_reset_confirm'),
    # path('reset/done/', auth_views.password_reset_complete, name='password_reset_complete'),
]
