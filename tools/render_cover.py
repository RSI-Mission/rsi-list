#!/usr/bin/env python3
"""Render the README images from the site itself.

    python3 tools/render_cover.py                    # from https://rsi-list.com
    python3 tools/render_cover.py http://localhost:8000/

Writes assets/cover.jpg (the hero) and assets/takeoff.png (the chart), both at 2x.
The hero is film grain over a gradient, which PNG stores badly (1.7MB); JPEG at q88
is a fifth of a megabyte and indistinguishable. The chart is thin lines on black, so PNG.
Needs playwright with chromium:  pip install playwright && playwright install chromium
"""
import os, sys
from PIL import Image
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://rsi-list.com/"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=2)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(9000)          # let the fonts settle and the chart finish drawing
    for selector, name in ((".hero", "cover.jpg"), ("#tk-chart", "takeoff.png")):
        el = page.query_selector(selector)
        if el is None:
            sys.exit(f"{selector} not found on {URL}")
        path = os.path.join(OUT, name)
        if name.endswith(".jpg"):
            tmp = path + ".png"
            el.screenshot(path=tmp)
            Image.open(tmp).convert("RGB").save(path, quality=88, optimize=True, progressive=True)
            os.remove(tmp)
        else:
            el.screenshot(path=path)
        box = el.bounding_box()
        print(f"{name}: {int(box['width'])}x{int(box['height'])} css px -> {path}")
    browser.close()
