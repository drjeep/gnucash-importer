import os
from django.conf import settings
from django.test import TestCase
from gnucash import Session
from .. import queries


class TestQueries(TestCase):
    def setUp(self):
        self.session = Session(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.gnucash")
        )

    def tearDown(self):
        self.session.end()

    def test_get_accounts(self):
        root = self.session.book.get_root_account()
        print([acc.name for acc in queries.get_accounts(root)])

    def test_get_account_ancestors(self):
        root = self.session.book.get_root_account()
        acc = root.lookup_by_name(settings.GNUCASH_BANK_ACCOUNT)
        print([acc.name for acc in queries.get_account_ancestors(acc)])

    def test_get_account_maps(self):
        pass

    def test_match_account(self):
        pass

    def test_get_invoice_numbers(self):
        pass
