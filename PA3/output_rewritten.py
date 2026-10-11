import argparse
import csv
import json
import sys
from pathlib import Path

CSV_PATH = Path(__file__).parent / "expenses.csv"
REPORT_PATH = Path(__file__).parent / "report.txt"

DEFAULT_BUDGETS = {
    "food": 200,
    "transport": 100,
    "entertainment": 150,
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the expense summarizer.

    Returns:
        The parsed arguments, with ``csv`` set to the expenses CSV path and
        ``budgets`` set to a budgets JSON path or None.

    Raises:
        SystemExit: If the arguments are invalid or ``--help`` is passed.
    """
    parser = argparse.ArgumentParser(description="Summarize expenses against a budget.")
    parser.add_argument(
        "--csv",
        default=str(CSV_PATH),
        help="Path to the expenses CSV file (default: %(default)s)",
    )
    parser.add_argument(
        "--budgets",
        default=None,
        help="Path to a JSON file of budget limits (default: built-in budgets)",
    )
    return parser.parse_args()


def load_budgets(budgets_path: str | None) -> dict[str, float]:
    """Load budget limits from a JSON file, falling back to the defaults.

    If the file is missing or contains invalid JSON, an error is printed to
    stderr and the default budgets are returned.

    Args:
        budgets_path: Path to a JSON file mapping category names to budget
            limits, or None to use the built-in defaults.

    Returns:
        A mapping of category name to budget limit.
    """
    if budgets_path is None:
        return DEFAULT_BUDGETS

    try:
        with open(budgets_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: budgets file not found: {budgets_path}", file=sys.stderr)
        return DEFAULT_BUDGETS
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in budgets file {budgets_path}: {e}", file=sys.stderr)
        return DEFAULT_BUDGETS


def _parse_row(
    row: dict[str, str | None], line_num: int, budgets: dict[str, float]
) -> tuple[tuple[str, float] | None, str | None]:
    """Validate and parse a single CSV row into a category and amount.

    Args:
        row: The CSV row as a mapping of column name to value.
        line_num: The line number of the row in the CSV file, used in
            error messages.
        budgets: A mapping of known category names to budget limits; rows
            with categories not in this mapping are rejected.

    Returns:
        A tuple of ``(parsed, reason)``. On success, ``parsed`` is a
        ``(category, amount)`` tuple and ``reason`` is None. On failure,
        ``parsed`` is None and ``reason`` describes why the row was skipped.
    """
    date = row.get("date")
    category = row.get("category")
    amount_raw = row.get("amount")

    if date is None or category is None or amount_raw is None:
        return None, f"Line {line_num}: row has missing columns"

    category = category.strip()
    amount_raw = amount_raw.strip()

    if not category or not amount_raw:
        return None, f"Line {line_num}: missing category or amount"

    try:
        amount = float(amount_raw)
    except ValueError:
        return None, f"Line {line_num}: invalid amount '{amount_raw}'"

    if amount < 0:
        return None, f"Line {line_num}: negative amount ({amount:.2f}) is suspicious"

    if category not in budgets:
        return None, f"Line {line_num}: unrecognized category '{category}' (no budget defined)"

    return (category, amount), None


def load_expenses(
    csv_path: str | Path, budgets: dict[str, float] | None = None
) -> tuple[list[tuple[str, float]], list[str]]:
    """Load and validate expense rows from a CSV file.

    Invalid rows are skipped and their reasons are printed to stderr. If the
    file is missing or has no header row, an error is printed and empty
    lists are returned.

    Args:
        csv_path: Path to the expenses CSV file.
        budgets: A mapping of known category names to budget limits, used to
            reject unrecognized categories. Defaults to the built-in budgets.

    Returns:
        A tuple of ``(rows, skipped_reasons)``, where ``rows`` is a list of
        valid ``(category, amount)`` tuples and ``skipped_reasons`` is a
        list of messages describing each skipped row.
    """
    if budgets is None:
        budgets = DEFAULT_BUDGETS

    rows = []
    skipped_reasons = []

    try:
        f = open(csv_path, newline="", encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        return rows, skipped_reasons

    with f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            print("Error: CSV file has no header row", file=sys.stderr)
            return rows, skipped_reasons

        for line_num, row in enumerate(reader, start=2):  # header is line 1
            parsed, reason = _parse_row(row, line_num, budgets)
            if parsed is None:
                print(reason, file=sys.stderr)
                skipped_reasons.append(reason)
                continue
            rows.append(parsed)

    return rows, skipped_reasons


def calculate_totals(rows: list[tuple[str, float]]) -> dict[str, float]:
    """Sum expense amounts by category.

    Args:
        rows: A list of ``(category, amount)`` tuples.

    Returns:
        A mapping of category name to total amount spent.
    """
    totals = {}
    for category, amount in rows:
        totals[category] = totals.get(category, 0.0) + amount
    return totals


def build_summary_lines(totals: dict[str, float]) -> list[str]:
    """Build the formatted lines of the expense summary table.

    Categories are listed in descending order of total spent, followed by a
    grand total.

    Args:
        totals: A mapping of category name to total amount spent.

    Returns:
        The summary table as a list of lines, or a single "No expenses
        found." line if ``totals`` is empty.
    """
    if not totals:
        return ["No expenses found."]

    grand_total = sum(totals.values())
    name_width = max(len(cat) for cat in totals) + 2

    lines = ["Expense Summary", "-" * (name_width + 12)]

    for category, total in sorted(totals.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"{category:<{name_width}}${total:>10.2f}")

    lines.append("-" * (name_width + 12))
    lines.append(f"{'Total':<{name_width}}${grand_total:>10.2f}")
    return lines


def check_budgets(
    totals: dict[str, float], budgets: dict[str, float]
) -> list[tuple[str, float, bool]]:
    """Compare category totals against their budget limits.

    Categories without a budget are ignored.

    Args:
        totals: A mapping of category name to total amount spent.
        budgets: A mapping of category name to budget limit.

    Returns:
        A list of ``(category, remaining, over_budget)`` tuples, where
        ``remaining`` is the budget minus the amount spent and
        ``over_budget`` is True if ``remaining`` is negative.
    """
    status = []
    for category, spent in totals.items():
        if category not in budgets:
            continue
        remaining = budgets[category] - spent
        status.append((category, remaining, remaining < 0))
    return status


def build_budget_lines(totals: dict[str, float], budgets: dict[str, float]) -> list[str]:
    """Build the formatted lines of the budget status table.

    Args:
        totals: A mapping of category name to total amount spent.
        budgets: A mapping of category name to budget limit.

    Returns:
        The budget status table as a list of lines, showing the amount
        remaining or over budget for each budgeted category, or an empty
        list if no spent category has a budget.
    """
    status = check_budgets(totals, budgets)
    if not status:
        return []

    name_width = max(len(category) for category, _, _ in status) + 2

    lines = ["Budget Status", "-" * (name_width + 12)]

    for category, remaining, over_budget in status:
        if over_budget:
            lines.append(f"{category:<{name_width}}${-remaining:>10.2f} OVER BUDGET")
        else:
            lines.append(f"{category:<{name_width}}${remaining:>10.2f} remaining")

    return lines


def print_summary(totals: dict[str, float]) -> None:
    """Print the expense summary table to stdout.

    Args:
        totals: A mapping of category name to total amount spent.
    """
    for line in build_summary_lines(totals):
        print(line)


def print_budget_status(totals: dict[str, float], budgets: dict[str, float]) -> None:
    """Print the budget status table to stdout, preceded by a blank line.

    Nothing is printed if no spent category has a budget.

    Args:
        totals: A mapping of category name to total amount spent.
        budgets: A mapping of category name to budget limit.
    """
    lines = build_budget_lines(totals, budgets)
    if not lines:
        return
    print()
    for line in lines:
        print(line)


def write_report(
    totals: dict[str, float],
    budgets: dict[str, float],
    skipped_reasons: list[str],
    report_path: str | Path,
) -> None:
    """Write a plain-text expense report to a file.

    The report contains the expense summary, the budget status, and a list
    of skipped rows. Any existing file at ``report_path`` is overwritten.

    Args:
        totals: A mapping of category name to total amount spent.
        budgets: A mapping of category name to budget limit.
        skipped_reasons: Messages describing each row skipped during loading.
        report_path: Path of the report file to write.

    Raises:
        OSError: If the report file cannot be opened for writing.
    """
    lines = ["EXPENSE REPORT", "=" * 40, ""]

    lines.extend(build_summary_lines(totals))
    lines.append("")

    budget_lines = build_budget_lines(totals, budgets)
    lines.extend(budget_lines if budget_lines else ["Budget Status", "-" * 20, "No budgeted categories with spending."])
    lines.append("")

    lines.append("Skipped Rows")
    lines.append("-" * 20)
    if skipped_reasons:
        lines.extend(f"- {reason}" for reason in skipped_reasons)
    else:
        lines.append("None")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    """Run the expense summarizer from the command line.

    Loads budgets and expenses, prints the summary and budget status, and
    writes the full report to ``REPORT_PATH``.
    """
    args = parse_args()
    budgets = load_budgets(args.budgets)

    rows, skipped_reasons = load_expenses(args.csv, budgets)
    totals = calculate_totals(rows)
    print_summary(totals)
    print_budget_status(totals, budgets)
    print()
    print(f"Skipped {len(skipped_reasons)} row(s) due to validation errors.")

    write_report(totals, budgets, skipped_reasons, REPORT_PATH)
    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
