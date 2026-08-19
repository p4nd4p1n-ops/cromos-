#!/usr/bin/env python3
"""Extract any embedded sales data from the saved card page."""
import re

with open("/root/comc-data/harper-ajax.html") as f:
    html = f.read()

print("=== Price patterns near 'sale' text ===")
for m in re.finditer(r"(?:price|sale|sold|cost|amount)[^0-9]*?(\$?\d+\.\d{2})", html[:50000], re.I):
    ctx = html[max(0,m.start()-50):m.end()+50]
    print("{}: ...{}...".format(m.group(1), ctx.replace("\n", " ")[:150]))

print("\n=== Script blocks with sales/sparkline ===")
for m in re.finditer(r"<script[^>]*>(.{50,800}?)</script>", html[:100000], re.DOTALL):
    script = m.group(1)
    if re.search(r"(?:sparkline|sale|chart|historical)", script, re.I):
        print("SCRIPT:", script[:400])
        print("---")

print("\n=== '4 year sales' context ===")
idx = html.find("4 year sales")
if idx >= 0:
    print(html[idx-200:idx+500].replace("\n", " "))

print("\n=== 'sparkline' context ===")
for m in re.finditer(r"sparkline[^<>]{0,200}", html, re.I):
    print(m.group())

print("\n=== Any '/Chart' or '/api/' URLs ===")
for m in re.finditer(r'(?:/[Cc]hart[^"\'\s]*|/api/[^"\'\s]*)', html):
    url = m.group()
    if len(url) > 5:
        print(url)
