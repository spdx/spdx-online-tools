from __future__ import unicode_literals

from django.conf.urls import url

from api import views

urlpatterns = [
    url(r'^imageupload/$', views.FileUploadView.as_view(), name='image'),
    url(r'^fileupload/$', views.FileUploadViewSet.as_view({'get': 'perform_create'}), name='file'),
]
