from django.conf.urls import url
from .views import income, expenses

urlpatterns = [
    url(r"^$", expenses.upload, {}, "gnucash-import"),
    url(r"^fields/$", expenses.map_fields, {}, "gnucash-map-fields"),
    url(r"^accounts/$", expenses.map_accounts, {}, "gnucash-map-accounts"),
    url(r"^finish/$", expenses.finish, {}, "gnucash-finish"),
    url(r"^income/$", income.upload, {}, "income-import"),
    url(r"^income/fields/$", income.map_fields, {}, "income-map-fields"),
    url(r"^income/customers/$", income.map_customers, {}, "income-map-customers"),
    url(r"^income/finish/$", income.finish, {}, "income-finish"),
]
