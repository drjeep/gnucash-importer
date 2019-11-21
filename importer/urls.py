from django.conf.urls import url
from .views import income, expenses

urlpatterns = [
    url(r"^expenses/$", expenses.upload, {}, "expenses-import"),
    url(r"^expenses/fields/$", expenses.map_fields, {}, "expenses-map-fields"),
    url(r"^expenses/accounts/$", expenses.map_accounts, {}, "expenses-map-accounts"),
    url(r"^expenses/finish/$", expenses.finish, {}, "expenses-finish"),
    url(r"^income/$", income.upload, {}, "income-import"),
    url(r"^income/fields/$", income.map_fields, {}, "income-map-fields"),
    url(r"^income/customers/$", income.map_customers, {}, "income-map-customers"),
    url(r"^income/finish/$", income.finish, {}, "income-finish"),
]
