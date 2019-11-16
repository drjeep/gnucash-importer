import logging
import re
from gnucash import Account
from .models import AccountMap

log = logging.getLogger(__name__)


def get_accounts(root, account_list=[]):
    for account in root.get_children():
        if type(account) != Account:
            account = Account(instance=account)
        if not account.get_children():
            account_list.append(account)
        get_accounts(account, account_list)
    return account_list


def get_account_ancestors(account, account_list=[]):
    if not account.is_root():
        account_list.append(account)
        get_account_ancestors(account.get_parent(), account_list)
    return account_list


def get_account_maps():
    return AccountMap.objects.values_list('match', 'account', 'vat_inclusive')


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
