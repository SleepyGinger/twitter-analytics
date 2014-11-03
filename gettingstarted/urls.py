from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

import hello.views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'gettingstarted.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', hello.views.index, name='index'),
    url(r'^analyze', hello.views.analyze, name='analyze'),
    url(r'date_graph', hello.views.date_graph, name='date_graph'),
    url(r'^admin/', include(admin.site.urls)),
)
