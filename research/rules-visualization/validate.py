#!/usr/bin/env python3
"""Structural checks for the isolated prototype pages.

This is not a WCAG conformance test. It checks the invariants the static
prototype relies on so a future edit cannot silently remove the text
equivalent, language metadata, captions or table headers.
"""
from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PAGES = [ROOT / 'prototype' / lang / 'index.html' for lang in ('en', 'fr', 'ar')] + [ROOT / 'prototype' / 'index.html']


class Doc(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.ids: list[str] = []
        self.title = ''
        self.h1 = 0
        self.main = 0
        self.skip = False
        self.captions = 0
        self.scope = 0
        self.svg_titles = 0
        self.svg_desc = 0
        self.script_src = 0
        self.canvas = 0
        self.labels: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if 'id' in attrs: self.ids.append(attrs['id'])
        if tag == 'title': self._in_title = True
        if tag == 'h1': self.h1 += 1
        if tag == 'main': self.main += 1
        if tag == 'caption': self.captions += 1
        if tag == 'th' and attrs.get('scope'): self.scope += 1
        if tag == 'svg' and attrs.get('role') == 'img': self.svg_titles += 1
        if tag == 'desc': self.svg_desc += 1
        if tag == 'script' and attrs.get('src'): self.script_src += 1
        if tag == 'canvas': self.canvas += 1
        if tag == 'a': self.labels.append((attrs.get('href') or '', ''))

    def handle_endtag(self, tag):
        if tag == 'title': self._in_title = False

    def handle_data(self, data):
        if self._in_title: self.title += data
        if self.labels and data.strip(): self.labels[-1] = (self.labels[-1][0], self.labels[-1][1] + data.strip())


def check(page: Path) -> list[str]:
    doc = Doc(); doc.feed(page.read_text(encoding='utf-8'))
    errors: list[str] = []
    tag_map = {tag: attrs for tag, attrs in doc.tags}
    if not doc.title.strip(): errors.append('missing title')
    if doc.h1 != 1: errors.append(f'h1 count {doc.h1}')
    if doc.main != 1: errors.append(f'main count {doc.main}')
    if not any(tag == 'a' and attrs.get('class') == 'skip' and attrs.get('href') == '#main' for tag, attrs in doc.tags):
        errors.append('missing skip link to #main')
    if tag_map.get('main', {}).get('tabindex') != '-1': errors.append('main is not tabindex=-1')
    if page.parent.name in ('en', 'fr', 'ar'):
        if doc.captions < 2: errors.append('expected at least two table captions')
        if doc.scope < 6: errors.append('table headers missing scope')
        if doc.svg_titles < 1 or doc.svg_desc < 1: errors.append('SVG title/desc missing')
    if doc.canvas: errors.append('canvas used')
    if doc.script_src: errors.append('external script')
    if len(doc.ids) != len(set(doc.ids)): errors.append('duplicate IDs')
    html_tag = tag_map.get('html', {})
    if not html_tag.get('lang'): errors.append('missing html lang')
    if html_tag.get('dir') not in ('ltr', 'rtl'): errors.append('missing html dir')
    ids = set(doc.ids)
    for tag, attrs in doc.tags:
        for attr in ('aria-labelledby', 'aria-describedby'):
            for ref in (attrs.get(attr) or '').split():
                if ref and ref not in ids: errors.append(f'{attr} references missing #{ref}')
    for href, label in doc.labels:
        if not label.strip(): errors.append(f'empty link name for {href!r}')
        if href.startswith(('http://', 'https://', 'mailto:')): continue
        if href.startswith('#'): continue
        target = (page.parent / href).resolve()
        if href.endswith('.md') or href.endswith('.l4') or href.endswith('.json') or href.endswith('.dot') or href.endswith('.txt') or href.endswith('.yaml'):
            if not target.exists(): errors.append(f'missing local target {href}')
        elif href.endswith('/') or href.endswith('index.html') or href in ('../', '../../'):
            candidate = target / 'index.html' if target.is_dir() else target
            if not candidate.exists() and not target.exists(): errors.append(f'missing page target {href}')
    # External synthetic citation host is the only allowed external example host.
    for tag, attrs in doc.tags:
        if tag == 'a':
            host = urlparse(attrs.get('href', '')).hostname
            if host and host not in ('example.org',):
                errors.append(f'unexpected external host {host}')
    return errors


def main() -> int:
    all_errors = []
    summary = {}
    for page in PAGES:
        errors = check(page)
        summary[str(page.relative_to(ROOT))] = {'errors': errors}
        all_errors.extend(f'{page.relative_to(ROOT)}: {error}' for error in errors)
    print(json.dumps({'pages': len(PAGES), 'errors': all_errors}, indent=2))
    return 1 if all_errors else 0


if __name__ == '__main__':
    sys.exit(main())
