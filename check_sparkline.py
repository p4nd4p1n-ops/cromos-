#!/usr/bin/env python3
"""Final check: embedded sales data in the sparklines section."""
import re

with open("/root/comc-data/harper-ajax.html") as f:
    html = f.read()

idx = html.find("sparklines")
if idx >= 0:
    section = html[max(0,idx-200):idx+2000]
    for m in re.finditer(r"<(script|div|span|h5|h6|a)[^>]*>(.*?)</\1>", section, re.DOTALL):
        tag = m.group(1)
        content = m.group(2).strip()
        if len(content) > 10:
            print("<{}>: {}".format(tag, content[:200]))
    
    for m in re.finditer(r'(?:data-\w+|value|id)=[\"\']([^\"\']{5,})[\"\']', section):
        print("ATTR: {}".format(m.group()[:150]))

# Also look for any inline JSON data in script blocks near sparkline
for m in re.finditer(r"<script[^>]*>([\s\S]{20,500}?)</script>", section, re.DOTALL):
    print("SCRIPT:", m.group(1)[:300])

# Check if there's a separate sparkline data URL anywhere in the page
for m in re.finditer(r"(?:sparkline|spark|chart|history|sales)[^\"\'\s]*\.(?:json|js|ashx|aspx)[^\"\'\s]*", html, re.I):
    print("DATA URL:", m.group())
