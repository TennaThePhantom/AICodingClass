# Watchlist Tracker

A movie watchlist tracker. Keeps a list of movies I want to watch or
have watched. Plain Python scripts + a CSV file. No frameworks.

## Commands

- Add an entry:  python add_entry.py "Title" "type" "genre" "status" "rating"
  (rating may be left out or blank)
- Filter / sort: python filter_entries.py --status unwatched --genre Action --sort date_added
- Sort options: date_added or rating

## Structure

All information lives in watchlist.csv in this file
Do not rename, move, or duplicate it.

Scripts:
- add_entry.py, appends one row to watchlist.csv
- filter_entries.py, reads watchlist.csv and prints filtered/sorted rows

## CSV columns

title, type, genre, status, rating, date_added

- title: movie name, exactly as written (don't "fix" capitalization)
- type: "movie" or "show"
- genre: e.g. Action, Comedy, Animation, Sci-Fi
- status: "watched" or "unwatched"
- rating: 0-10, or blank if not rated yet(can have decimal rating as well like 5.3)
- date_added: YYYY-MM-DD

## Rules

- Always modify watchlist.csv through the scripts never by hand.
- Use YYYY-MM-DD for any new dates.
- Leave rating blank if a movie hasn't been rated.
- Never delete rows unless I explicitly ask.
- If something is unclear, ask before guessing.

## Do Not
- Do not run /init.
- Do not rewrite or reformat the whole CSV.
- Do not create new CSV files all data goes in watchlist.csv.
- Do not add new columns without asking.