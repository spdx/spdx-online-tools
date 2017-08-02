from __future__ import unicode_literals

from django.conf.urls import url

from api import views

urlpatterns = [
    #url(r'^imageupload/$', views.FileUploadView.as_view(), name='image'),
    #url(r'^validate/$', views.ValidateViewSet.as_view({'get': 'perform_create'}), name='file'),
    #url(r'^convert/$', views.ConvertViewSet.as_view({'get': 'perform_create'}), name='file'),
]
