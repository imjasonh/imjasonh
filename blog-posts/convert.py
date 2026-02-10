#!/usr/bin/env python3
"""Convert a blog post URL to clean Markdown.

Usage: python3 convert.py <url> [output.md]

If output.md is omitted, derives filename from the URL slug.
Supports Chainguard (chainguard.dev) and Red Hat Developer
(developers.redhat.com) blog posts, with a generic fallback
for other sites.

Requirements: pip install beautifulsoup4 markdownify
"""

import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

# Invisible Unicode characters to strip
INVISIBLE_RE = re.compile('[\u200b\u200c\u200d\u200e\u200f\u2060\ufeff\u00ad]')


class BlogConverter(MarkdownConverter):
    """MarkdownConverter with image URL resolution for Next.js sites."""

    def convert_img(self, el, text, parent_tags=None):
        alt = el.get('alt', '') or ''
        src = el.get('src', '') or ''
        # Resolve /_next/image proxied URLs to the original
        if '/_next/image' in src:
            src = self._extract_next_image_url(src) or src
        if not src or '/_next/image' in src:
            srcset = el.get('srcset', '')
            for part in srcset.split(','):
                part = part.strip().split(' ')[0]
                if '/_next/image' in part:
                    resolved = self._extract_next_image_url(part)
                    if resolved:
                        src = resolved
                        break
                elif part.startswith('http'):
                    src = part
                    break
        return f'![{alt}]({src})'

    @staticmethod
    def _extract_next_image_url(url):
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        return params['url'][0] if 'url' in params else None


def _fetch(url):
    """Fetch URL with curl, return HTML string."""
    result = subprocess.run(
        ['curl', '-sL', url], capture_output=True, text=True, timeout=30,
    )
    return result.stdout


def _to_markdown(soup_element):
    """Convert a BeautifulSoup element to Markdown."""
    return BlogConverter(
        heading_style='ATX', bullets='-', strong_em_symbol='*',
        code_language='', strip=['script', 'style', 'nav', 'footer'],
    ).convert_soup(soup_element)


def _clean(md):
    """Strip invisible chars, trailing whitespace, and excess blank lines."""
    md = INVISIBLE_RE.sub('', md)
    md = '\n'.join(line.rstrip() for line in md.split('\n'))
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md.strip()


def _make_relative_links_absolute(md, base):
    """Turn bare relative markdown links into absolute URLs."""
    return re.sub(r'\]\((/[^)]+)\)', rf']({base}\1)', md)


def _build_doc(title, author, date, body):
    """Assemble the final Markdown document."""
    parts = [f'# {title}', '']
    if author:
        parts += [f'**{author}**', '']
    if date:
        parts += [f'*{date}*', '']
    parts += ['---', '', body, '']
    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Site-specific extractors
# ---------------------------------------------------------------------------

def convert_chainguard(url):
    soup = BeautifulSoup(_fetch(url), 'html.parser')

    title = (soup.find('h1').get_text(strip=True)
             if soup.find('h1') else '')

    author = date = ''
    container = soup.find(
        'div', class_=lambda c: c and 'container' in c and 'max-w' in c)
    if container:
        for child in container.children:
            if not (hasattr(child, 'get_text') and hasattr(child, 'get')):
                continue
            if 'richtext' in ' '.join(child.get('class', [])):
                break
            t = child.get_text(strip=True)
            if t and title in t:
                lines = [l.strip() for l in
                         child.get_text('\n', strip=True).split('\n')
                         if l.strip()]
                for i, line in enumerate(lines):
                    if re.match(r'(?:January|February|March|April|May|June|'
                                r'July|August|September|October|November|'
                                r'December)\s+\d', line):
                        date = line
                    if line == title and i + 1 < len(lines):
                        author = lines[i + 1]

    richtext = soup.find('div', class_=lambda c: c and 'richtext' in c)
    if not richtext:
        sys.exit(f'ERROR: No richtext div found for {url}')

    body = _clean(_to_markdown(richtext))
    return _build_doc(title, author, date, body)


def convert_redhat(url):
    soup = BeautifulSoup(_fetch(url), 'html.parser')

    h1 = soup.find('h1', class_='article-info-title') or soup.find('h1')
    title = h1.get_text(strip=True) if h1 else ''

    date_div = soup.find('div', class_='publish-date')
    date = date_div.get_text(strip=True) if date_div else ''

    author_div = soup.find(
        'div', class_=lambda c: c and 'main-author' in c)
    author = author_div.get_text(strip=True) if author_div else ''

    content = (soup.find('div',
                         class_=lambda c: c and 'article-content' in c)
               or soup.find('main') or soup.find('body'))

    # Strip sidebar / footer cruft
    for heading in content.find_all(['h2', 'h3']):
        if heading.get_text(strip=True) in ('Related Posts', 'Recent Posts'):
            for sib in list(heading.find_next_siblings()):
                sib.decompose()
            heading.decompose()
    for el in content.find_all(True):
        if 'Last updated' in el.get_text():
            el.decompose()

    body = _clean(_to_markdown(content))
    body = _make_relative_links_absolute(body, 'https://developers.redhat.com')
    return _build_doc(title, author, date, body)


def convert_generic(url):
    """Best-effort conversion for unknown sites."""
    soup = BeautifulSoup(_fetch(url), 'html.parser')

    h1 = soup.find('h1')
    title = h1.get_text(strip=True) if h1 else ''

    content = (soup.find('article')
               or soup.find('main')
               or soup.find('div', role='main')
               or soup.find('body'))

    body = _clean(_to_markdown(content))
    parsed = urllib.parse.urlparse(url)
    body = _make_relative_links_absolute(body,
                                         f'{parsed.scheme}://{parsed.netloc}')
    return _build_doc(title, '', '', body)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def output_path_from_url(url):
    """Derive a .md filename from the URL slug."""
    slug = url.rstrip('/').rsplit('/', 1)[-1]
    return slug + '.md'


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)

    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else output_path_from_url(url)

    if 'chainguard.dev' in url:
        md = convert_chainguard(url)
    elif 'developers.redhat.com' in url:
        md = convert_redhat(url)
    else:
        md = convert_generic(url)

    Path(out).write_text(md)
    print(f'Wrote {out} ({len(md)} bytes)')


if __name__ == '__main__':
    main()
