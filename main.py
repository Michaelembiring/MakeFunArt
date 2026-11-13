#!/usr/bin/env python3
"""Neon Archipelago — deterministic generative art for make.fun coolest-art-01.

Running this program writes one SVG artwork, `art.svg`, into the output
directory (MAKEFUN_OUTPUT if set, else /output when present, else ./output).
The picture is fully deterministic: a fixed seed drives every choice, so two
runs on the same machine produce byte-identical output. Standard library only.

Scene: a ringed sun sinks over layered island ridgelines while seeded
flow-field ribbons — currents of coral, gold and teal — sweep the sea in
front of it, under a field of stars.
"""

import math
import os
import random

W, H = 1600, 1000
SEED = 20261113

SKY_TOP = "#0a0e27"
SKY_MID = "#173a5e"
SKY_LOW = "#c65d21"
SUN_CORE = "#ffd98a"
SUN_RING = "#ff9e57"
SEA_DEEP = "#081226"
RIDGE_COLORS = ["#123a5c", "#0f4c5c", "#14655f", "#1b7a6e"]
RIBBON_COLORS = ["#ff7847", "#ffb347", "#37e0c8", "#ff5d8f", "#ffe066", "#7bdff2"]


def ridge_path(base_y, amp, phase, rng):
    """One island ridgeline as a smooth summed-sine silhouette path."""
    waves = [(rng.uniform(0.6, 1.4), rng.uniform(0.0, 6.28), rng.uniform(0.25, 0.6))
             for _ in range(4)]
    pts = []
    for x in range(-20, W + 21, 20):
        y = base_y
        for freq, ph, share in waves:
            y += math.sin(x / (260.0 * freq) + phase + ph) * amp * share
        pts.append((x, y))
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} "
    for x, y in pts[1:]:
        d += f"L {x:.1f} {y:.1f} "
    d += f"L {W + 20} {H} L -20 {H} Z"
    return d


def flow_ribbon(y0, drift, color, width, opacity, rng):
    """A long bezier current ribbon sweeping left to right."""
    c1x, c1y = rng.uniform(300, 500), y0 + rng.uniform(-90, 90) + drift
    c2x, c2y = rng.uniform(1000, 1250), y0 + rng.uniform(-90, 90) - drift
    endy = y0 + rng.uniform(-50, 50)
    return (f'<path d="M -20 {y0:.1f} C {c1x:.1f} {c1y:.1f}, '
            f'{c2x:.1f} {c2y:.1f}, {W + 20} {endy:.1f}" fill="none" '
            f'stroke="{color}" stroke-width="{width:.1f}" '
            f'stroke-opacity="{opacity:.2f}" stroke-linecap="round"/>')


def build_svg():
    rng = random.Random(SEED)
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
                 f'viewBox="0 0 {W} {H}">')
    parts.append("<defs>"
                 '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
                 f'<stop offset="0" stop-color="{SKY_TOP}"/>'
                 f'<stop offset="0.55" stop-color="{SKY_MID}"/>'
                 f'<stop offset="1" stop-color="{SKY_LOW}"/>'
                 "</linearGradient>"
                 '<radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">'
                 f'<stop offset="0" stop-color="{SUN_CORE}" stop-opacity="0.85"/>'
                 f'<stop offset="1" stop-color="{SUN_CORE}" stop-opacity="0"/>'
                 "</radialGradient>"
                 "</defs>")
    parts.append(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')

    # Stars over the upper sky.
    for _ in range(240):
        x = rng.uniform(0, W)
        y = rng.uniform(0, 430) * rng.uniform(0.4, 1.0)
        r = rng.uniform(0.6, 2.1)
        o = rng.uniform(0.25, 0.95)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" '
                     f'fill="#ffffff" opacity="{o:.2f}"/>')

    # Ringed sun with a soft halo.
    sun_x, sun_y = 1080, 400
    parts.append(f'<circle cx="{sun_x}" cy="{sun_y}" r="330" fill="url(#glow)"/>')
    for i, rr in enumerate((196, 168, 140)):
        parts.append(f'<circle cx="{sun_x}" cy="{sun_y}" r="{rr}" fill="none" '
                     f'stroke="{SUN_RING}" stroke-width="{3 + i * 2}" '
                     f'opacity="{0.35 + i * 0.18:.2f}"/>')
    parts.append(f'<circle cx="{sun_x}" cy="{sun_y}" r="112" fill="{SUN_CORE}"/>')

    # Island ridgelines, far to near.
    base = 470
    for i, color in enumerate(RIDGE_COLORS):
        d = ridge_path(base + i * 68, 34 + i * 10, i * 1.7, rng)
        parts.append(f'<path d="{d}" fill="{color}" opacity="{0.82 + i * 0.05:.2f}"/>')

    # Sea base.
    parts.append(f'<rect y="735" width="{W}" height="{H - 735}" fill="{SEA_DEEP}"/>')

    # Flow-field ribbons: the currents in front of the islands.
    for i in range(64):
        y0 = rng.uniform(700, 985)
        color = RIBBON_COLORS[i % len(RIBBON_COLORS)]
        parts.append(flow_ribbon(y0, rng.uniform(10, 60), color,
                                 rng.uniform(1.2, 4.6), rng.uniform(0.25, 0.8), rng))

    # Sun glitter: short dashes of light scattered on the water under the sun.
    for _ in range(90):
        x = sun_x + rng.gauss(0, 150)
        y = rng.uniform(745, 985)
        ln = rng.uniform(8, 46) * (1 - (y - 745) / 320)
        if ln <= 2:
            continue
        parts.append(f'<line x1="{x - ln / 2:.1f}" y1="{y:.1f}" x2="{x + ln / 2:.1f}" '
                     f'y2="{y:.1f}" stroke="{SUN_CORE}" stroke-width="2.4" '
                     f'opacity="{rng.uniform(0.3, 0.85):.2f}" stroke-linecap="round"/>')

    # Birds crossing the sun, drawn as paired arcs.
    for i in range(7):
        bx = 300 + i * 74 + rng.uniform(-14, 14)
        by = 210 + (i % 3) * 44 + rng.uniform(-10, 10)
        s = rng.uniform(9, 15)
        parts.append(f'<path d="M {bx - s:.1f} {by:.1f} Q {bx - s / 2:.1f} '
                     f'{by - s * 0.7:.1f} {bx:.1f} {by:.1f} Q {bx + s / 2:.1f} '
                     f'{by - s * 0.7:.1f} {bx + s:.1f} {by:.1f}" fill="none" '
                     f'stroke="#0a0e27" stroke-width="2.6" stroke-linecap="round"/>')

    # Soft vignette to seat the composition.
    parts.append("<defs>"
                 '<radialGradient id="vig" cx="0.5" cy="0.46" r="0.85">'
                 '<stop offset="0.72" stop-color="#000000" stop-opacity="0"/>'
                 '<stop offset="1" stop-color="#000000" stop-opacity="0.38"/>'
                 "</radialGradient>"
                 "</defs>")
    parts.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def output_dir():
    for cand in (os.environ.get("MAKEFUN_OUTPUT"), "/output",
                 os.path.join(os.getcwd(), "output")):
        if cand and os.path.isdir(cand) and os.access(cand, os.W_OK):
            return cand
    d = os.path.join(os.getcwd(), "output")
    os.makedirs(d, exist_ok=True)
    return d


def main():
    svg = build_svg()
    path = os.path.join(output_dir(), "art.svg")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"WROTE art.svg ({len(svg.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    main()
