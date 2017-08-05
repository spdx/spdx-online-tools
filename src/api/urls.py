from __future__ import unicode_literals

from django.conf.urls import url

from api import views

urlpatterns = [
    #url(r'^imageupload/$', views.FileUploadView.as_view(), name='image'),
    url(r'^validate/$', views.validate, name='validate-api'),
    url(r'^convert/$', views.convert, name='convert-api'),
    #url(r'^convert/$', views.ConvertViewSet.as_view({'get': 'perform_create'}), name='file'),
]
