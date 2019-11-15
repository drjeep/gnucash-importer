import os
from ..utils import create_split_transaction
from datetime import date
from decimal import Decimal
from django.conf import settings
from gnucash import Session

session = Session(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.gnucash")
)

try:
    create_split_transaction(
        session.book,
        settings.GNUCASH_BANK_ACCOUNT,
        "Internet",
        date.today(),
        "ADSL",
        Decimal("539.00"),
    )
    create_split_transaction(
        session.book,
        settings.GNUCASH_BANK_ACCOUNT,
        "Internet",
        date.today(),
        "ADSL (no VAT)",
        Decimal("539.00"),
        vat_incl=False,
    )
    # session.save()

finally:
    session.end()
