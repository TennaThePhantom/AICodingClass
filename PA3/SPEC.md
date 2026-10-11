# SPEC: budget_alert — Over-Budget Markdown Report CLI

Status: **APPROVED** (2026-09-27), with §10 C amended.

## 1. Goal

A command-line tool for a class assignment. It reads an expenses CSV and a budgets JSON file, then writes a Markdown report (`alert.md`) that shows which categories are over budget, gives a summary table, and lists the rows it skipped. A grader runs it against test files, so the output must be **deterministic** (the same input always gives byte-identical output) and edge cases must be handled explicitly.

## 2. Constraints

- Python 3, **standard library only** (`csv`, `json`, `pathlib`, `argparse`, `decimal`, `re`, `sys`). No third-party packages.
- All money math uses `decimal.Decimal`, never `float`.
- Run manually. No scheduling, no network.

## 3. CLI

```
python budget_alert.py --expenses <path.csv> --budgets <path.json> --out <path.md>
```

- All three flags are **required** and have no defaults. A missing flag is an argparse usage error (exit 2, argparse's default).
- Exit codes:
  - `0`: success, including when categories are over budget.
  - `1`: fatal error. A message goes to stderr as `error: <message>` and **no output file is written**.
- Warnings go to stderr as `warning: <message>`. They never appear in `alert.md`.
- The output file is written **only after all parsing and computation succeed**. A fatal error must never leave a partial or new `alert.md` behind.

## 4. Inputs

### 4.1 Budgets JSON

- Must be a single flat JSON object: `{"food": 300, "transport": 200}`.
- Keys are category names and values are numeric limits.
- Parse numbers directly to `Decimal`, using `parse_float=Decimal` and converting ints to `Decimal`.

| Situation | Handling |
|---|---|
| File missing or unreadable | **Fatal** |
| Invalid JSON | **Fatal** |
| Top level is not an object (list, number, etc.) | **Fatal** |
| A value is an object or array (not flat) | **Fatal** |
| Two keys are the same after normalization (e.g. `"Food"` and `"food "`) | **Fatal** |
| A value is a numeric string (trimmed, matches the §5 amount grammar, e.g. `"300"`, `" 12.50 "`) | Valid. Converted to `Decimal` (`"300"` → 300) |
| A value is a non-numeric string (`"abc"`, `"$300"`, `""`), bool, null, NaN/Infinity, or negative (number or string) | Skip that key, print a warning |
| Key is empty or whitespace-only | Skip that key, print a warning |
| Value is `0` | Valid. Any spending in that category is over budget |
| `{}` (no budgets) | Valid. Every expense row is skipped as "no budget for category" |

### 4.2 Expenses CSV

- Read as `utf-8-sig`, which strips an Excel BOM if present.
- Columns: `date, category, amount, description`. Only `category` and `amount` are **required**. `date` and `description` are optional and unused.
- Header names are matched **case-insensitively after trimming whitespace**. Extra columns are ignored, and column order doesn't matter.

| Situation | Handling |
|---|---|
| File missing or unreadable | **Fatal** |
| File is empty (0 bytes / only whitespace) | Not fatal. Valid report with empty sections |
| Header-only (no data rows) | Not fatal. Valid report with empty sections |
| First row (the header) lacks `category` or `amount` | **Fatal** ("missing required column(s)") |
| Header has a required column twice (e.g. two `amount`) | **Fatal** (ambiguous) |
| Data row has extra fields | Extra fields ignored |
| Data row is too short to contain the category/amount field | That field counts as missing (see §5) |
| Completely blank line | Ignored silently, but still counts toward row numbers |

### 4.3 Row numbering

The header is row 1, so the first data record is **Row 2**. Every record the `csv` reader returns increments the counter, including blank lines, which are ignored.

## 5. Row validation

Normalization for matching is `value.strip().lower()`, applied to both CSV categories and budget keys.

Amount grammar: after trimming, the amount must fully match `-?\d+(\.\d+)?`.
- Valid: `12.50`, `0`, `12.345` (kept at full precision)
- Invalid: `$12.50`, `1,200.00`, `abc`, `.50`, `5.`, `1e3`, `+5`, `NaN`
- Matches the pattern but starts with `-` (e.g. `-15.00`): negative, so skipped

Checks run in this order, and **the first failing check is the only reason reported**:

| # | Condition | Exact skip reason |
|---|---|---|
| 1 | Category missing, empty, or whitespace-only | `Row N: missing category` |
| 2 | Amount missing or empty after trim | `Row N: missing amount` |
| 3 | Amount doesn't match the grammar | `Row N: invalid amount "<raw>"` |
| 4 | Amount is negative | `Row N: negative amount "<raw>"` |
| 5 | Normalized category not in budgets | `Row N: no budget for category "<raw category>"` |

`<raw>` / `<raw category>` is the field value with surrounding whitespace trimmed. Its original case is kept.

## 6. Computation

- Spent per category = the exact `Decimal` sum of valid amounts.
- A category is **over budget** when `spent > limit` (strictly). Spending exactly the limit is OK.
- Two statuses only: `OVER` and `OK`. No warning tier.
- Budget categories with **no valid expenses are left out** of the report entirely.
- Display name = the budget file's key with whitespace trimmed and its original case kept.
- Sort order everywhere: alphabetical by normalized (lowercased) category name.
- Rounding: sums are exact, and each value is rounded **half-up to 2 decimals only at display time** (`quantize(Decimal("0.01"), ROUND_HALF_UP)`).
- Remaining = limit − spent (negative when over). Over by = spent − limit.

## 7. Output: `alert.md`

- UTF-8, `\n` line endings on every platform (open with `newline="\n"`), ending with a single trailing newline.
- Numbers: always 2 decimals, no currency symbol, no thousands separator. Negatives look like `-50.00`.
- A `|` inside a category name is escaped as `\|` in the table.
- Every section heading is always present. An empty section contains the single line `None.`

Exact layout:

```markdown
# Budget Alert Report

## Over Budget

- **Food**: spent 350.00 of 300.00 (over by 50.00)

## Summary

| Category | Budget | Spent | Remaining | Status |
|----------|-------:|------:|----------:|--------|
| Food | 300.00 | 350.00 | -50.00 | OVER |
| Transport | 200.00 | 120.00 | 80.00 | OK |
| **Total** | 500.00 | 470.00 | 30.00 | |

## Skipped Rows

- Row 4: invalid amount "abc"
- Row 7: no budget for category "entertainment"
```

- **Total row:** sums Budget, Spent, and Remaining over the listed categories only, and its Status cell is empty. If the summary is empty, the table is replaced by `None.` and there is no Total row.
- Skipped rows are listed in ascending row order.

## 8. Acceptance criteria

1. A stdlib `unittest` suite (`tests/test_budget_alert.py`) with small fixture files in `tests/fixtures/` covers every rule in §3–§7, including each fatal case, each skip reason, the first-reason-wins order, the `>` vs `=` threshold, zero budget, BOM input, and empty/header-only CSV.
2. Running the tool twice on the same input gives **byte-identical** `alert.md`.
3. Every fatal case exits `1`, prints `error: ...` to stderr, and **does not create or modify** the output file.
4. Over-budget results still exit `0`.
5. `python -m unittest discover tests` passes with no third-party packages installed.

## 9. Deliverables

```
PA3/
  SPEC.md
  budget_alert.py
  tests/test_budget_alert.py
  tests/fixtures/...
```

## 10. Assumptions (approved)

- **A. "Missing header" vs "empty CSV":** these conflicted, so I read "missing header" as "the first row doesn't contain `category`/`amount`" (fatal), while a 0-byte or whitespace-only file counts as empty (valid, empty report).
- **B. Blank lines** are ignored silently but still count toward row numbers, so row numbers line up with the lines in the file.
- **C. Budget value types (amended):** JSON numbers and numeric strings are valid. `"300"` is accepted as 300. A numeric string must match the §5 amount grammar after trimming. Non-numeric values are skipped with a warning.
- **D.** Duplicate required header columns are fatal.
- **E.** The Total row also sums Remaining, and its Status cell is blank.
- **F.** An unwritable `--out` path is fatal (exit 1).
