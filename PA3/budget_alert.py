"""budget_alert: write a Markdown report of over-budget expense categories.

Usage:
    python budget_alert.py --expenses expenses.csv --budgets budgets.json --out alert.md

See SPEC.md for the full behavior contract.
"""

import argparse
import csv
import io
import json
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

# Plain non-negative/negative decimal: digits, optional fractional part. ASCII digits only.
AMOUNT_RE = re.compile(r"-?[0-9]+(\.[0-9]+)?")
CENT = Decimal("0.01")


class FatalError(Exception):
    """Input problem that stops the run; no report is written."""


class _Pairs(list):
    """Marks a JSON object parsed via object_pairs_hook (keeps duplicate keys)."""


_INVALID = object()  # stands in for NaN / Infinity / -Infinity from JSON


def warn(message):
    print(f"warning: {message}", file=sys.stderr)


def normalize(name):
    return name.strip().lower()


def parse_amount_text(text):
    """Classify a trimmed amount string: ('ok', Decimal) | ('invalid', None) | ('negative', None)."""
    if not AMOUNT_RE.fullmatch(text):
        return "invalid", None
    if text.startswith("-"):
        return "negative", None
    return "ok", Decimal(text)


def fmt(value):
    """Round half-up to 2 decimals for display; never show -0.00."""
    q = value.quantize(CENT, rounding=ROUND_HALF_UP)
    if q == 0:
        q = abs(q)
    return f"{q:.2f}"


def read_text(path, label):
    try:
        return Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise FatalError(f"cannot read {label} file '{path}': {exc}") from None


def load_budgets(path):
    """Return {normalized_name: (display_name, limit)}."""
    text = read_text(path, "budgets")
    try:
        data = json.loads(
            text,
            parse_float=Decimal,
            parse_int=Decimal,
            parse_constant=lambda _: _INVALID,
            object_pairs_hook=_Pairs,
        )
    except json.JSONDecodeError as exc:
        raise FatalError(f"budgets file '{path}' is not valid JSON: {exc}") from None

    if not isinstance(data, _Pairs):
        raise FatalError(f"budgets file '{path}' must be a JSON object")

    # Fatal checks first, so nothing is warned about when the file is rejected.
    seen = {}
    for key, value in data:
        if isinstance(value, list):  # nested object (_Pairs) or array
            raise FatalError(f"budgets file '{path}' must be flat; key \"{key}\" has a nested value")
        norm = normalize(key)
        if not norm:
            continue
        if norm in seen:
            raise FatalError(
                f"budgets file '{path}' has duplicate category \"{seen[norm]}\" and \"{key}\""
            )
        seen[norm] = key

    budgets = {}
    for key, value in data:
        norm = normalize(key)
        if not norm:
            warn("skipping budget with empty category name")
            continue
        if isinstance(value, Decimal):
            if value.is_signed():
                warn(f"skipping budget \"{key}\": negative value")
                continue
            limit = value
        elif isinstance(value, str):
            status, limit = parse_amount_text(value.strip())
            if status != "ok":
                warn(f"skipping budget \"{key}\": {'negative' if status == 'negative' else 'non-numeric'} value")
                continue
        else:  # bool, null, NaN/Infinity
            warn(f"skipping budget \"{key}\": non-numeric value")
            continue
        budgets[norm] = (key.strip(), limit)
    return budgets


def load_expenses(path, budgets):
    """Return (spent, skipped): spent is {normalized_name: Decimal}, skipped is a list of reasons."""
    text = read_text(path, "expenses")
    spent = {}
    skipped = []
    if not text.strip():
        return spent, skipped

    try:
        records = list(csv.reader(io.StringIO(text, newline="")))
    except csv.Error as exc:
        raise FatalError(f"expenses file '{path}' is not valid CSV: {exc}") from None

    header = [normalize(name) for name in records[0]]
    columns = {}
    for required in ("category", "amount"):
        count = header.count(required)
        if count == 0:
            raise FatalError(f"expenses file '{path}' is missing required column '{required}'")
        if count > 1:
            raise FatalError(f"expenses file '{path}' has duplicate column '{required}'")
        columns[required] = header.index(required)

    def field(record, name):
        index = columns[name]
        return record[index].strip() if index < len(record) else ""

    for row_num, record in enumerate(records[1:], start=2):
        if not record:  # completely blank line
            continue
        category = field(record, "category")
        amount_text = field(record, "amount")
        if not category:
            skipped.append(f"Row {row_num}: missing category")
            continue
        if not amount_text:
            skipped.append(f"Row {row_num}: missing amount")
            continue
        status, amount = parse_amount_text(amount_text)
        if status == "invalid":
            skipped.append(f'Row {row_num}: invalid amount "{amount_text}"')
            continue
        if status == "negative":
            skipped.append(f'Row {row_num}: negative amount "{amount_text}"')
            continue
        norm = normalize(category)
        if norm not in budgets:
            skipped.append(f'Row {row_num}: no budget for category "{category}"')
            continue
        spent[norm] = spent.get(norm, Decimal(0)) + amount
    return spent, skipped


def render(budgets, spent, skipped):
    names = sorted(spent)
    lines = ["# Budget Alert Report", "", "## Over Budget", ""]

    over = [n for n in names if spent[n] > budgets[n][1]]
    if over:
        for n in over:
            display, limit = budgets[n]
            lines.append(
                f"- **{display}**: spent {fmt(spent[n])} of {fmt(limit)} (over by {fmt(spent[n] - limit)})"
            )
    else:
        lines.append("None.")

    lines += ["", "## Summary", ""]
    if names:
        lines.append("| Category | Budget | Spent | Remaining | Status |")
        lines.append("|----------|-------:|------:|----------:|--------|")
        total_budget = total_spent = Decimal(0)
        for n in names:
            display, limit = budgets[n]
            status = "OVER" if spent[n] > limit else "OK"
            cell = display.replace("|", "\\|")
            lines.append(
                f"| {cell} | {fmt(limit)} | {fmt(spent[n])} | {fmt(limit - spent[n])} | {status} |"
            )
            total_budget += limit
            total_spent += spent[n]
        lines.append(
            f"| **Total** | {fmt(total_budget)} | {fmt(total_spent)} | {fmt(total_budget - total_spent)} | |"
        )
    else:
        lines.append("None.")

    lines += ["", "## Skipped Rows", ""]
    lines += [f"- {reason}" for reason in skipped] or ["None."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Write a Markdown report of over-budget categories.")
    parser.add_argument("--expenses", required=True, help="path to expenses CSV")
    parser.add_argument("--budgets", required=True, help="path to budgets JSON")
    parser.add_argument("--out", required=True, help="path to write the Markdown report")
    args = parser.parse_args(argv)

    try:
        budgets = load_budgets(args.budgets)
        spent, skipped = load_expenses(args.expenses, budgets)
        report = render(budgets, spent, skipped)
        try:
            with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(report)
        except OSError as exc:
            raise FatalError(f"cannot write output file '{args.out}': {exc}") from None
    except FatalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
