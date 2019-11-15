import os
import datetime
from decimal import Decimal
from gnucash import Session, GncNumeric
from ..utils import gnc_numeric_from_decimal

session = Session(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.gnucash")
)

try:
    book = session.book
    root = book.get_root_account()

    invoice = book.InvoiceLookupByID("002310")
    customer = invoice.GetOwner()
    posted_acc = invoice.GetPostedAcc()
    xfer_acc = root.lookup_by_name("Checking Account")
    amount = gnc_numeric_from_decimal(Decimal("149.00"))

    customer.ApplyPayment(
        None,
        invoice,
        posted_acc,
        xfer_acc,
        amount,
        GncNumeric(1),
        datetime.date.today(),
        "",
        "",
        True,
    )
    # session.save()
finally:
    session.end()
