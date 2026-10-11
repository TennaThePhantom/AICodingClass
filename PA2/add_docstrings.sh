#!/bin/bash
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <python_file>"
    exit 1
fi

FILE="$1"

if [ ! -f "$FILE" ]; then
    echo "Error: '$FILE' not found."
    exit 1
fi

PROMPT="Read the Python file at '$FILE' Add a clear PEP 257-compliant docstring(python) to every function, method, and class that currently lacks one. Do not change any logic, imports, or formatting. Preserve the original code exactly except for the inserted docstrings. Overwrite the file in place."

claude -p "$PROMPT" --allowedTools "Read,Edit,Write"

echo "Done. Docstrings added to $FILE."