from django.conf.urls import patterns, url
from ssms import views
urlpatterns = [
	url(r'^$', views.index, name='index'),
]	
