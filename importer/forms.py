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
def account_choices(book=None):
    choices = [("", "---------")]
    if not book:
        session = Session(settings.GNUCASH_FILE)
        book = session.book
    for ac in queries.get_accounts(book.get_root_account()):
        choices.append((ac.name, ac.name))
    if "session" in locals():
        session.end()
    return choices


@cache_memoize(60)
def customer_choices(book=None):
    choices = [("", "---------")]
    if not book:
        session = Session(settings.GNUCASH_FILE)
        book = session.book
    for c in queries.get_customers(book):
        choices.append((c.GetID(), c.GetName()))
    if "session" in locals():
        session.end()
    return choices


class PaymentDateField(forms.Field):
    def to_python(self, value):
        try:
            return parser.parse(value).date()
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
    account = forms.ChoiceField(choices=())
    amount = forms.DecimalField(widget=forms.HiddenInput)
    date = PaymentDateField(widget=forms.HiddenInput)
    description = forms.CharField(widget=forms.HiddenInput)
    vat_incl = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        book = kwargs.pop("book", None)
        super(AccountForm, self).__init__(*args, **kwargs)
        self.fields["account"].choices = account_choices(book)


class CustomerForm(forms.Form):
    customer = forms.ChoiceField(choices=())
    amount = forms.DecimalField(widget=forms.HiddenInput)
    date = PaymentDateField(widget=forms.HiddenInput)
    description = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        book = kwargs.pop("book", None)
        super(CustomerForm, self).__init__(*args, **kwargs)
        self.fields["customer"].choices = customer_choices(book)


class AccountMapForm(forms.ModelForm):
    account = forms.ChoiceField(choices=account_choices())

    class Meta:
        model = AccountMap
        fields = ("match", "account", "vat_inclusive")
