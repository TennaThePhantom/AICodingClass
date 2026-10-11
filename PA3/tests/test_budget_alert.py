"""Tests for budget_alert.py. Section numbers refer to SPEC.md."""

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(ROOT))

import budget_alert  # noqa: E402

HEADER = "date,category,amount,description\n"


class CLITestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.out = self.tmp / "alert.md"

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, content):
        path = self.tmp / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_bytes(content.encode("utf-8"))
        return path

    def run_tool(self, csv_content, json_content='{"food": 300}'):
        """Run main() in-process. Returns (exit_code, report_text_or_None, stderr)."""
        expenses = self.write("expenses.csv", csv_content) if csv_content is not None else self.tmp / "nope.csv"
        budgets = self.write("budgets.json", json_content) if json_content is not None else self.tmp / "nope.json"
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = budget_alert.main(
                ["--expenses", str(expenses), "--budgets", str(budgets), "--out", str(self.out)]
            )
        report = self.out.read_bytes().decode("utf-8") if self.out.exists() else None
        return code, report, err.getvalue()

    def skipped(self, report):
        section = report.split("## Skipped Rows\n\n", 1)[1]
        return [line[2:] for line in section.splitlines() if line.startswith("- ")]

    def summary_rows(self, report):
        section = report.split("## Summary\n\n", 1)[1].split("\n\n## ", 1)[0]
        return section.splitlines()

    def assertFatal(self, csv_content, json_content='{"food": 300}', fragment=""):
        code, report, err = self.run_tool(csv_content, json_content)
        self.assertEqual(code, 1)
        self.assertIsNone(report, "no output file may be written on a fatal error")
        self.assertTrue(err.startswith("error: "), err)
        self.assertIn(fragment, err)
        return err


class GoldenFileTests(CLITestCase):
    """§7 exact layout, §8.2 determinism."""

    def run_basic(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = budget_alert.main([
                "--expenses", str(FIXTURES / "basic" / "expenses.csv"),
                "--budgets", str(FIXTURES / "basic" / "budgets.json"),
                "--out", str(self.out),
            ])
        return code, self.out.read_bytes()

    def test_matches_expected_bytes(self):
        code, data = self.run_basic()
        self.assertEqual(code, 0)
        self.assertEqual(data, (FIXTURES / "basic" / "expected_alert.md").read_bytes())

    def test_byte_identical_across_runs(self):
        _, first = self.run_basic()
        _, second = self.run_basic()
        self.assertEqual(first, second)

    def test_lf_line_endings_and_single_trailing_newline(self):
        _, data = self.run_basic()
        self.assertNotIn(b"\r", data)
        self.assertTrue(data.endswith(b"\n") and not data.endswith(b"\n\n"))

    def test_subprocess_entry_point(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "budget_alert.py"),
             "--expenses", str(FIXTURES / "basic" / "expenses.csv"),
             "--budgets", str(FIXTURES / "basic" / "budgets.json"),
             "--out", str(self.out)],
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.out.read_bytes(), (FIXTURES / "basic" / "expected_alert.md").read_bytes())


class CLIArgumentTests(CLITestCase):
    """§3."""

    def test_all_flags_required(self):
        for argv in ([], ["--expenses", "a.csv", "--budgets", "b.json"], ["--out", "x.md"]):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    budget_alert.main(argv)
                self.assertEqual(ctx.exception.code, 2)

    def test_over_budget_still_exits_zero(self):
        code, report, _ = self.run_tool(HEADER + "d,food,999,x\n")
        self.assertEqual(code, 0)
        self.assertIn("| OVER |", report)

    def test_unwritable_output_is_fatal(self):
        self.out = self.tmp / "missing_dir" / "alert.md"
        code, _, err = self.run_tool(HEADER + "d,food,1,x\n")
        self.assertEqual(code, 1)
        self.assertIn("cannot write output file", err)
        self.assertFalse(self.out.exists())

    def test_fatal_does_not_modify_existing_output(self):
        self.out.write_text("previous report", encoding="utf-8")
        self.run_tool(HEADER + "d,food,1,x\n", "not json")
        self.assertEqual(self.out.read_text(encoding="utf-8"), "previous report")


class BudgetFileTests(CLITestCase):
    """§4.1."""

    def test_missing_budgets_file(self):
        self.assertFatal(HEADER, None, "cannot read budgets file")

    def test_invalid_json(self):
        self.assertFatal(HEADER, '{"food": 300,', "not valid JSON")

    def test_top_level_not_object(self):
        for doc in ("[1, 2]", "300", '"food"', "null"):
            with self.subTest(doc=doc):
                self.assertFatal(HEADER, doc, "must be a JSON object")

    def test_nested_values_fatal(self):
        for doc in ('{"food": {"limit": 300}}', '{"food": [300]}'):
            with self.subTest(doc=doc):
                self.assertFatal(HEADER, doc, "must be flat")

    def test_duplicate_normalized_keys_fatal(self):
        self.assertFatal(HEADER, '{"Food": 300, "food ": 100}', "duplicate category")

    def test_exact_duplicate_keys_fatal(self):
        self.assertFatal(HEADER, '{"food": 300, "food": 100}', "duplicate category")

    def test_duplicate_fatal_even_if_one_value_invalid(self):
        self.assertFatal(HEADER, '{"Food": 300, "food": "abc"}', "duplicate category")

    def test_numeric_string_accepted(self):
        code, report, err = self.run_tool(HEADER + "d,food,250,x\n", '{"food": " 300 "}')
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("| food | 300.00 | 250.00 | 50.00 | OK |", report)

    def test_invalid_values_skipped_with_warning(self):
        cases = {
            '"abc"': "non-numeric", '"$300"': "non-numeric", '""': "non-numeric",
            '"1e3"': "non-numeric", "true": "non-numeric", "null": "non-numeric",
            "NaN": "non-numeric", "Infinity": "non-numeric",
            "-50": "negative", '"-50"': "negative", "-0.0": "negative",
        }
        for value, kind in cases.items():
            with self.subTest(value=value):
                code, report, err = self.run_tool(
                    HEADER + "d,gifts,5,x\nd,food,1,x\n", f'{{"gifts": {value}, "food": 300}}'
                )
                self.assertEqual(code, 0)
                self.assertIn(f'warning: skipping budget "gifts": {kind} value', err)
                self.assertNotIn("warning", report)
                self.assertIn('Row 2: no budget for category "gifts"', self.skipped(report))
                self.assertIn("| food |", report)

    def test_empty_key_skipped_with_warning(self):
        code, report, err = self.run_tool(HEADER + "d,food,1,x\n", '{"  ": 5, "food": 300}')
        self.assertEqual(code, 0)
        self.assertIn("warning: skipping budget with empty category name", err)

    def test_zero_budget_any_spend_is_over(self):
        _, report, _ = self.run_tool(HEADER + "d,gifts,0.01,x\n", '{"gifts": 0}')
        self.assertIn("- **gifts**: spent 0.01 of 0.00 (over by 0.01)", report)

    def test_empty_budgets_object(self):
        code, report, _ = self.run_tool(HEADER + "d,food,1,x\n", "{}")
        self.assertEqual(code, 0)
        self.assertEqual(self.skipped(report), ['Row 2: no budget for category "food"'])

    def test_budget_float_kept_exact(self):
        _, report, _ = self.run_tool(HEADER + "d,food,0.1,x\nd,food,0.2,x\n", '{"food": 0.3}')
        self.assertIn("| food | 0.30 | 0.30 | 0.00 | OK |", report)


class ExpensesFileTests(CLITestCase):
    """§4.2, §4.3."""

    def test_missing_expenses_file(self):
        self.assertFatal(None, '{"food": 300}', "cannot read expenses file")

    def test_missing_required_columns(self):
        for header in ("date,amount,description\n", "date,category,description\n", "food,12.00\n"):
            with self.subTest(header=header):
                self.assertFatal(header + "x,y\n", fragment="missing required column")

    def test_duplicate_required_column(self):
        self.assertFatal("category,amount,Amount\nfood,1,2\n", fragment="duplicate column 'amount'")

    def test_header_case_and_whitespace_insensitive_any_order(self):
        _, report, _ = self.run_tool(" AMOUNT , Notes ,CATEGORY\n5, x ,food\n")
        self.assertIn("| food | 300.00 | 5.00 | 295.00 | OK |", report)

    def test_empty_file_gives_empty_report(self):
        for content in ("", "   \n\n"):
            with self.subTest(content=repr(content)):
                code, report, _ = self.run_tool(content)
                self.assertEqual(code, 0)
                self.assertEqual(report, (
                    "# Budget Alert Report\n\n## Over Budget\n\nNone.\n\n"
                    "## Summary\n\nNone.\n\n## Skipped Rows\n\nNone.\n"
                ))

    def test_header_only_gives_empty_report(self):
        code, report, _ = self.run_tool(HEADER)
        self.assertEqual(code, 0)
        self.assertEqual(self.summary_rows(report), ["None."])
        self.assertEqual(self.skipped(report), [])

    def test_utf8_bom_is_stripped(self):
        code, report, _ = self.run_tool(b"\xef\xbb\xbfcategory,amount\nfood,5\n")
        self.assertEqual(code, 0)
        self.assertIn("| food |", report)

    def test_crlf_input(self):
        _, report, _ = self.run_tool("category,amount\r\nfood,5\r\nbad,x\r\n")
        self.assertEqual(self.skipped(report), ['Row 3: invalid amount "x"'])

    def test_extra_fields_ignored(self):
        _, report, _ = self.run_tool("category,amount\nfood,5,lunch, with comma,extra\n")
        self.assertIn("| food | 300.00 | 5.00 |", report)

    def test_short_row_counts_as_missing_field(self):
        _, report, _ = self.run_tool("date,category,amount\nd,food\nd\n")
        self.assertEqual(self.skipped(report), ["Row 2: missing amount", "Row 3: missing category"])

    def test_blank_lines_ignored_but_counted(self):
        _, report, _ = self.run_tool("category,amount\n\nfood,x\n\nfood,1\n")
        self.assertEqual(self.skipped(report), ['Row 3: invalid amount "x"'])

    def test_quoted_fields(self):
        _, report, _ = self.run_tool('category,amount,description\n"food","7.00","a, b"\n')
        self.assertIn("| food | 300.00 | 7.00 |", report)


class RowValidationTests(CLITestCase):
    """§5."""

    def reasons(self, rows, budgets='{"food": 300}'):
        _, report, _ = self.run_tool("category,amount\n" + rows, budgets)
        return self.skipped(report)

    def test_valid_amounts(self):
        for amount in ("12.50", "0", "12.345", " 7 ", "007.10"):
            with self.subTest(amount=amount):
                self.assertEqual(self.reasons(f"food,{amount}\n"), [])

    def test_invalid_amounts(self):
        for amount in ("$12.50", '"1,200.00"', "abc", ".50", "5.", "1e3", "+5", "NaN", "Infinity", "1 000", "١٢"):
            with self.subTest(amount=amount):
                raw = amount.strip('"')
                self.assertEqual(self.reasons(f"food,{amount}\n"), [f'Row 2: invalid amount "{raw}"'])

    def test_negative_amounts(self):
        for amount in ("-15.00", "-0", "-3"):
            with self.subTest(amount=amount):
                self.assertEqual(self.reasons(f"food,{amount}\n"), [f'Row 2: negative amount "{amount}"'])

    def test_missing_category(self):
        for category in ("", "   "):
            with self.subTest(category=repr(category)):
                self.assertEqual(self.reasons(f"{category},5\n"), ["Row 2: missing category"])

    def test_missing_amount(self):
        self.assertEqual(self.reasons("food,\nfood,   \n"), ["Row 2: missing amount", "Row 3: missing amount"])

    def test_no_budget_keeps_raw_trimmed_category(self):
        self.assertEqual(self.reasons("  Entertainment ,5\n"), ['Row 2: no budget for category "Entertainment"'])

    def test_first_failing_check_wins(self):
        rows = (
            ",\n"               # missing category beats missing amount
            " ,abc\n"           # missing category beats invalid amount
            "unknown,\n"        # missing amount beats no budget
            "unknown,abc\n"     # invalid amount beats no budget
            "unknown,-5\n"      # negative amount beats no budget
        )
        self.assertEqual(self.reasons(rows), [
            "Row 2: missing category",
            "Row 3: missing category",
            "Row 4: missing amount",
            'Row 5: invalid amount "abc"',
            'Row 6: negative amount "-5"',
        ])

    def test_category_matching_normalized(self):
        _, report, _ = self.run_tool("category,amount\nFOOD,1\n  food  ,2\nFood,3\n", '{" Food ": 300}')
        self.assertIn("| Food | 300.00 | 6.00 | 294.00 | OK |", report)


class ComputationTests(CLITestCase):
    """§6, §7."""

    def test_exactly_at_limit_is_ok(self):
        _, report, _ = self.run_tool("category,amount\nfood,100\nfood,200\n")
        self.assertIn("| food | 300.00 | 300.00 | 0.00 | OK |", report)
        self.assertIn("## Over Budget\n\nNone.\n", report)

    def test_one_cent_over(self):
        _, report, _ = self.run_tool("category,amount\nfood,300.01\n")
        self.assertIn("- **food**: spent 300.01 of 300.00 (over by 0.01)", report)
        self.assertIn("| OVER |", report)

    def test_over_uses_exact_not_rounded_values(self):
        # 300.004 displays as 300.00 but is still strictly greater than the limit.
        _, report, _ = self.run_tool("category,amount\nfood,300.004\n")
        self.assertIn("- **food**: spent 300.00 of 300.00 (over by 0.00)", report)

    def test_round_half_up_at_display_only(self):
        _, report, _ = self.run_tool("category,amount\nfood,0.005\nfood,0.005\nfood,0.125\n")
        # sum is 0.135 exactly -> 0.14 (half-up); summing rounded values would give 0.03
        self.assertIn("| food | 300.00 | 0.14 | 299.87 | OK |", report)

    def test_no_negative_zero(self):
        _, report, _ = self.run_tool("category,amount\nfood,300.001\n")
        self.assertIn("(over by 0.00)", report)
        self.assertNotIn("-0.00", report)

    def test_budgets_without_expenses_omitted(self):
        _, report, _ = self.run_tool("category,amount\nfood,1\n", '{"food": 300, "rent": 1000}')
        self.assertNotIn("rent", report)
        self.assertIn("| **Total** | 300.00 | 1.00 | 299.00 | |", report)

    def test_sorted_case_insensitively_with_budget_spelling(self):
        _, report, _ = self.run_tool(
            "category,amount\nzoo,1\nbeta,1\nalpha,1\n", '{"Zoo": 5, "beta": 5, "Alpha": 5}'
        )
        rows = self.summary_rows(report)[2:5]
        self.assertEqual([r.split(" | ")[0] for r in rows], ["| Alpha", "| beta", "| Zoo"])

    def test_over_budget_list_sorted(self):
        _, report, _ = self.run_tool("category,amount\nb,9\na,9\n", '{"b": 1, "a": 1}')
        over = report.split("## Over Budget\n\n", 1)[1].split("\n\n", 1)[0].splitlines()
        self.assertEqual(over, [
            "- **a**: spent 9.00 of 1.00 (over by 8.00)",
            "- **b**: spent 9.00 of 1.00 (over by 8.00)",
        ])

    def test_pipe_escaped_in_table(self):
        _, report, _ = self.run_tool("category,amount\na|b,1\n", '{"a|b": 5}')
        self.assertIn("| a\\|b | 5.00 | 1.00 | 4.00 | OK |", report)

    def test_total_row(self):
        _, report, _ = self.run_tool("category,amount\nfood,350\nfun,10\n", '{"food": 300, "fun": 50}')
        self.assertEqual(self.summary_rows(report)[-1], "| **Total** | 350.00 | 360.00 | -10.00 | |")

    def test_no_currency_or_thousands_separator(self):
        _, report, _ = self.run_tool("category,amount\nfood,1234567.5\n", '{"food": 2000000}')
        self.assertIn("| food | 2000000.00 | 1234567.50 | 765432.50 | OK |", report)


if __name__ == "__main__":
    unittest.main()
