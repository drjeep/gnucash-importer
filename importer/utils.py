import logging
import re
from decimal import Decimal
from django.conf import settings
from gnucash import Account, GncNumeric, Transaction, Split

log = logging.getLogger(__name__)


def gnc_numeric_from_decimal(decimal_value):
    sign, digits, exponent = decimal_value.as_tuple()

    # convert decimal digits to a fractional numerator
    # equivlent to
    # numerator = int(''.join(digits))
    # but without the wated conversion to string and back,
    # this is probably the same algorithm int() uses
    numerator = 0
    TEN = int(Decimal(0).radix())  # this is always 10
    numerator_place_value = 1
    # add each digit to the final value multiplied by the place value
    # from least significant to most sigificant
    for i in range(len(digits) - 1, -1, -1):
        numerator += digits[i] * numerator_place_value
        numerator_place_value *= TEN

    if decimal_value.is_signed():
        numerator = -numerator

    # if the exponent is negative, we use it to set the denominator
    if exponent < 0:
        denominator = TEN ** (-exponent)
    # if the exponent isn't negative, we bump up the numerator
    # and set the denominator to 1
    else:
        numerator *= TEN ** exponent
        denominator = 1

    return GncNumeric(numerator, denominator)


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
            amount - (amount / Decimal(settings.GNUCASH_VAT_RATE)).quantize(Decimal("0.01"))
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


def match_account(value, amount=0):
    if value:
        if value.startswith("SARS TAX PAYMENT") and Decimal(amount) < Decimal(
            "-15000.00"
        ):
            log.debug("Matched %s to %s" % (value, "PAYE"))
            return "PAYE", False
        elif value.startswith("SARS TAX PAYMENT") and Decimal(amount) > Decimal(
            "-2000.00"
        ):
            log.debug("Matched %s to %s" % (value, "VAT Payments"))
            return "VAT Payments", False
        elif Decimal(amount) in (Decimal("-1.1"), Decimal("-1.11")):
            log.debug("Matched %s to %s" % (value, "Bank Service Charge"))
            return "Bank Service Charge", True

        lookup = (
            # bank account
            ("sB AUTOPAY 5221", ("Credit Card", False)),
            ("STANDARD BANK CARD", ("Credit Card", False)),
            ("ACC 270784500", ("Bank Service Charge", True)),
            ("FOREX", ("Bank Service Charge", False)),
            ("SALARY", ("Salaries", False)),
            ("AFRIHOST", ("Internet", True)),
            ("MULTID FORHETZNER", ("Equipment Rental", True)),
            ("CELL C", ("Cell Phone", True)),
            ("CELLC", ("Cell Phone", True)),
            ("CELC PREPD", ("Cell Phone", True)),
            ("TELKOM", ("Phone", True)),
            ("FRONTOSA", ("Computers", True)),
            ("FIRST TECHNOLOGY", ("Computers", True)),
            ("MIRO DIST", ("Computers", True)),
            ("AC VENTER", ("Accounting", True)),
            ("COFFEE ROASTING", ("Office Supplies", True)),
            ("SB MERCH", ("Bank Service Charge", True)),
            ("DHL INTERNATIONAL", ("Postage and Delivery", False)),
            ("FEDEX", ("Postage and Delivery", False)),
            ("VIRTUALSTOCK", ("Virtualstock", False)),
            ("SARS-ITA-ASSESED 999598805", ("Business ITA", False)),
            ("SARS-PROV-PROVII 999598805", ("Business PROV", False)),
            ("SARS-STC-SECONDA 999598805", ("Business STC", False)),
            ("DIRECTORS LOAN", ("Director's Loan", False)),
            ("LUNO 262804033", ("Cryptocurrency", False)),
            # credit card
            ("Opensrs", ("Domain Registration", False)),
            ("europeregistry.com", ("Domain Registration", False)),
            ("Za Central Registry", ("Domain Registration", True)),
            ("Amazon Web Services", ("Amazon AWS", False)),
            ("Softlayer", ("Equipment Rental", False)),
            ("Easynews", ("Dues and Subscriptions", False)),
            ("Netflix", ("Dues and Subscriptions", False)),
            ("Showmax", ("Dues and Subscriptions", False)),
            ("Google Music", ("Dues and Subscriptions", False)),
            ("Msft", ("Dues and Subscriptions", False)),
            ("Steam", ("Software", False)),
            ("Service Fee", ("Bank Service Charge", True)),
            ("Intern.atm", ("Bank Service Charge", False)),
            ("Cash Finance Charge", ("Bank Service Charge", False)),
            ("Intellect", ("Office Supplies", True)),
            ("Takealot", ("Books", True)),
            ("Kindle", ("Books", False)),
            ("Registry.net.za", ("Domain Registration", True)),
            ("Accessusa Shipping", ("Postage and Delivery", False)),
            ("Banggood", ("Low Value Assets", False)),
            ("aliexpress.com", ("Low Value Assets", False)),
            ("Gearbest", ("Low Value Assets", False)),
            ("Travelex", ("Travel and Accommodation", False)),
            ("Rs Components", ("Low Value Assets", True)),
            ("firsttech.co.za", ("Low Value Assets", True)),
            ("hponline.co.za", ("Low Value Assets", True)),
            ("Flying Robot", ("Low Value Assets", True)),
            ("Hobby Mani", ("Low Value Assets", True)),
            ("rclipocoza", ("Low Value Assets", False)),
            ("Geewiz", ("Low Value Assets", True)),
            ("3d Printing Store", ("Office Supplies", True)),
            ("Intl. Trans Fee", ("Bank Service Charge", False)),
        )
        value = re.sub("\s\s+", " ", value).upper()
        for k, v in lookup:
            #            log.debug([value, k])
            if k.upper() in value:
                log.debug("Matched %s to %s" % (value, v[0]))
                return v

        return None, False
