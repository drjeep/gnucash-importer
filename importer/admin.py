from django.contrib import admin
from .forms import AccountMapForm
from .models import AccountMap


@admin.register(AccountMap)
class AccountMapAdmin(admin.ModelAdmin):
    form = AccountMapForm
    list_display = ('match', 'account', 'vat_inclusive', 'created', 'modified')
    list_filter = ('vat_inclusive',)
