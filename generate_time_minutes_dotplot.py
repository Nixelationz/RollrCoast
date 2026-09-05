#!/usr/bin/env python3
import csv
import math
from collections import Counter
from pathlib import Path


CSV_PATH = Path(__file__).resolve().parent / "rollrcoast.csv"
OUT_PATH = Path(__file__).resolve().parent / "graphs" / "time_minutes_dotplot.svg"


def read_time_minutes(csv_path: Path):
    values = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = (row.get("TIME [s]", "") or "").strip()
            if not raw:
                continue
            try:
                seconds = float(raw)
            except ValueError:
                continue
            values.append(math.floor(seconds / 60.0))
    return values


def bucket_for_minutes(minutes: int) -> int:
    if minutes <= 13:
        return 0
    return 1 + ((minutes - 14) // 13)


def bucket_label(bucket: int) -> str:
    if bucket == 0:
        return "0-13"
    start = bucket * 13 + 1
    end = start + 12
    return f"{start}-{end}"


def build_svg(values, output_path: Path):
    counts = Counter(bucket_for_minutes(v) for v in values)
    if not counts:
        raise ValueError("No TIME [s] values found in the CSV.")

    buckets = sorted(counts)
    max_count = max(counts.values())
    bucket_count = len(buckets)

    width = 1200
    height = 700
    pad_left = 90
    pad_right = 60
    pad_top = 70
    pad_bottom = 80
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    def x_scale(bucket_index):
        if bucket_count == 1:
            return pad_left + plot_w / 2
        return pad_left + (bucket_index / (bucket_count - 1)) * plot_w

    def y_scale(rank):
        if max_count <= 1:
            return height - pad_bottom - plot_h * 0.5
        return height - pad_bottom - (rank / max_count) * plot_h

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    lines.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    lines.append(f'<text x="{width / 2}" y="32" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" font-weight="bold">Dotplot of TIME [s] in 13-minute blocks</text>')
    lines.append(f'<text x="{width / 2}" y="56" text-anchor="middle" font-family="Arial, sans-serif" font-size="14">Each dot = one tower; x range shown as 0-13, 14-26, ...</text>')

    ax_x1 = pad_left
    ax_x2 = width - pad_right
    ax_y1 = height - pad_bottom
    ax_y2 = pad_top
    lines.append(f'<line x1="{ax_x1}" y1="{ax_y1}" x2="{ax_x2}" y2="{ax_y1}" stroke="#333" stroke-width="2"/>')
    lines.append(f'<line x1="{ax_x1}" y1="{ax_y1}" x2="{ax_x1}" y2="{ax_y2}" stroke="#333" stroke-width="2"/>')
    lines.append(f'<text x="{width / 2}" y="{height - 20}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14">13-minute range</text>')
    lines.append(f'<text x="22" y="{height / 2}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" transform="rotate(-90 22 {height / 2})">Count</text>')

    for bucket in buckets:
        x = x_scale(bucket)
        lines.append(f'<line x1="{x}" y1="{ax_y1}" x2="{x}" y2="{ax_y1 + 6}" stroke="#666" stroke-width="1"/>')
        lines.append(f'<text x="{x}" y="{ax_y1 + 22}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11">{bucket_label(bucket)}</text>')

    for tick in range(0, max_count + 1):
        y = y_scale(tick)
        lines.append(f'<line x1="{ax_x1 - 6}" y1="{y}" x2="{ax_x1}" y2="{y}" stroke="#666" stroke-width="1"/>')
        lines.append(f'<text x="{ax_x1 - 10}" y="{y + 4}" text-anchor="end" font-family="Arial, sans-serif" font-size="11">{tick}</text>')

    for bucket in buckets:
        cx = x_scale(bucket)
        total = counts[bucket]
        for rank in range(total):
            cy = y_scale(rank + 1)
            lines.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="#4c78a8" stroke="#1f2d3d" stroke-width="0.7" opacity="0.9"/>')

    lines.append('</svg>')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    values = read_time_minutes(CSV_PATH)
    if not values:
        raise SystemExit(f"No valid TIME [s] values found in {CSV_PATH}.")
    build_svg(values, OUT_PATH)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
