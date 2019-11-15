import csv
import logging
from io import TextIOWrapper
from datetime import datetime
from decimal import Decimal
from gnucash import Session
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from .forms import UploadForm, FieldForm, AccountForm
from .utils import create_split_transaction, match_account

log = logging.getLogger(__name__)


def upload(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = TextIOWrapper(request.FILES["upload"], encoding="utf8")
            dialect = csv.Sniffer().sniff(f.read())
            f.seek(0)
            reader = csv.reader(f, dialect)
            rows = []
            for row in reader:
                rows.append(row)
            request.session["rows"] = rows
            request.session["statement"] = form.cleaned_data["statement"]

            return HttpResponseRedirect(reverse("gnucash-map-fields"))
    else:
        form = UploadForm()

    return render(request, "importer/upload.html", {"form": form})


def map_fields(request):
    rows = request.session.get("rows", [])

    FieldFormSet = formset_factory(FieldForm, extra=len(rows[0]))

    if request.method == "POST":
        formset = FieldFormSet(request.POST)
        if formset.is_valid():
            map = {}
            for i, form in enumerate(formset.forms):
                field = form.cleaned_data.get("field")
                if field:
                    map[i] = field
            request.session["map"] = map

            return HttpResponseRedirect(reverse("gnucash-map-accounts"))
    else:
        formset = FieldFormSet()

    return render(
        request, "importer/map-fields.html", {"formset": formset, "rows": rows[:10]}
    )


def map_accounts(request):
    rows = request.session.get("rows", [])
    map = request.session.get("map", {})
    statement = request.session.get("statement", "bank")
    if statement == "bank":
        bank_account = settings.GNUCASH_BANK_ACCOUNT
    else:
        bank_account = settings.GNUCASH_CARD_ACCOUNT

    data = []
    for row in rows:
        new_row = {}
        for index, field in map.items():
            new_row[field] = row[int(index)]
        # @todo: split into debit/credit views
        if statement == "card" or (
            new_row["amount"].startswith("-") or "VIRTUALSTOCK" in new_row["account"]
        ):
            data.append(new_row)
    #    log.debug(data)

    AccountFormSet = formset_factory(AccountForm, extra=0)

    if request.method == "POST":
        formset = AccountFormSet(request.POST)

        session = Session(settings.GNUCASH_FILE)
        root = session.book.get_root_account()
        if statement == "bank":
            bank = root.lookup_by_name(settings.GNUCASH_BANK_ACCOUNT)
        else:
            bank = root.lookup_by_name(settings.GNUCASH_CARD_ACCOUNT)

        check = []
        for split in bank.GetSplitList():
            trans = split.parent
            dte = datetime.fromtimestamp(trans.GetDate())
            amt = Decimal(str(split.GetAmount()))
            if statement == "card":
                amt = -amt
            if dte.year > 2011:
                check.append([dte, amt])
        log.debug(check)

        try:
            ok = dup = 0
            for form in formset.forms:
                if form.is_valid():
                    clean = form.cleaned_data
                    log.debug(clean)
                    if [clean["date"], clean["amount"]] not in check:
                        create_split_transaction(
                            session.book,
                            bank_account,
                            str(clean["account"]),
                            clean["date"],
                            str(clean["description"]),
                            clean["amount"],
                            vat_incl=clean["vat_incl"],
                        )
                        ok += 1
                    else:
                        messages.warning(
                            request,
                            "Skipped %s %s %s"
                            % (
                                clean["date"].strftime("%Y-%m-%d"),
                                clean["description"],
                                clean["amount"],
                            ),
                        )
                        dup += 1

            session.save()
            messages.info(request, "Successfully imported %s transactions" % ok)
            if dup:
                messages.warning(request, "Skipped %s duplicate transactions" % dup)

        except Exception as e:
            messages.error(request, e)

        finally:
            session.end()

    #        return HttpResponseRedirect(reverse('gnucash-finish'))
    else:
        initial = []
        for row in data:
            log.debug(row)
            account, vat_incl = match_account(row.get("account"), row.get("amount", 0))
            #            log.debug([account, vat_incl])
            initial.append(
                {
                    "account": account,
                    "amount": row.get("amount"),
                    "date": row.get("date"),
                    "description": row.get("account"),
                    "vat_incl": vat_incl,
                }
            )
        formset = AccountFormSet(initial=initial)

    return render(
        request,
        "importer/map-accounts.html",
        {
            "formset": formset,
            "rows": zip(data, formset.forms),
            "gnucash": settings.GNUCASH_FILE,
        },
    )


def finish(request):
    del request.session["rows"]
    del request.session["map"]

    return render(request, "gnucash/finish.html")
