import os
from django.conf import settings
from ..utils import get_accounts, get_account_ancestors
from gnucash import Session

session = Session(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.gnucash")
)

try:
    book = session.book
    root = book.get_root_account()
    print([acc.name for acc in get_accounts(root)])

    acc = root.lookup_by_name(settings.GNUCASH_BANK_ACCOUNT)
    print([acc.name for acc in get_account_ancestors(acc)])

finally:
    session.end()
