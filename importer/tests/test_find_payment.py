import os
from gnucash import Session

session = Session(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.gnucash")
)

try:
    book = session.book
    root = book.get_root_account()
    bank = root.lookup_by_name("Checking Account")
    for split in bank.GetSplitList():
        trans = split.parent
        ref = trans.GetNum()
        if ref:
            print(trans.GetNum())
finally:
    session.end()
