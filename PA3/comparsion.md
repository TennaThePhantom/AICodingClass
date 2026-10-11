# Original Week 2 prompt
Read the Python file at 'expenses.py'. Add a clear PEP 257-compliant docstring
(python) to every function, method, and class that currently lacks one. Do not
change any logic, imports, or formatting. Preserve the original code exactly
except for the inserted docstrings. Overwrite the file in place.

It was vague about docstring style, structure, and edge cases, which made it an
ideal to demonstrate how 4-part structure improves output quality.

# Rewritten prompt (4-part)
See rewritten_prompt.txt

# output comparison

| Function | Original output | Rewritten output |
|---|---|---|
| parse_args | 1-line docstring | Full docstring + Returns + Raises: SystemExit |
| load_budget/rename PA3-task2-interview
s | 1-line docstring | Full docstring + Args + Returns |
| _parse_row | Partial, no Args | Full Args + Returns |
| load_expenses | Prose paragraph | Structured Args + Returns |
| calculate_totals | 1-line docstring | Full Args + Returns |
| build_summary_lines | 1-line docstring | Full docstring + Args + Returns |
| check_budgets | Partial | Full Args + Returns |
| build_budget_lines | 1-line docstring | Full Args + Returns |
| print_summary | 1-line docstring | Full Args |
| print_budget_status | 1-line docstring | Full docstring + Args |
| write_report | 1-line docstring | Full docstring + Args + Raises: OSError |
| main | 1-line docstring | Multi-line docstring |

# improvements
 Every function received a structured docstring the original left many as one-liners.
Raises sections appeared where relevant the original never added any.
 Args sections appear consistently the original added them only sometimes.
Uniform Google-style formatting across the entire file the original was inconsistent.

## Diff
See comparison_diff.txt

# files that claude made
- tests
- budget_alert.py
- spec.md
- output_original
- output_rewritten

# files that I used
expense_without_docstring.py(week 2)
expense.py(week 2)