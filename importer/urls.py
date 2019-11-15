from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.upload, {}, "gnucash-import"),
    url(r"^fields/$", views.map_fields, {}, "gnucash-map-fields"),
    url(r"^accounts/$", views.map_accounts, {}, "gnucash-map-accounts"),
    url(r"^finish/$", views.finish, {}, "gnucash-finish"),
]
