#!/usr/bin/env python3
import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import median


def read_points(csv_path):
    points = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                x = float(row.get("NUM", ""))
                y = float(row.get("TIME [s]", ""))
            except ValueError:
                continue
            points.append({"x": x, "y": y, "row": row})
    return points


def cross(o, a, b):
    return (a["x"] - o["x"]) * (b["y"] - o["y"]) - (a["y"] - o["y"]) * (b["x"] - o["x"]) if isinstance(o, dict) else (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])


def convex_hull(points):
    pts = sorted(points, key=lambda p: (p["x"], p["y"]))
    if len(pts) <= 1:
        return pts
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def point_on_segment(pt, a, b, eps=1e-9):
    if abs(cross(a, b, pt)) > eps:
        return False
    return min(a["x"], b["x"]) - eps <= pt["x"] <= max(a["x"], b["x"]) + eps and min(a["y"], b["y"]) - eps <= pt["y"] <= max(a["y"], b["y"]) + eps


def point_in_poly(pt, poly):
    if len(poly) < 3:
        return False
    x, y = pt["x"], pt["y"]
    inside = False
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        if point_on_segment(pt, a, b):
            return True
        if ((a["y"] > y) != (b["y"] > y)):
            x_int = a["x"] + (b["x"] - a["x"]) * (y - a["y"]) / (b["y"] - a["y"]) if (b["y"] - a["y"]) != 0 else a["x"]
            if x < x_int:
                inside = not inside
    return inside


def tukey_depth(points):
    n = len(points)
    if n == 0:
        return []
    depths = [n] * n
    for i, p in enumerate(points):
        best = n
        for j, q in enumerate(points):
            if i == j:
                continue
            pos = neg = zero = 0
            for r in points:
                c = (q["x"] - p["x"]) * (r["y"] - p["y"]) - (q["y"] - p["y"]) * (r["x"] - p["x"])
                if c > 0:
                    pos += 1
                elif c < 0:
                    neg += 1
                else:
                    zero += 1
            best = min(best, min(pos + zero, neg + zero))
            if best <= 1:
                break
        depths[i] = best
    return depths


def scale_polygon(poly, center, factor):
    return [
        {"x": center["x"] + factor * (p["x"] - center["x"]), "y": center["y"] + factor * (p["y"] - center["y"])}
        for p in poly
    ]


def build_svg(points, bag_poly, fence_poly, center, outliers, svg_path):
    pad = 40
    x_min = min(p["x"] for p in points)
    x_max = max(p["x"] for p in points)
    y_min = min(p["y"] for p in points)
    y_max = max(p["y"] for p in points)
    x_pad = max(1.0, (x_max - x_min) * 0.08)
    y_pad = max(1.0, (y_max - y_min) * 0.08)
    view_left = x_min - x_pad
    view_right = x_max + x_pad
    view_bottom = y_min - y_pad
    view_top = y_max + y_pad
    width = 1000
    height = 700

    def sx(x):
        return pad + (x - view_left) / (view_right - view_left) * (width - pad * 2)

    def sy(y):
        return height - pad - (y - view_bottom) / (view_top - view_bottom) * (height - pad * 2)

    def poly_to_svg(poly, fill, stroke, stroke_width=2, opacity=0.4):
        pts = " ".join(f"{sx(p['x'])},{sy(p['y'])}" for p in poly)
        return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" opacity="{opacity}"/>'

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width/2}" y="30" text-anchor="middle" font-family="Arial, sans-serif" font-size="22" font-weight="bold">Bagplot of NUM vs TIME [s]</text>',
        f'<text x="{width/2}" y="52" text-anchor="middle" font-family="Arial, sans-serif" font-size="14">X = NUM, Y = TIME [s]</text>',
    ]

    # axes
    lines.append(f'<line x1="{sx(view_left)}" y1="{sy(view_bottom)}" x2="{sx(view_right)}" y2="{sy(view_bottom)}" stroke="#333" stroke-width="2"/>')
    lines.append(f'<line x1="{sx(view_left)}" y1="{sy(view_bottom)}" x2="{sx(view_left)}" y2="{sy(view_top)}" stroke="#333" stroke-width="2"/>')
    lines.append(f'<text x="{sx(view_right)}" y="{sy(view_bottom) + 24}" text-anchor="end" font-family="Arial, sans-serif" font-size="12">NUM</text>')
    lines.append(f'<text x="{sx(view_left) - 30}" y="{sy(view_top)}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" transform="rotate(-90 {sx(view_left)-30},{sy(view_top)})">TIME [s]</text>')

    # grid lines
    for i in range(6):
        xx = view_left + (view_right - view_left) * i / 5
        lines.append(f'<line x1="{sx(xx)}" y1="{sy(view_bottom)}" x2="{sx(xx)}" y2="{sy(view_top)}" stroke="#eee" stroke-width="1"/>')
        lines.append(f'<text x="{sx(xx)}" y="{sy(view_bottom) + 18}" text-anchor="middle" font-family="Arial, sans-serif" font-size="10">{xx:.1f}</text>')
    for i in range(6):
        yy = view_bottom + (view_top - view_bottom) * i / 5
        lines.append(f'<line x1="{sx(view_left)}" y1="{sy(yy)}" x2="{sx(view_right)}" y2="{sy(yy)}" stroke="#eee" stroke-width="1"/>')
        lines.append(f'<text x="{sx(view_left) - 8}" y="{sy(yy) + 4}" text-anchor="end" font-family="Arial, sans-serif" font-size="10">{yy:.0f}</text>')

    if bag_poly:
        lines.append(poly_to_svg(bag_poly, fill="#87CEEB", stroke="#1974D2", opacity=0.4))
    if fence_poly:
        pts = " ".join(f"{sx(p['x'])},{sy(p['y'])}" for p in fence_poly)
        lines.append(f'<polygon points="{pts}" fill="none" stroke="#d62728" stroke-width="2" stroke-dasharray="8,6" opacity="0.8"/>')

    # points
    for p in points:
        color = "#999"
        size = 6
        if p in outliers:
            color = "#d62728"
            lines.append(f'<circle cx="{sx(p["x"]) }" cy="{sy(p["y"]) }" r="{size}" fill="{color}" stroke="#000" stroke-width="1"/>')
        else:
            lines.append(f'<circle cx="{sx(p["x"]) }" cy="{sy(p["y"]) }" r="{size}" fill="{color}" opacity="0.8"/>')

    if center is not None:
        lines.append(f'<circle cx="{sx(center["x"]) }" cy="{sy(center["y"]) }" r="8" fill="#d62728" stroke="#fff" stroke-width="2"/>')

    lines.append('</svg>')
    svg_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    source = Path(__file__).resolve().parent / "rollrcoast.csv"
    output = Path(__file__).resolve().parent / "graphs" / "num_time_bagplot.svg"
    points = read_points(source)
    if not points:
        raise SystemExit("No valid NUM/TIME [s] pairs found in rollrcoast.csv.")

    depths = tukey_depth(points)
    depth_threshold = int(median(depths)) if depths else 0
    center_points = [p for p, d in zip(points, depths) if d == max(depths)] if depths else []
    center = None
    if center_points:
        center = {"x": sum(p["x"] for p in center_points) / len(center_points), "y": sum(p["y"] for p in center_points) / len(center_points)}

    bag_points = [p for p, d in zip(points, depths) if d >= depth_threshold]
    bag_poly = convex_hull(bag_points) if len(bag_points) >= 3 else bag_points
    fence_poly = scale_polygon(bag_poly, center, 3.0) if bag_poly and center is not None else []
    outliers = [p for p in points if fence_poly and not point_in_poly(p, fence_poly)]

    build_svg(points, bag_poly, fence_poly, center, outliers, output)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
