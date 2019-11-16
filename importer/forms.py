from dateutil import parser
from django import forms
from django.conf import settings
from django.core.cache import cache
from gnucash import Session
from .models import AccountMap
from .queries import get_accounts

FIELD_CHOICES = (
    ("", "---------"),
    ("account", "Account"),
    ("amount", "Amount"),
    ("date", "Date"),
)

STATEMENT_CHOICES = (("bank", "Bank"), ("card", "Credit Card"))


def account_choices():
    if "account_choices" in cache:
        choices = cache.get("account_choices")
    else:
        choices = [("", "---------")]
        session = Session(settings.GNUCASH_FILE)
        root = session.book.get_root_account()
        for ac in get_accounts(root):
            choices.append((ac.name, ac.name))
        session.end()
        session.destroy()

        cache.set("account_choices", choices, 30)

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


class FieldForm(forms.Form):
    field = forms.ChoiceField(choices=FIELD_CHOICES)


class AccountForm(forms.Form):
    account = forms.ChoiceField(choices=account_choices())
    amount = forms.DecimalField(widget=forms.HiddenInput)
    date = PaymentDateField(widget=forms.HiddenInput)
    description = forms.CharField(widget=forms.HiddenInput)
    vat_incl = forms.BooleanField(required=False)


class AccountMapForm(forms.ModelForm):
    account = forms.ChoiceField(choices=account_choices())

    class Meta:
        model = AccountMap
        fields = ('match', 'account')
