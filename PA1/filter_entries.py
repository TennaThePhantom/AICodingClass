"""
Filter and sort watchlist.csv.

Usage:
    python filter_entries.py --status unwatched --genre Action --sort date_added

All flags optional. With no flags, prints the whole list.
Sort options: date_added or rating
"""

import argparse
import csv
from pathlib import Path

CSV_PATH = Path(__file__).parent / "watchlist.csv"


def parse_args():
    parser = argparse.ArgumentParser(description="Filter and sort watchlist.csv")
    parser.add_argument("--status", choices=["watched", "unwatched"])
    parser.add_argument("--genre")
    parser.add_argument("--sort", choices=["date_added", "rating"])
    return parser.parse_args()


def main():
    args = parse_args()

    with CSV_PATH.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if args.status:
        rows = [r for r in rows if r["status"] == args.status]

    if args.genre:
        rows = [r for r in rows if r["genre"].lower() == args.genre.lower()]

    if args.sort == "date_added":
        rows.sort(key=lambda r: r["date_added"])
    elif args.sort == "rating":
        rows.sort(key=lambda r: float(r["rating"]) if r["rating"] else -1, reverse=True)

    if not rows:
        print("No matching entries.")
        return

    header = f'{"title":<45} {"type":<6} {"genre":<10} {"status":<10} {"rating":<7} {"date_added"}'
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f'{r["title"]:<45} {r["type"]:<6} {r["genre"]:<10} {r["status"]:<10} '
            f'{r["rating"]:<7} {r["date_added"]}'
        )


if __name__ == "__main__":
    main()
