import csv
from dateutil import parser
from decimal import Decimal
from django.core.management.base import BaseCommand
from gnucash import Session, GncNumeric
from importer.utils import gnc_numeric_from_decimal


class Command(BaseCommand):
    help = "Import payments from CSV file"

    def handle(self, *args, **options):
        try:
            s = Session("_docs/gnucash/wickedbox.gnc")

            book = s.book
            root = book.get_root_account()
            bank = root.lookup_by_name("Checking Account")

            # load payment numbers
            refs = set()
            for split in bank.GetSplitList():
                trans = split.parent
                ref = trans.GetNum()
                if ref:
                    refs.add(ref)

            f = open(args[0], "r")
            reader = csv.DictReader(f)

            for row in reader:
                invoice = book.InvoiceLookupByID(row["invoice"])
                if not invoice:
                    raise Exception(
                        "Could not find invoice %s... aborting" % row["invoice"]
                    )

                number = row["number"]
                if number in refs:
                    print("Payment %s already exists... skipping" % number)
                else:
                    customer = invoice.GetOwner()
                    posted_acc = invoice.GetPostedAcc()
                    xfer_acc = root.lookup_by_name("Checking Account")
                    amount = gnc_numeric_from_decimal(Decimal(row["amount"]))
                    date = parser.parse(row["date"])

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

            s.save()

        except Exception:
            raise

        finally:
            s.end()
