import logging
from decimal import Decimal
from django.conf import settings
from gnucash import Transaction, Split, GncNumeric
from .queries import get_invoice_numbers
from .convert import gnc_numeric_from_decimal

log = logging.getLogger(__name__)


def create_split_transaction(
    book, bank_acc_name, exp_acc_name, trans_date, description, amount, vat_incl=True
):
    """
    @todo: more generic handling of assets/income/expenses/liabilities
    """
    root = book.get_root_account()
    comm_table = book.get_table()
    currency = comm_table.lookup("CURRENCY", settings.GNUCASH_CURRENCY)

    bank_acc = root.lookup_by_name(bank_acc_name)
    exp_acc = root.lookup_by_name(exp_acc_name)
    if vat_incl:
        vat_acc = root.lookup_by_name(settings.GNUCASH_VAT_ACCOUNT)

    trans1 = Transaction(book)
    trans1.BeginEdit()

    num1 = gnc_numeric_from_decimal(amount)  # total
    if vat_incl:
        num2 = gnc_numeric_from_decimal(
            (amount / Decimal(settings.GNUCASH_VAT_RATE)).quantize(Decimal("0.01"))
        )  # subtotal
        num3 = gnc_numeric_from_decimal(
            amount
            - (amount / Decimal(settings.GNUCASH_VAT_RATE)).quantize(Decimal("0.01"))
        )  # vat
    else:
        num2 = num1  # total

    if bank_acc_name == settings.GNUCASH_CARD_ACCOUNT:
        num1 = num1.neg()
        num2 = num2.neg()
        try:
            num3 = num3.neg()
        except NameError:
            pass

    split1 = Split(book)
    split1.SetAccount(exp_acc)
    split1.SetParent(trans1)
    split1.SetValue(num2.neg())

    if vat_incl:
        split2 = Split(book)
        split2.SetAccount(vat_acc)
        split2.SetParent(trans1)
        split2.SetValue(num3.neg())

    split3 = Split(book)
    split3.SetAccount(bank_acc)
    split3.SetParent(trans1)
    split3.SetValue(num1)

    trans1.SetCurrency(currency)
    trans1.SetDate(trans_date.day, trans_date.month, trans_date.year)
    trans1.SetDescription(description)

    trans1.CommitEdit()


def pay_invoice(book, number, amount, date):
    root = book.get_root_account()
    invoice = book.InvoiceLookupByID(number)
    if not invoice:
        raise Exception("Could not find invoice %s... aborting" % number)

    if number in get_invoice_numbers(book):
        print("Payment %s already exists... skipping" % number)
    else:
        customer = invoice.GetOwner()
        posted_acc = invoice.GetPostedAcc()
        xfer_acc = root.lookup_by_name(settings.GNUCASH_BANK_ACCOUNT)
        amount = gnc_numeric_from_decimal(amount)

        customer.ApplyPayment(
            None,
            None,
            posted_acc,
            xfer_acc,
            amount,
            GncNumeric(1),
            date,
            "",
            number,
            True,
        )
