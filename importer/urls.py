from django.conf.urls import url
from .views import income, expenses

urlpatterns = [
    url(r"^$", expenses.upload, {}, "gnucash-import"),
    url(r"^fields/$", expenses.map_fields, {}, "gnucash-map-fields"),
    url(r"^accounts/$", expenses.map_accounts, {}, "gnucash-map-accounts"),
    url(r"^finish/$", expenses.finish, {}, "gnucash-finish"),
]
