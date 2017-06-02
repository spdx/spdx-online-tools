from django.conf.urls import patterns, url
from app import views
urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^validate/$', views.validate, name='index'),
	url(r'^about/$', views.about, name='about'),
	url(r'^convert/$', views.convert, name='convert'),
	url(r'^compare/$', views.compare, name='compare'),
	url(r'^search/$', views.search, name='search'),
	url(r'^login/$', views.login, name='login'),
]	
