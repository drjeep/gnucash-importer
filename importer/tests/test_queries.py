import os
from django.conf import settings
from django.test import TestCase
from gnucash import Session
from .. import queries
from ..models import AccountMap


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
        root = self.session.book.get_root_account()
        self.assertEqual(len(queries.get_accounts(root)), 52)

    def test_get_account_ancestors(self):
        root = self.session.book.get_root_account()
        acc = root.lookup_by_name(settings.GNUCASH_BANK_ACCOUNT)
        self.assertEqual(len(queries.get_account_ancestors(acc)), 3)

    def test_get_customers(self):
        customers = queries.get_customers(self.session.book)
        self.assertEqual(len(customers), 1)

    def test_get_account_maps(self):
        self.assertEqual(
            queries.get_account_maps(),
            [("Telkom", "Phone", True), ("Vodacom", "Cellphone", False)],
        )

    def test_match_account(self):
        self.assertEqual(queries.match_account("1 Telkom Ltd"), ("Phone", True))

    def test_match_account_not_found(self):
        self.assertEqual(queries.match_account("Some other ref"), (None, False))

    def test_get_payment_refs(self):
        self.assertEqual(queries.get_payment_refs(self.session.book), {"00001"})
