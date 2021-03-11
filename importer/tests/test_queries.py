import os
from datetime import date
from decimal import Decimal
from django.conf import settings
from django.test import TestCase, override_settings
from gnucash import Session
from ..models import AccountMap
from .. import queries


@override_settings(GNUCASH_HISTORY_DAYS=3650)
class TestQueries(TestCase):
    def setUp(self):
        self.session = Session(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.gnucash")
        )

    @classmethod
    def setUpTestData(cls):
        AccountMap.objects.create(match="Telkom", account="Phone", vat_inclusive=True)
        AccountMap.objects.create(
            match="Vodacom", account="Cellphone", vat_inclusive=False
        )

    def tearDown(self):
        self.session.end()

    def test_get_accounts(self):
        self.assertEqual(
            len(queries.get_accounts(self.session.book.get_root_account())), 62
        )

    def test_get_account_ancestors(self):
        root = self.session.book.get_root_account()
        acc = root.lookup_by_name(settings.GNUCASH_BANK_ACCOUNT)
        self.assertEqual(len(queries.get_account_ancestors(acc)), 3)

    def test_get_customers(self):
        customers = queries.get_customers(self.session.book)
        self.assertEqual(len(customers), 2)

    def test_get_invoices(self):
        self.assertEqual(len(queries.get_invoices(self.session.book)), 3)

    def test_get_invoices_customer(self):
        customer = self.session.book.CustomerLookupByID("000001")
        self.assertEqual(len(queries.get_invoices(self.session.book, customer)), 2)

    def test_get_account_maps(self):
        self.assertEqual(
            queries.get_account_maps(),
            [("Telkom", "Phone", True), ("Vodacom", "Cellphone", False)],
        )

    def test_match_account(self):
        self.assertEqual(queries.match_account("1 Telkom Ltd"), ("Phone", True))

    def test_match_account_not_found(self):
        self.assertEqual(queries.match_account("not found"), (None, False))

    def test_match_customer_name(self):
        self.assertEqual(queries.match_customer(self.session.book, "Acme"), "000001")

    def test_match_customer_invoice(self):
        self.assertEqual(queries.match_customer(self.session.book, "00002"), "000001")

    def test_match_customer_not_found(self):
        self.assertEqual(queries.match_customer(self.session.book, "not found"), None)

    def test_get_payment_refs(self):
        self.assertEqual(queries.get_payment_refs(self.session.book), {"000001"})

    def test_get_duplicate_check_data(self):
        root = self.session.book.get_root_account()
        acc = root.lookup_by_name(settings.GNUCASH_BANK_ACCOUNT)
        self.assertEqual(
            queries.get_duplicate_check_data(acc),
            [[date(2019, 11, 21), Decimal("9.99")]],
        )
