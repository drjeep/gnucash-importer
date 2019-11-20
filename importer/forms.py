from cache_memoize import cache_memoize
from dateutil import parser
from django import forms
from django.conf import settings
from gnucash import Session
from .models import AccountMap
from . import queries

FIELD_CHOICES = (
    ("", "---------"),
    ("account", "Account"),
    ("amount", "Amount"),
    ("date", "Date"),
)

INCOME_FIELD_CHOICES = (
    ("", "---------"),
    ("customer", "Customer"),
    ("amount", "Amount"),
    ("date", "Date"),
)

STATEMENT_CHOICES = (("bank", "Bank"), ("card", "Credit Card"))


@cache_memoize(60)
def account_choices():
    choices = [("", "---------")]
    session = Session(settings.GNUCASH_FILE)
    for ac in queries.get_accounts(session.book.get_root_account()):
        choices.append((ac.name, ac.name))
    session.end()

    return choices


@cache_memoize(60)
def customer_choices():
    choices = [("", "---------")]
    session = Session(settings.GNUCASH_FILE)
    for c in queries.get_customers(session.book):
        choices.append((c.GetID(), c.GetName()))
    session.end()

    return choices


class PaymentDateField(forms.Field):
    def to_python(self, value):
        try:
            return parser.parse(value)
        except ValueError as e:
            raise forms.ValidationError(e)


class UploadForm(forms.Form):
    statement = forms.ChoiceField(choices=STATEMENT_CHOICES)
    upload = forms.FileField()


class IncomeUploadForm(forms.Form):
    upload = forms.FileField()


class FieldForm(forms.Form):
    field = forms.ChoiceField(choices=FIELD_CHOICES)


class IncomeFieldForm(forms.Form):
    field = forms.ChoiceField(choices=INCOME_FIELD_CHOICES)


class AccountForm(forms.Form):
    account = forms.ChoiceField(choices=account_choices())
    amount = forms.DecimalField(widget=forms.HiddenInput)
    date = PaymentDateField(widget=forms.HiddenInput)
    description = forms.CharField(widget=forms.HiddenInput)
    vat_incl = forms.BooleanField(required=False)


class CustomerForm(forms.Form):
    customer = forms.ChoiceField(choices=customer_choices())
    amount = forms.DecimalField(widget=forms.HiddenInput)
    date = PaymentDateField(widget=forms.HiddenInput)
    description = forms.CharField(widget=forms.HiddenInput)


class AccountMapForm(forms.ModelForm):
    account = forms.ChoiceField(choices=account_choices())

    class Meta:
        model = AccountMap
        fields = ("match", "account", "vat_inclusive")
