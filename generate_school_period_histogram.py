#!/usr/bin/env python3
"""Generate an SVG histogram of towers completed in each school period."""

from html import escape
from pathlib import Path

from generate_school_year_tower_table import (
    DATA_PATH,
    build_periods,
    period_for,
    read_towers,
)

OUTPUT_PATH = Path(__file__).resolve().parent / "graphs" / "school_period_tower_histogram.svg"


def period_counts() -> list[tuple[str, int]]:
    periods = build_periods()
    counts = {label: 0 for label, _, _ in periods}
    for tower in read_towers(DATA_PATH):
        label = period_for(tower["completed_at"].date(), periods)
        if label is not None:
            counts[label] += 1
    return [(label, counts[label]) for label, _, _ in periods if counts[label]]


def build_svg(counts: list[tuple[str, int]]) -> str:
    width = 1280
    height = 760
    left = 90
    right = 40
    top = 80
    bottom = 170
    chart_width = width - left - right
    chart_height = height - top - bottom
    max_count = max(count for _, count in counts)
    y_step = 20
    y_max = ((max_count + y_step - 1) // y_step) * y_step
    bar_gap = chart_width / len(counts)
    bar_width = bar_gap * 0.62

    def y_position(value: int) -> float:
        return top + chart_height - (value / y_max) * chart_height

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fffaf2"/>',
        '<text x="640" y="38" text-anchor="middle" font-family="Georgia, serif" font-size="28" font-weight="bold" fill="#17212b">',
        "Towers Completed by School Period",
        "</text>",
        '<text x="640" y="62" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#52606d">Number of towers completed in each grade and summer period</text>',
    ]

    for value in range(0, y_max + 1, y_step):
        y = y_position(value)
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="#ded7cc" stroke-width="1"/>')
        lines.append(f'<text x="{left - 12}" y="{y + 5:.1f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#52606d">{value}</text>')

    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}" stroke="#17212b" stroke-width="2"/>')
    lines.append(f'<line x1="{left}" y1="{top + chart_height}" x2="{width - right}" y2="{top + chart_height}" stroke="#17212b" stroke-width="2"/>')

    for index, (label, count) in enumerate(counts):
        x = left + index * bar_gap + (bar_gap - bar_width) / 2
        y = y_position(count)
        color = "#167d9a" if "grade" in label else "#e07a3f"
        lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{top + chart_height - y:.1f}" fill="{color}"/>')
        lines.append(f'<text x="{x + bar_width / 2:.1f}" y="{y - 9:.1f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#17212b">{count}</text>')
        label_x = x + bar_width / 2
        label_y = top + chart_height + 28
        lines.append(f'<text x="{label_x:.1f}" y="{label_y}" text-anchor="start" transform="rotate(35 {label_x:.1f},{label_y})" font-family="Arial, sans-serif" font-size="13" fill="#17212b">{escape(label)}</text>')

    lines.extend(
        [
            f'<text x="{left - 62}" y="{top + chart_height / 2:.1f}" text-anchor="middle" transform="rotate(-90 {left - 62},{top + chart_height / 2:.1f})" font-family="Arial, sans-serif" font-size="14" fill="#52606d">Tower count</text>',
            f'<text x="{width / 2:.1f}" y="{height - 20}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#52606d">School period</text>',
            '</svg>',
        ]
    )
    return "\n".join(lines)


def main() -> None:
    counts = period_counts()
    if not counts:
        raise SystemExit("No school-period tower counts were found.")
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(build_svg(counts), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} with {sum(count for _, count in counts)} towers.")


if __name__ == "__main__":
    main()
