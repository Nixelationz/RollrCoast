#!/usr/bin/env python3
"""Generate a Markdown table of towers grouped by school year and summer."""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "rollrcoast.csv"
OUTPUT_PATH = Path(__file__).resolve().parent / "towers_by_school_year.md"

SCHOOL_YEARS = (
    ("7th grade", date(2021, 8, 25), date(2022, 6, 16)),
    ("8th grade", date(2022, 8, 24), date(2023, 6, 15)),
    ("9th grade", date(2023, 8, 23), date(2024, 6, 13)),
    ("10th grade", date(2024, 8, 21), date(2025, 6, 12)),
    ("11th grade", date(2025, 8, 20), date(2026, 6, 11)),
    ("12th grade", date(2026, 8, 19), date(2027, 6, 10)),
)


def format_date(value: date) -> str:
    return value.strftime("%B %-d, %Y")


def read_towers(csv_path: Path) -> list[dict]:
    towers = []
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            try:
                completed_at = datetime.fromisoformat(row["COMPLETION DATE"])
                order = int(row["ORDER"])
                tower = row["TOWER"].strip()
                acronym = row["ACRONYM"].strip()
                time = row["TIME"].strip()
            except (KeyError, TypeError, ValueError):
                continue

            towers.append(
                {
                    "order": order,
                    "tower": tower,
                    "acronym": acronym,
                    "completed_at": completed_at,
                    "time": time,
                }
            )
    return sorted(towers, key=lambda tower: tower["completed_at"])


def build_periods() -> list[tuple[str, date, date | None]]:
    periods = []
    for index, (label, start, end) in enumerate(SCHOOL_YEARS):
        periods.append((label, start, end))
        if index + 1 < len(SCHOOL_YEARS):
            next_start = SCHOOL_YEARS[index + 1][1]
            summer_start = end + timedelta(days=1)
            summer_end = next_start - timedelta(days=1)
            periods.append(
                (
                    f"Summer {summer_start.year}",
                    summer_start,
                    summer_end,
                )
            )
    return periods


def period_for(completed_on: date, periods: list[tuple[str, date, date | None]]) -> str | None:
    for label, start, end in periods:
        if start <= completed_on and (end is None or completed_on <= end):
            return label
    return None


def line_for(tower: dict) -> str:
    completed_date = format_date(tower["completed_at"].date())
    return (
        f"{tower['order']}. {tower['tower']} ({tower['acronym']}), "
        f"beaten on {completed_date} in {tower['time']}"
    )


def build_markdown(towers: list[dict]) -> str:
    periods = build_periods()
    grouped = {label: [] for label, _, _ in periods}
    unassigned = []

    for tower in towers:
        label = period_for(tower["completed_at"].date(), periods)
        if label is None:
            unassigned.append(tower)
        else:
            grouped[label].append(tower)

    if unassigned:
        dates = ", ".join(format_date(tower["completed_at"].date()) for tower in unassigned)
        raise ValueError(f"Could not assign {len(unassigned)} tower(s) to a school period: {dates}")

    sections = [
        "# Towers by School Year",
        "",
        "## Breakdown",
        "",
        "| Time period | Tower count |",
        "| --- | ---: |",
    ]
    sections.extend(
        f"| {label} | {len(grouped[label])} |"
        for label, _, _ in periods
        if grouped[label]
    )
    sections.extend(["", "## Towers", ""])

    for label, start, end in periods:
        towers_in_period = grouped[label]
        if not towers_in_period:
            continue
        end_text = format_date(end) if end is not None else "present"
        sections.append(f"## {label} ({format_date(start)} - {end_text})")
        sections.append("")
        sections.extend(line_for(tower) for tower in towers_in_period)
        sections.append("")

    return "\n".join(sections).rstrip() + "\n"


def main() -> None:
    towers = read_towers(DATA_PATH)
    markdown = build_markdown(towers)
    OUTPUT_PATH.write_text(markdown, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} with {len(towers)} towers.")


if __name__ == "__main__":
    main()
