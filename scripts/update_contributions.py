#!/usr/bin/env python3
"""Regenerate assets/contribution-grid.svg from the real GitHub
contribution calendar. No token needed: the contributions page is public.
Run: python3 scripts/update_contributions.py
"""
import json, re, sys, urllib.request
from datetime import date
from pathlib import Path

USER = "LeebSite"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "contribution-grid.svg"

COLOR = {"0": "#161b22", "1": "#2ea88a", "2": "#4ade80", "3": "#7ee787", "4": "#a7f3c0"}
DIM   = {"0": "#161b22", "1": "#0e2e22", "2": "#0e2e22", "3": "#123324", "4": "#123324"}

def fetch():
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")

def parse(html):
    pat = re.compile(
        r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)".*?'
        r'<tool-tip[^>]*>(.*?)</tool-tip>', re.S)
    levels, counts = {}, {}
    for d, lvl, tip in pat.findall(html):
        levels[d] = lvl
        m = re.search(r"(\d+) contribution", tip)
        counts[d] = int(m.group(1)) if m else 0
    if len(levels) < 300:
        raise SystemExit(f"parse failed: only {len(levels)} days found")
    return levels, counts

def build(levels, counts):
    start = date.fromisoformat(min(levels))
    total = sum(counts.values())
    active = sum(1 for v in levels.values() if v != "0")
    peak_d, peak_c = max(counts.items(), key=lambda x: x[1])
    peak = peak_d[5:].replace("-", " ")  # not used for label, kept simple
    # label: "Sep 9 · 35"
    from datetime import datetime as dt
    peak_label = dt.fromisoformat(peak_d).strftime("%b %-d")
    cell, step, x0, y0 = 14, 18, 52, 48
    rects = []
    for d_str, lvl in sorted(levels.items()):
        d = date.fromisoformat(d_str)
        off = (d - start).days
        col, row = off // 7, off % 7
        x, y = x0 + col * step, y0 + row * step
        if lvl == "0":
            rects.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3.5" fill="#161b22"/>')
        else:
            t = round(0.03 + (col / 52) * 0.70, 3)
            rects.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3.5" fill="{COLOR[lvl]}" opacity="0.25">'
                f'<animate attributeName="opacity" values="0.25;1;1;0.25" keyTimes="0;{t};0.92;1" dur="9s" repeatCount="indefinite"/>'
                f'<animate attributeName="fill" values="{DIM[lvl]};{COLOR[lvl]};{COLOR[lvl]};{DIM[lvl]}" keyTimes="0;{t};0.92;1" dur="9s" repeatCount="indefinite"/>'
                f'</rect>')
    W, H = x0 + 53 * step + 20, y0 + 7 * step + 52
    months, seen = [], set()
    for d_str in sorted(levels):
        d = date.fromisoformat(d_str)
        if d.day <= 7 and d.strftime("%b %Y") not in seen:
            seen.add(d.strftime("%b %Y"))
            col = (d - start).days // 7
            months.append(f'<text x="{x0 + col * step}" y="34" font-size="12" fill="#8b949e" class="mono">{d.strftime("%b")}</text>')
    weekdays = "".join(f'<text x="14" y="{y0 + r * step + 11}" font-size="11" fill="#6e7681" class="mono">{lbl}</text>'
                       for r, lbl in [(1, "Mon"), (3, "Wed"), (5, "Fri")])
    ball_y = y0 + 3 * step + 7
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contribution grid with a light orb sweeping left to right">
<defs>
<style>.mono{{font-family:"JetBrains Mono",Consolas,monospace;}}</style>
<filter id="glow" x="-120%" y="-120%" width="340%" height="340%"><feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7ee787" stop-opacity="0.28"/><stop offset="0.5" stop-color="#7ee787" stop-opacity="0.05"/><stop offset="1" stop-color="#7ee787" stop-opacity="0.28"/></linearGradient>
</defs>
<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="14" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>
<text x="20" y="22" font-size="13" fill="#8b949e" class="mono">~/contributions — {total} total · {active} active days · peak {peak_label} · {peak_c}</text>
{''.join(months)}
{weekdays}
{''.join(rects)}
<rect x="0" y="40" width="46" height="142" rx="20" fill="url(#beam)" opacity="0">
<animate attributeName="x" values="{x0-23};{x0+53*step-23};{x0+53*step-23};{x0-23}" keyTimes="0;0.72;0.92;1" dur="9s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0;0.9;0.9;0" keyTimes="0;0.05;0.92;1" dur="9s" repeatCount="indefinite"/>
</rect>
<g filter="url(#glow)">
<circle r="9" fill="#ffffff" opacity="0">
<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.03;0.92;1" dur="9s" repeatCount="indefinite"/>
<animateMotion dur="9s" repeatCount="indefinite" path="M {x0} {ball_y} L {x0+53*step} {ball_y}" keyPoints="0;0.78;0.92;1" keyTimes="0;0.72;0.92;1" calcMode="linear"/>
</circle>
<circle r="5" fill="#7ee787" opacity="0">
<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.03;0.92;1" dur="9s" repeatCount="indefinite"/>
<animateMotion dur="9s" repeatCount="indefinite" path="M {x0} {ball_y} L {x0+53*step} {ball_y}" keyPoints="0;0.78;0.92;1" keyTimes="0;0.72;0.92;1" calcMode="linear"/>
</circle>
</g>
<text x="20" y="{H-12}" font-size="11" fill="#6e7681" class="mono">Less</text>
<rect x="58" y="{H-22}" width="11" height="11" rx="3" fill="#161b22" stroke="#30363d"/><rect x="73" y="{H-22}" width="11" height="11" rx="3" fill="#2ea88a"/><rect x="88" y="{H-22}" width="11" height="11" rx="3" fill="#4ade80"/><rect x="103" y="{H-22}" width="11" height="11" rx="3" fill="#7ee787"/><rect x="118" y="{H-22}" width="11" height="11" rx="3" fill="#a7f3c0"/>
<text x="136" y="{H-12}" font-size="11" fill="#6e7681" class="mono">More</text>
</svg>'''

def main():
    levels, counts = parse(fetch())
    svg = build(levels, counts)
    old = OUT.read_text() if OUT.exists() else ""
    if svg == old:
        print("no change")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg)
    print(f"updated {OUT}: {sum(counts.values())} total, "
          f"{sum(1 for v in levels.values() if v != '0')} active days, "
          f"{min(levels)} to {max(levels)}")

if __name__ == "__main__":
    main()
