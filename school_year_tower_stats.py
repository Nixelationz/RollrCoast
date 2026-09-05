#!/usr/bin/env python3
"""Report the longest and shortest tower completed during each school year."""

import csv
from datetime import date, datetime
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "rollrcoast.csv"

SCHOOL_YEARS = (
    ("7th grade", date(2021, 8, 25), date(2022, 6, 16)),
    ("8th grade", date(2022, 8, 24), date(2023, 6, 15)),
    ("9th grade", date(2023, 8, 23), date(2024, 6, 13)),
    ("10th grade", date(2024, 8, 21), date(2025, 6, 12)),
    ("11th grade", date(2025, 8, 20), date(2026, 6, 11)),
    ("12th grade", date(2026, 8, 19), date(2027, 6, 10)),
)


def read_towers(csv_path: Path) -> list[dict]:
    towers = []
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            try:
                completed_at = datetime.fromisoformat(row["COMPLETION DATE"])
                completion_time = float(row["TIME [s]"])
            except (KeyError, TypeError, ValueError):
                continue

            towers.append(
                {
                    "tower": row.get("TOWER", "").strip(),
                    "acronym": row.get("ACRONYM", "").strip(),
                    "completed_at": completed_at,
                    "time_seconds": completion_time,
                }
            )
    return towers


def school_year_for(completed_on: date) -> str | None:
    for label, start, end in SCHOOL_YEARS:
        if start <= completed_on <= end:
            return label
    return None


def format_tower(tower: dict) -> str:
    acronym = f" ({tower['acronym']})" if tower["acronym"] else ""
    return (
        f"{tower['tower']}{acronym} - "
        f"{tower['time_seconds']:,.2f} seconds - "
        f"{tower['completed_at'].date().isoformat()}"
    )


def main() -> None:
    towers_by_year = {label: [] for label, _, _ in SCHOOL_YEARS}
    outside_school_years = 0

    for tower in read_towers(DATA_PATH):
        school_year = school_year_for(tower["completed_at"].date())
        if school_year is None:
            outside_school_years += 1
        else:
            towers_by_year[school_year].append(tower)

    for label, _, _ in SCHOOL_YEARS:
        towers = towers_by_year[label]
        print(label)
        if not towers:
            print("  No completed towers in this date range.")
            continue

        longest = max(towers, key=lambda tower: tower["time_seconds"])
        shortest = min(towers, key=lambda tower: tower["time_seconds"])
        print(f"  Longest: {format_tower(longest)}")
        print(f"  Shortest: {format_tower(shortest)}")

    print(f"\nTowers outside the listed school years: {outside_school_years}")


if __name__ == "__main__":
    main()
