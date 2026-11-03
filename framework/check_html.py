#!/usr/bin/env python3
"""Static accessibility lint for generated HTML.

This checks structure, not conformance. It cannot decide meaning, translation
quality, or whether a page works with assistive technology.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys

HEADINGS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
EXTERNAL_SCHEMES = ('http', 'https', 'mailto', 'tel', 'data')


class PageChecker(HTMLParser):
    def __init__(self, path: Path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.errors: list[str] = []
        self.doc_lang = None
        self.doc_dir = None
        self.in_title = False
        self.title_parts: list[str] = []
        self.main_count = 0
        self.main_tabindex = None
        self.heading_levels: list[int] = []
        self.table_count = 0
        self.caption_count = 0
        self.th_without_scope = 0
        self.ids: set[str] = set()
        self.open_links: list[dict] = []
        self.links: list[dict] = []
        self.skip_link_count = 0
        self.foreign_without_direction = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        element_id = attributes.get('id')
        if element_id:
            if element_id in self.ids:
                self.errors.append(f'duplicate id: {element_id}')
            self.ids.add(element_id)

        if tag == 'html':
            self.doc_lang = attributes.get('lang')
            self.doc_dir = attributes.get('dir')
        if tag == 'title':
            self.in_title = True
        if tag == 'main':
            self.main_count += 1
            self.main_tabindex = attributes.get('tabindex')
        if tag in HEADINGS:
            self.heading_levels.append(int(tag[1]))
        if tag == 'table':
            self.table_count += 1
        if tag == 'caption':
            self.caption_count += 1
        if tag == 'th' and attributes.get('scope') not in ('row', 'col'):
            self.th_without_scope += 1
        if tag == 'a':
            href = attributes.get('href')
            self.open_links.append({
                'href': href,
                'text': '',
                'aria_label': attributes.get('aria-label'),
            })
            if href == '#main':
                self.skip_link_count += 1
        lang = attributes.get('lang')
        if (tag not in ('html', 'link', 'meta') and lang
                and lang != self.doc_lang and not attributes.get('dir')):
            self.foreign_without_direction += 1

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'a' and self.open_links:
            self.links.append(self.open_links.pop())

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)
        if self.open_links:
            self.open_links[-1]['text'] += data

    def check_local_link(self, href: str):
        parts = urlsplit(href)
        if parts.scheme:
            if parts.scheme not in EXTERNAL_SCHEMES:
                self.errors.append(f'unexpected link scheme: {href}')
            return
        path = unquote(parts.path)
        fragment = unquote(parts.fragment)
        if not path:
            if fragment and fragment not in self.ids:
                self.errors.append(f'fragment target not found: {href}')
            return
        target = (self.path.parent / path).resolve()
        if path.endswith('/') or target.is_dir():
            target = target / 'index.html'
        if not target.is_file():
            self.errors.append(f'broken local link: {href}')

    def finish(self):
        if not self.doc_lang or self.doc_dir not in ('ltr', 'rtl'):
            self.errors.append('html needs lang and ltr/rtl dir')
        if self.main_count != 1:
            self.errors.append(f'expected one main landmark, found {self.main_count}')
        if self.main_tabindex != '-1':
            self.errors.append('main landmark needs tabindex="-1" for the skip link')
        if not self.skip_link_count:
            self.errors.append('missing skip link to #main')
        if self.heading_levels.count(1) != 1:
            self.errors.append(f'expected one h1, found {self.heading_levels.count(1)}')
        previous = 0
        for level in self.heading_levels:
            if previous and level > previous + 1:
                self.errors.append(f'heading level jumps from h{previous} to h{level}')
            previous = level
        if self.table_count != self.caption_count:
            self.errors.append('every table needs a caption')
        if self.th_without_scope:
            self.errors.append(f'{self.th_without_scope} th element(s) without scope')
        if self.foreign_without_direction:
            self.errors.append(
                f'{self.foreign_without_direction} foreign-language element(s) without dir')
        for link in self.links:
            name = (link['text'] or link['aria_label'] or '').strip()
            if not name:
                self.errors.append(f'link without accessible name: {link["href"]}')
            if link['href']:
                self.check_local_link(link['href'])
        if self.open_links:
            self.errors.append('unclosed link element')


def main() -> int:
    dist = Path('dist')
    pages = sorted(dist.rglob('*.html'))
    errors: list[str] = []
    titles: dict[str, list[str]] = {}
    for page_path in pages:
        checker = PageChecker(page_path.resolve())
        checker.feed(page_path.read_text(encoding='utf-8'))
        checker.close()
        checker.finish()
        relative = page_path.relative_to(dist)
        errors.extend(f'{relative}: {error}' for error in checker.errors)
        title = ' '.join(checker.title_parts).strip()
        if not title:
            errors.append(f'{relative}: missing document title')
        titles.setdefault(title, []).append(str(relative))
    for title, files in titles.items():
        if len(files) > 1:
            errors.append(f'duplicate document title {title!r}: {", ".join(files)}')
    if errors:
        print('\n'.join(errors))
        return 1
    print(f'HTML accessibility structure checks: passed ({len(pages)} pages)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
