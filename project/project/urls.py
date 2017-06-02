from django.conf.urls import include, url,patterns
from django.contrib import admin
from django.views.generic import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [
    # Examples:
    # url(r'^$', 'project.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
		url(r'^(/)?$', RedirectView.as_view(url='/app/')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^app/', include('app.urls')),
]

urlpatterns += staticfiles_urlpatterns()
