from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

urlpatterns = [
    path("", include("importer.urls")),
    path("health/", lambda x: HttpResponse()),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns = debug_toolbar_urls() + urlpatterns
