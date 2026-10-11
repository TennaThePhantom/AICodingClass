"""
Append one entry to watchlist.csv.

Usage:
    python add_entry.py "Title" "type" "genre" "status" "rating"

rating may be omitted or left blank.
"""

import csv
import sys
from datetime import date
from pathlib import Path

CSV_PATH = Path(__file__).parent / "watchlist.csv"
VALID_TYPES = {"movie", "show"}
VALID_STATUSES = {"watched", "unwatched"}


def main():
    if len(sys.argv) not in (5, 6):
        print(
            'Usage: python add_entry.py "Title" "type" "genre" "status" "rating"\n'
            "(rating may be omitted or blank)"
        )
        sys.exit(1)

    title = sys.argv[1]
    entry_type = sys.argv[2]
    genre = sys.argv[3]
    status = sys.argv[4]
    rating = sys.argv[5] if len(sys.argv) == 6 else ""

    if entry_type not in VALID_TYPES:
        print(f'Error: type must be one of {sorted(VALID_TYPES)}, got "{entry_type}"')
        sys.exit(1)

    if status not in VALID_STATUSES:
        print(f'Error: status must be one of {sorted(VALID_STATUSES)}, got "{status}"')
        sys.exit(1)

    if rating:
        try:
            rating_value = float(rating)
        except ValueError:
            print(f'Error: rating must be a number 0-10, got "{rating}"')
            sys.exit(1)
        if not (0 <= rating_value <= 10):
            print(f'Error: rating must be between 0 and 10, got "{rating}"')
            sys.exit(1)

    date_added = date.today().isoformat()

    needs_newline = False
    if CSV_PATH.exists() and CSV_PATH.stat().st_size > 0:
        with CSV_PATH.open("rb") as f:
            f.seek(-1, 2)
            needs_newline = f.read(1) not in (b"\n", b"\r")

    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")
        writer = csv.writer(f)
        writer.writerow([title, entry_type, genre, status, rating, date_added])

    print(f'Added "{title}" ({entry_type}, {genre}, {status}) on {date_added}')


if __name__ == "__main__":
    main()
