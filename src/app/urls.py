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

from django.conf.urls import url,handler400, handler403, handler404, handler500

from app import views
#from django.contrib.auth import views as auth_views


handler400 = 'views.handler400'
handler403 = 'views.handler403'
handler404 = 'views.handler404'
handler500 = 'views.handler500'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^validate/$', views.validate, name='validate'),
    url(r'^about/$', views.about, name='about'),
    url(r'^convert/$', views.convert, name='convert'),
    url(r'^compare/$', views.compare, name='compare'),
    url(r'^check_license/$', views.check_license, name='check-license'),
    url(r'^login/$', views.loginuser, name='login'),
    url(r'^register/$', views.register, name='register'),
    url(r'^logout/$', views.logoutuser, name='logout'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^checkusername/$', views.checkusername, name='check-username'),
    url(r'^xml_upload/$',views.xml_upload, name='xml-upload'),
    url(r'^edit/(?P<page_id>[0-9a-z]+)/$', views.xml_edit, name='editor'),
    url(r'^edit_license_xml/(?P<license_id>[0-9]+)/$', views.edit_license_xml, name='license_xml_editor'),
    url(r'^edit_license_xml/$', views.edit_license_xml, name='license_xml_editor_none'),
    url(r'^validate_xml/$', views.validate_xml, name='validate-xml'),
    url(r'^search/$',views.autocompleteModel, name='autocompleteModel'),
    url(r'^make_pr/$', views.pull_request, name='pull-request'),
    url(r'^update_session/$',views.update_session_variables, name='update-session-variables'),
    url(r'^submit_new_license/$', views.submitNewLicense, name='submit-new-license'),
    url(r'^license_requests/$', views.licenseRequests, name='license-requests'),
    url(r'^license_requests/(?P<licenseId>\d+)/$', views.licenseInformation, name='license-information'),
    #url(r'^password_reset/$', auth_views.password_reset, name='password_reset'),
    #url(r'^password_reset/done/$', auth_views.password_reset_done, name='password_reset_done'),
    #url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
    #    auth_views.password_reset_confirm, name='password_reset_confirm'),
    #url(r'^reset/done/$', auth_views.password_reset_complete, name='password_reset_complete'),
]
