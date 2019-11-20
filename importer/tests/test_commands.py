import os
from datetime import date
from decimal import Decimal
from django.conf import settings
from django.test import TestCase
from gnucash import Session
from ..exceptions import PaymentExists
from .. import commands


class TestCommands(TestCase):
    def setUp(self):
        self.session = Session(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.gnucash")
        )

    def tearDown(self):
        self.session.end()

    def test_create_split_transaction_vat(self):
        commands.create_split_transaction(
            self.session.book,
            settings.GNUCASH_BANK_ACCOUNT,
            "Internet",
            date.today(),
            "ADSL",
            Decimal("539.00"),
        )

    def test_create_split_transaction_novat(self):
        commands.create_split_transaction(
            self.session.book,
            settings.GNUCASH_BANK_ACCOUNT,
            "Internet",
            date.today(),
            "ADSL",
            Decimal("539.00"),
        )

    def test_pay_invoice(self):
        commands.pay_invoice(
            self.session.book, "00002", Decimal("999.99"), date.today()
        )

    def test_pay_invoice_exists(self):
        self.assertRaises(
            PaymentExists,
            commands.pay_invoice,
            self.session.book,
            "00001",
            Decimal("9999.99"),
            date.today(),
        )

    # def test_apply_payment(self):
    #     commands.apply_payment(
    #         self.session.book, "00001", Decimal("999.99"), date.today()
    #     )
