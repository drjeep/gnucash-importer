import csv
import logging
from dateutil import parser
from decimal import Decimal
from django.conf import settings
from django.core.management.base import BaseCommand
from gnucash import Session
from importer.commands import pay_invoice
from importer.exceptions import PaymentExists

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import payments from CSV file"

    def handle(self, *args, **options):
        try:
            s = Session(settings.GNUCASH_FILE)
            book = s.book
            with open(args[0], "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    number = row["invoice"]
                    amount = Decimal(row["amount"])
                    date = parser.parse(row["date"])
                    try:
                        pay_invoice(book, number, amount, date)
                    except PaymentExists as e:
                        print("%s... skipping" % e)
            s.save()
        finally:
            s.end()
