import logging
import re
from datetime import datetime, date
from cache_memoize import cache_memoize
from django.conf import settings
from gnucash import Query
from gnucash.gnucash_business import Customer
from .convert import gnc_numeric_to_decimal
from .models import AccountMap

log = logging.getLogger(__name__)


def get_accounts(root, account_list=None):
    if account_list is None:
        account_list = []
    for account in root.get_children():
        if not account.get_children():
            account_list.append(account)
        get_accounts(account, account_list)
    return account_list


def get_account_ancestors(account, account_list=None):
    if account_list is None:
        account_list = []
    if not account.is_root():
        account_list.append(account)
        get_account_ancestors(account.get_parent(), account_list)
    return account_list


def get_customers(book):
    customers = []
    query = Query()
    query.set_book(book)
    query.search_for('gncCustomer')
    for result in query.run():
        customers.append(Customer(instance=result))
    query.destroy()
    return customers


def get_customer_invoice(customer):
    return None


@cache_memoize(60)
def get_account_maps():
    return list(AccountMap.objects.values_list("match", "account", "vat_inclusive"))


def match_account(value, amount=0):
    if value:
        lookup = []
        for match, account, vat_incl in get_account_maps():
            lookup.append((match, (account, vat_incl)))
        value = re.sub("\s\s+", " ", value).upper()
        for k, v in lookup:
            if k.upper() in value:
                log.debug("Matched %s to %s" % (value, v[0]))
                return v

    return None, False


@cache_memoize(60)
def get_payment_refs(book):
    refs = set()
    root = book.get_root_account()
    bank = root.lookup_by_name(settings.GNUCASH_BANK_ACCOUNT)
    for split in bank.GetSplitList():
        trans = split.parent
        ref = trans.GetNum()
        if ref:
            refs.add(ref)
    return refs


def get_duplicate_check_data(account):
    check = []
    for split in account.GetSplitList():
        trans = split.parent
        try:
            dte = datetime.fromtimestamp(trans.GetDate())
        except TypeError:
            dte = trans.GetDate()
        amt = gnc_numeric_to_decimal(split.GetAmount())
        if dte.year > date.today().year - 2:
            check.append([dte, amt])
    return check
