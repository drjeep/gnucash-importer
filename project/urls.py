from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.http import HttpResponse

urlpatterns = [
    url(r"^", include("importer.urls")),
    url(r"^health/$", lambda x: HttpResponse()),
    url(r"^admin/", include(admin.site.urls)),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [url(r"^__debug__/", include(debug_toolbar.urls))] + urlpatterns
