#!/usr/bin/env python3
"""ebay_parse6.py — muestra HTML crudo alrededor del primer link itm."""
import re

resp = open("/tmp/ebay_search2.html").read()
m = re.search(r'href="(https://www\.ebay\.com/itm/\d+)[^"]*"', resp)
if m:
    s = max(0, m.start() - 500)
    e = min(len(resp), m.start() + 2500)
    print(resp[s:e])
else:
    print("sin links itm")
