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

from django.urls import path, re_path
from django.conf.urls import handler400, handler403, handler404, handler500

from app import views
#from django.contrib.auth import views as auth_views


handler400 = 'views.handler400'
handler403 = 'views.handler403'
handler404 = 'views.handler404'
handler500 = 'views.handler500'

urlpatterns = [
    path('', views.index, name='index'),
    path('validate/', views.validate, name='validate'),
    path('about/', views.about, name='about'),
    path('convert/', views.convert, name='convert'),
    path('compare/', views.compare, name='compare'),
    path('check_license/', views.check_license, name='check-license'),
    path('login/', views.loginuser, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logoutuser, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('checkusername/', views.checkusername, name='check-username'),
    path('xml_upload/',views.xml_upload, name='xml-upload'),
    re_path(r'^edit/(?P<page_id>[0-9a-z]+)/$', views.xml_edit, name='editor'),
    path('validate_xml/', views.validate_xml, name='validate-xml'),
    path('search/',views.autocompleteModel, name='autocompleteModel'),
    path('make_pr/', views.pull_request, name='pull-request'),
    path('update_session/',views.update_session_variables, name='update-session-variables'),
    path('submit_new_license/', views.submitNewLicense, name='submit-new-license'),
    path('license_requests/', views.licenseRequests, name='license-requests'),
    re_path(r'^license_requests/(?P<licenseId>\d+)/$', views.licenseInformation, name='license-information'),
    # path('password_reset/', auth_views.password_reset, name='password_reset'),
    # path('password_reset/done/', auth_views.password_reset_done, name='password_reset_done'),
    # re_path(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
    #    auth_views.password_reset_confirm, name='password_reset_confirm'),
    # path('reset/done/', auth_views.password_reset_complete, name='password_reset_complete'),
]
