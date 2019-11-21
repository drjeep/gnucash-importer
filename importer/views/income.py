import csv
import logging
from io import TextIOWrapper
from gnucash import Session
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from importer.forms import IncomeUploadForm, IncomeFieldForm, CustomerForm
from importer import commands, queries

log = logging.getLogger(__name__)


def upload(request):
    if request.method == "POST":
        form = IncomeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = TextIOWrapper(request.FILES["upload"], encoding="utf8")
            dialect = csv.Sniffer().sniff(f.read())
            f.seek(0)
            reader = csv.reader(f, dialect)
            rows = []
            for row in reader:
                rows.append(row)
            request.session["rows"] = rows

            return HttpResponseRedirect(reverse("income-map-fields"))
    else:
        form = IncomeUploadForm()

    return render(request, "importer/upload.html", {"form": form})


def map_fields(request):
    rows = request.session.get("rows", [])

    IncomeFieldFormSet = formset_factory(IncomeFieldForm, extra=len(rows[0]))

    if request.method == "POST":
        formset = IncomeFieldFormSet(request.POST)
        if formset.is_valid():
            map = {}
            for i, form in enumerate(formset.forms):
                field = form.cleaned_data.get("field")
                if field:
                    map[i] = field

            if not all(
                [
                    "customer" in map.values(),
                    "amount" in map.values(),
                    "date" in map.values(),
                ]
            ):
                messages.error(
                    request, "Please select customer, amount and date fields"
                )
                return HttpResponseRedirect(reverse("income-map-fields"))

            request.session["map"] = map
            return HttpResponseRedirect(reverse("income-map-customers"))
    else:
        formset = IncomeFieldFormSet()

    return render(
        request, "importer/map-fields.html", {"formset": formset, "rows": rows[:10]}
    )


def map_customers(request):
    rows = request.session.get("rows", [])
    map = request.session.get("map", {})

    data = []
    for row in rows:
        new_row = {}
        for index, field in map.items():
            new_row[field] = row[int(index)]
        if not new_row["amount"].startswith("-"):
            data.append(new_row)

    CustomerFormSet = formset_factory(CustomerForm, extra=0)

    session = Session(settings.GNUCASH_FILE)
    bank = queries.get_bank_account(session.book)

    if request.method == "POST":
        formset = CustomerFormSet(request.POST)

        check = queries.get_duplicate_check_data(bank)

        try:
            ok = dup = 0
            for form in formset.forms:
                if form.is_valid():
                    clean = form.cleaned_data
                    if [clean["date"], clean["amount"]] not in check:
                        commands.apply_payment(
                            clean["customer"], clean["amount"], clean["date"]
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

        return HttpResponseRedirect(reverse("income-finish"))
    else:
        initial = []
        for row in data:
            customer = queries.match_customer(session.book, row.get("customer"))
            initial.append(
                {
                    "customer": customer,
                    "amount": row.get("amount"),
                    "date": row.get("date"),
                    "description": row.get("account"),
                }
            )
        formset = CustomerFormSet(initial=initial)

    return render(
        request,
        "importer/map-customers.html",
        {
            "formset": formset,
            "rows": zip(data, formset.forms),
            "gnucash": settings.GNUCASH_FILE,
        },
    )


def finish(request):
    del request.session["rows"]
    del request.session["map"]

    return render(request, "importer/finish.html")
