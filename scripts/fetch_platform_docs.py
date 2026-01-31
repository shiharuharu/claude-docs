#!/usr/bin/env python3
"""
Download Anthropic Claude Platform documentation from sitemap.xml.

Features:
- Discovers documentation pages from sitemap.xml (always up-to-date)
- Downloads all English .md files
- Preserves directory structure
- Fixes relative links within downloaded files
- Extracts real titles from markdown content
- Generates index.md with proper categorization

Usage:
    python scripts/fetch_platform_docs.py
"""

import re
import os
import time
import shutil
import random
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse


BASE_URL = "https://platform.claude.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
OUTPUT_DIR = "docs/platform"
INDEX_FILE = "index.md"
REQUEST_DELAY = 0.1
MAX_RETRIES = 3
RETRY_DELAY = 2
MAX_RETRY_DELAY = 30


def create_request(url: str) -> urllib.request.Request:
    """Create a request with proper headers."""
    return urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (compatible; DocsDownloader/2.0)',
            'Cache-Control': 'no-cache',
        }
    )


def download_content(url: str) -> str | None:
    """Download content from a URL with exponential backoff retry."""
    for attempt in range(MAX_RETRIES):
        try:
            req = create_request(url)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8')
                if content.strip().startswith('<!DOCTYPE html>'):
                    return None
                if not validate_markdown_content(content):
                    return None
                return content
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = int(e.headers.get('Retry-After', 60))
                print(f"  Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            if e.code == 404:
                return None
            if attempt == MAX_RETRIES - 1:
                print(f"  HTTP Error {e.code}: {url}")
            delay = min(RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
            time.sleep(delay * random.uniform(0.5, 1.0))
        except urllib.error.URLError as e:
            if attempt == MAX_RETRIES - 1:
                print(f"  URL Error: {e.reason}")
            delay = min(RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
            time.sleep(delay * random.uniform(0.5, 1.0))
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                print(f"  Error: {e}")
            delay = min(RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
            time.sleep(delay * random.uniform(0.5, 1.0))
    return None


def validate_markdown_content(content: str) -> bool:
    """Validate that content is proper markdown."""
    if not content or len(content.strip()) < 50:
        return False
    markdown_indicators = ['# ', '## ', '### ', '```', '- ', '* ', '1. ', '[', '**', '> ']
    lines = content.split('\n')[:50]
    indicator_count = sum(1 for line in lines for ind in markdown_indicators if ind in line)
    return indicator_count >= 3


def discover_pages_from_sitemap() -> list[str]:
    """Discover all English documentation pages from sitemap.xml."""
    print(f"Fetching sitemap from {SITEMAP_URL}...")
    try:
        req = create_request(SITEMAP_URL)
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()
        root = ET.fromstring(content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = []
        for url_elem in root.findall('.//ns:url', namespace):
            loc_elem = url_elem.find('ns:loc', namespace)
            if loc_elem is not None and loc_elem.text:
                urls.append(loc_elem.text)
        if not urls:
            for loc_elem in root.findall('.//loc'):
                if loc_elem.text:
                    urls.append(loc_elem.text)
        english_docs = [url for url in urls if '/docs/en/' in url and url != f"{BASE_URL}/docs/en"]
        print(f"Found {len(english_docs)} English documentation pages")
        return english_docs
    except Exception as e:
        print(f"Failed to fetch sitemap: {e}")
        return []


def url_to_local_path(url: str, output_dir: Path) -> Path:
    """Convert a URL to a local file path."""
    parsed = urlparse(url)
    # Extract path after /docs/en/
    path = parsed.path.replace('/docs/en/', '')
    if not path.endswith('.md'):
        path += '.md'
    return output_dir / path


def fix_relative_links(content: str, current_file_path: Path, output_dir: Path) -> str:
    """Fix links in markdown content to work with local file structure."""
    def replace_link(match):
        link_text = match.group(1)
        url = match.group(2)
        if not url.startswith('https://platform.claude.com/docs/'):
            return match.group(0)
        target_path = url_to_local_path(url, output_dir)
        try:
            current_dir = current_file_path.parent
            rel_path = os.path.relpath(target_path, current_dir)
            return f'[{link_text}]({rel_path})'
        except ValueError:
            return match.group(0)
    pattern = r'\[([^\]]+)\]\((https://platform\.claude\.com/docs/[^)]+)\)'
    return re.sub(pattern, replace_link, content)


def extract_title_and_description(content: str) -> tuple[str | None, str | None]:
    """Extract the title from the first H1 heading and the description below it.

    Expected formats:
        Format 1 (plain text):
            # Title

            Description text (one line)

            ---

        Format 2 (blockquote):
            # Title

            > Description text (one line)

            Content...
    """
    lines = content.split('\n')
    title = None
    description = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('# '):
            title = stripped[2:].strip()
            # Look for description in the next non-empty lines (before --- or next heading)
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if next_line == '':
                    continue
                if next_line.startswith('---'):
                    break
                if next_line.startswith('## ') or next_line.startswith('# '):
                    break
                # Handle blockquote format: "> Description"
                if next_line.startswith('> '):
                    description = next_line[2:].strip()
                else:
                    description = next_line
                break
            break

    return title, description


def download_and_save_file(url: str, output_dir: Path) -> tuple[bool, str | None, str | None]:
    """Download a single file and save it.

    Returns:
        tuple: (success, title, description)
    """
    md_url = url + '.md' if not url.endswith('.md') else url
    local_path = url_to_local_path(url, output_dir)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    content = download_content(md_url)
    if content is None:
        return False, None, None
    title, description = extract_title_and_description(content)
    content = fix_relative_links(content, local_path, output_dir)
    local_path.write_text(content, encoding='utf-8')
    return True, title, description


def clean_empty_directories(base_dir: Path):
    """Remove empty directories recursively."""
    for dirpath, dirnames, filenames in os.walk(base_dir, topdown=False):
        if not dirnames and not filenames:
            os.rmdir(dirpath)
            print(f"  Removed empty directory: {dirpath}")


def generate_index(docs_info: list[tuple[str, str, str, str]], output_dir: Path) -> str:
    """Generate index.md content from successful downloads.

    Args:
        docs_info: List of (url, title, description, local_path) tuples
        output_dir: Output directory path
    """
    lines = [
        "# Claude Platform Documentation",
        "",
        "> Anthropic Claude Platform API/SDK 官方文档镜像，包含 Messages API、Agent SDK、Tool Use 等完整参考。",
        "",
        "This is a mirror of the [Claude Platform documentation](https://platform.claude.com/docs).",
        "",
        "**Source**: [sitemap.xml](https://platform.claude.com/sitemap.xml)",
        "",
        "---",
        "",
    ]
    categories: dict[str, list[tuple[str, str, str]]] = {}
    for url, title, description, local_path in docs_info:
        path = url.replace(f"{BASE_URL}/docs/en/", "")
        parts = path.split('/')
        if len(parts) >= 2:
            category = parts[0].replace('-', ' ').title()
        else:
            category = "Getting Started"
        if not title:
            title = parts[-1].replace('-', ' ').title()
        rel_path = os.path.relpath(local_path, output_dir)
        if category not in categories:
            categories[category] = []
        categories[category].append((title, rel_path, description or ""))

    category_order = [
        "Getting Started", "About Claude", "Build With Claude",
        "Agents And Tools", "Agent Sdk", "Test And Evaluate",
        "Api", "Resources", "Release Notes",
    ]
    def sort_key(cat):
        try:
            return (0, category_order.index(cat))
        except ValueError:
            return (1, cat)
    for category in sorted(categories.keys(), key=sort_key):
        lines.append(f"## {category}")
        lines.append("")
        for title, rel_path, description in sorted(categories[category], key=lambda x: x[0]):
            if description:
                lines.append(f"- [{title}]({rel_path}) - {description}")
            else:
                lines.append(f"- [{title}]({rel_path})")
        lines.append("")
    return '\n'.join(lines)


def main():
    """Main function to download all documentation."""
    script_dir = Path(__file__).parent.parent
    output_dir = script_dir / OUTPUT_DIR

    if output_dir.exists():
        print("Cleaning up existing docs directory...")
        shutil.rmtree(output_dir)

    urls = discover_pages_from_sitemap()
    if not urls:
        print("No documentation pages found!")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0
    docs_info: list[tuple[str, str, str, str]] = []

    for i, url in enumerate(urls, 1):
        filename = urlparse(url).path.split('/')[-1]
        print(f"[{i}/{len(urls)}] Downloading {filename}...", end=" ")
        success, title, description = download_and_save_file(url, output_dir)
        if success:
            print(f"✓ {title or ''}")
            success_count += 1
            local_path = str(url_to_local_path(url, output_dir))
            docs_info.append((url, title or "", description or "", local_path))
        else:
            print("✗")
            fail_count += 1
        time.sleep(REQUEST_DELAY)

    print(f"\nDownload complete!")
    print(f"  Success: {success_count}")
    print(f"  Failed: {fail_count}")

    print("\nCleaning up empty directories...")
    clean_empty_directories(output_dir)

    print("\nGenerating index file...")
    index_content = generate_index(docs_info, output_dir)
    index_path = output_dir / INDEX_FILE
    index_path.write_text(index_content, encoding='utf-8')

    print(f"\nFinal results:")
    print(f"  Output directory: {output_dir}")
    print(f"  Index file: {index_path}")
    print(f"  Total files: {success_count}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    exit(main() or 0)
