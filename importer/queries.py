import logging
import re
from cache_memoize import cache_memoize
from datetime import date
from django.conf import settings
from fuzzywuzzy import fuzz
from gnucash import Query, QOF_QUERY_AND
from gnucash.gnucash_business import Customer, Invoice
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


def get_bank_account(book):
    root = book.get_root_account()
    return root.lookup_by_name(settings.GNUCASH_BANK_ACCOUNT)


def get_accounts_receivable(book):
    root = book.get_root_account()
    return root.lookup_by_name(settings.GNUCASH_ACCOUNTS_RECEIVABLE)


def get_customers(book):
    customers = []
    query = Query()
    query.set_book(book)
    query.search_for("gncCustomer")
    for result in query.run():
        customers.append(Customer(instance=result))
    query.destroy()
    return customers


def get_invoices(book, customer=None):
    invoices = []
    query = Query()
    query.set_book(book)
    query.search_for("gncInvoice")
    if customer:
        query.add_guid_match(["owner", "guid"], customer.GetGUID(), QOF_QUERY_AND)
    for result in query.run():
        invoices.append(Invoice(instance=result))
    return invoices


@cache_memoize(60)
def get_account_maps():
    return list(AccountMap.objects.values_list("match", "account", "vat_inclusive"))


def match_account(value, amount=None):
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


def match_customer(book, value):
    """
    @todo: match invoice numbers
    @todo: highlight score > 50
    @todo: optimize!
    """
    if value:
        s1 = value.upper()
        for customer in get_customers(book):
            s2 = customer.GetName()
            score = fuzz.partial_ratio(s1, s2.upper())
            if score > 80:
                log.debug("Matched customer %s to %s... %d" % (s1, s2.upper(), score))
                return customer.GetID()

            for invoice in get_invoices(book, customer):
                s2 = invoice.GetID()
                score = fuzz.partial_ratio(s1, s2.upper())
                if score > 80:
                    log.debug(
                        "Matched invoice %s to %s... %d" % (s1, s2.upper(), score)
                    )
                    return invoice.GetOwner().GetID()

    return None


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


@cache_memoize(60)
def get_duplicate_check_data(account):
    check = []
    for split in account.GetSplitList():
        trans = split.parent
        dte = trans.GetDate()
        amt = gnc_numeric_to_decimal(split.GetAmount())
        if dte.year > date.today().year - 2:
            check.append([dte, amt])
    return check
