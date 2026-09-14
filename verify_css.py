#!/usr/bin/env python3
"""Verify CSS class/ID coverage for an HTML artifact against its stylesheet.

Usage: python3 verify_css.py <index.html> <style.css>

Checks that every class and ID used in the HTML has a matching selector
in the CSS. Reports unstyled classes (likely CSS truncation) and
IDs that are JS-only (expected, not a problem).

JS-only IDs are ones commonly bound by JavaScript (cart bars, product
grids, filter tabs, modals, etc.). Add new ones to the JS_ONLY_IDS set
as your artifact uses them.
"""
import re, sys

JS_ONLY_IDS = frozenset([
    # Cart / checkout
    'cartBar', 'cartItems', 'cartEmpty', 'cartTotal', 'cartCount',
    'clearCart', 'checkoutBtn',
    # Product grid + filters
    'productsGrid', 'noResults', 'filterTabs', 'offersTrack',
    # Modals
    'orderModal', 'modalTitle', 'modalBody', 'modalClose',
    # Sections (anchor targets - not styled, just jumped to)
    'home', 'about', 'services', 'products', 'testimonials', 'contact',
    # misc JS-bound
    'mapPlaceholder', 'productSearch', 'productSearchBtn', 'searchResults',
    'replyOrderId', 'replyMsg', 'replySend', 'replyCancel',
    'pName', 'pCategory', 'pPrice', 'pDesc', 'pIcon',
    'pSave', 'pCancel',
    'ordersBody', 'productList', 'productAdd',
])

def extract_html_refs(path):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    classes = set()
    for m in re.finditer(r'class="([^"]+)"', html):
        for c in m.group(1).split():
            classes.add(c.strip())
    ids = set()
    for m in re.finditer(r'id="([^"]+)"', html):
        ids.add(m.group(1).strip())
    return classes, ids

def extract_css_selectors(path):
    with open(path, 'r', encoding='utf-8') as f:
        css = f.read()
    selectors = set()
    for m in re.finditer(r'\.([a-zA-Z][\w-]*)', css):
        selectors.add(m.group(1))
    for m in re.finditer(r'#([a-zA-Z][\w-]*)', css):
        selectors.add(m.group(1))
    return selectors

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <index.html> <style.css>")
        sys.exit(1)
    html_path, css_path = sys.argv[1], sys.argv[2]
    html_classes, html_ids = extract_html_refs(html_path)
    css_selectors = extract_css_selectors(css_path)
    missing_classes = sorted(c for c in html_classes if c not in css_selectors)
    missing_ids = sorted(i for i in html_ids if i not in css_selectors and i not in JS_ONLY_IDS)
    print(f"HTML classes: {len(html_classes)} | CSS selectors: {len(css_selectors)}")
    print(f"HTML IDs: {len(html_ids)} | JS-only (expected): {len(html_ids & JS_ONLY_IDS)}")
    if missing_classes:
        print(f"\nMISSING CSS CLASSES ({len(missing_classes)}):")
        for c in missing_classes:
            print(f"  .{c}")
    else:
        print("\u2713 All HTML classes covered in CSS")
    if missing_ids:
        print(f"\nMISSING CSS IDS ({len(missing_ids)}) - these have no style rule:")
        for i in missing_ids:
            print(f"  #{i}")
    else:
        print("\u2713 All non-JS HTML IDs covered in CSS")
    if missing_classes or missing_ids:
        sys.exit(1)

if __name__ == '__main__':
    main()
