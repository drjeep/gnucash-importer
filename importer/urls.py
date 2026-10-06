from django.urls import path
from .views import income, expenses

urlpatterns = [
    path("expenses/", expenses.upload, name="expenses-import"),
    path("expenses/fields/", expenses.map_fields, name="expenses-map-fields"),
    path("expenses/accounts/", expenses.map_accounts, name="expenses-map-accounts"),
    path("expenses/finish/", expenses.finish, name="expenses-finish"),
    path("income/", income.upload, name="income-import"),
    path("income/fields/", income.map_fields, name="income-map-fields"),
    path("income/customers/", income.map_customers, name="income-map-customers"),
    path("income/finish/", income.finish, name="income-finish"),
]
