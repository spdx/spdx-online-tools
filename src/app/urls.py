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

handler404 = 'views.handler404'
handler403 = 'views.handler403'
handler500 = 'views.handler500'
handler400 = 'views.handler400'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^validate/$', views.validate, name='index'),
    url(r'^about/$', views.about, name='about'),
    url(r'^convert/$', views.convert, name='convert'),
    url(r'^compare/$', views.compare, name='compare'),
    url(r'^check_license/$', views.check_license, name='check license'),
    url(r'^login/$', views.loginuser, name='login'),
    url(r'^register/$', views.register, name='register'),
    url(r'^logout/$', views.logoutuser, name='logout'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^password_reset/$', views.password_reset, name='password_reset'),
]