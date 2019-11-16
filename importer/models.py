from django.db import models


class AccountMap(models.Model):
    match = models.CharField(max_length=255)
    account = models.CharField(max_length=255)
    vat_inclusive = models.BooleanField('VAT inclusive', default=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
