import pytest

import expenses


def write_csv(path, rows):
    """Write a header-only or header+data CSV. `rows` is a list of already comma-joined lines."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write("date,category,amount,note\n")
        for row in rows:
            f.write(row + "\n")


def test_normal_csv_multiple_categories(tmp_path):
    """Verify a valid CSV with several categories loads cleanly and totals correctly."""
    csv_path = tmp_path / "expenses.csv"
    write_csv(csv_path, [
        "2025-01-01,food,20,lunch",
        "2025-01-02,transport,12,bus",
        "2025-01-03,food,80,groceries",
        "2025-01-04,entertainment,45,movie",
    ])

    rows, skipped_reasons = expenses.load_expenses(csv_path)
    totals = expenses.calculate_totals(rows)

    assert skipped_reasons == []
    assert totals == {"food": 100.0, "transport": 12.0, "entertainment": 45.0}


def test_empty_csv_header_only(tmp_path):
    """Verify a header-only CSV yields no rows and no skipped-row reasons."""
    csv_path = tmp_path / "expenses.csv"
    write_csv(csv_path, [])

    rows, skipped_reasons = expenses.load_expenses(csv_path)

    assert rows == []
    assert skipped_reasons == []


def test_missing_column_in_row(tmp_path):
    """Verify a row with missing columns is skipped and reported as such."""
    csv_path = tmp_path / "expenses.csv"
    write_csv(csv_path, [
        "2025-01-01,food",  # amount and note missing entirely
        "2025-01-02,transport,12,bus",
    ])

    rows, skipped_reasons = expenses.load_expenses(csv_path)

    assert rows == [("transport", 12.0)]
    assert len(skipped_reasons) == 1
    assert "missing columns" in skipped_reasons[0]


def test_non_numeric_amount(tmp_path):
    """Verify a row with a non-numeric amount is skipped as an invalid amount."""
    csv_path = tmp_path / "expenses.csv"
    write_csv(csv_path, [
        "2025-01-01,food,abc,lunch",
        "2025-01-02,transport,12,bus",
    ])

    rows, skipped_reasons = expenses.load_expenses(csv_path)

    assert rows == [("transport", 12.0)]
    assert len(skipped_reasons) == 1
    assert "invalid amount" in skipped_reasons[0]


def test_category_not_in_budget_dict(tmp_path):
    """Verify a row whose category is not recognized is skipped and reported."""
    csv_path = tmp_path / "expenses.csv"
    write_csv(csv_path, [
        "2025-01-01,rent,900,apartment",
        "2025-01-02,food,20,lunch",
    ])

    rows, skipped_reasons = expenses.load_expenses(csv_path)

    assert rows == [("food", 20.0)]
    assert len(skipped_reasons) == 1
    assert "unrecognized category" in skipped_reasons[0]


def test_negative_amount(tmp_path):
    """Verify a row with a negative amount is skipped as suspicious."""
    csv_path = tmp_path / "expenses.csv"
    write_csv(csv_path, [
        "2025-01-01,food,-15,refund",
        "2025-01-02,food,20,lunch",
    ])

    rows, skipped_reasons = expenses.load_expenses(csv_path)

    assert rows == [("food", 20.0)]
    assert len(skipped_reasons) == 1
    assert "suspicious" in skipped_reasons[0]


def test_total_calculation_correctness():
    """Verify calculate_totals sums amounts correctly for each category."""
    rows = [
        ("food", 23.50),
        ("food", 80.00),
        ("transport", 12.00),
        ("transport", 50.00),
        ("entertainment", 45.00),
    ]

    totals = expenses.calculate_totals(rows)

    assert totals["food"] == pytest.approx(103.50)
    assert totals["transport"] == pytest.approx(62.00)
    assert totals["entertainment"] == pytest.approx(45.00)
    assert sum(totals.values()) == pytest.approx(210.50)


def test_write_report_creates_file_with_expected_sections(tmp_path):
    """Verify write_report creates a file containing all expected report sections."""
    totals = {"food": 100.0, "transport": 12.0}
    budgets = {"food": 200, "transport": 100}
    skipped_reasons = ["Line 5: invalid amount 'abc'"]
    report_path = tmp_path / "report.txt"

    expenses.write_report(totals, budgets, skipped_reasons, report_path)

    content = report_path.read_text(encoding="utf-8")

    assert "EXPENSE REPORT" in content
    assert "Expense Summary" in content
    assert "Budget Status" in content
    assert "Skipped Rows" in content
    assert "Line 5: invalid amount 'abc'" in content
