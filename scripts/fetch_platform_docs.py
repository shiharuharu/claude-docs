#!/usr/bin/env python3
"""
Download Anthropic Claude Platform documentation from sitemap.xml.

Features:
- Discovers documentation pages from sitemap.xml (always up-to-date)
- Incremental sync via sitemap lastmod + local manifest
- Atomic snapshot replacement (safe on failures)
- Downloads all English .md files (or only changed/new files)
- Preserves directory structure
- Fixes relative links within downloaded files
- Extracts real titles from markdown content
- Generates index.md with proper categorization

Usage:
    python scripts/fetch_platform_docs.py [--force]
"""

import argparse
import re
import os
from pathlib import Path
from urllib.parse import urlparse

from sync_lib import (
    SitemapEntry,
    sync_docs,
)

BASE_URL = "https://platform.claude.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
OUTPUT_DIR = "docs/platform"
INDEX_FILE = "index.md"
MANIFEST_FILE = ".manifest.json"
REQUEST_DELAY = 0.1
SANITY_DROP_RATIO = 0.20  # >20% drop is suspicious
REQUIRED_FILES = ["get-started.md"]

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Claude Platform documentation (safe + incremental).")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force a full re-download (ignore manifest lastmod and cached files).",
    )
    return parser.parse_args(argv)


def url_to_rel_path(url: str) -> Path:
    """Convert a docs URL to a relative path inside docs/platform/."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if "/docs/en/" in path:
        path = path.split("/docs/en/", 1)[1]
    elif "/docs/" in path:
        path = path.split("/docs/", 1)[1]
    else:
        path = path.lstrip("/")
    if not path.endswith(".md"):
        path += ".md"
    return Path(path)


def url_to_local_path(url: str, output_dir: Path) -> Path:
    return output_dir / url_to_rel_path(url)


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

def filter_sitemap_entries(entries: list[SitemapEntry]) -> list[SitemapEntry]:
    docs: list[SitemapEntry] = []
    base = f"{BASE_URL}/docs/en/"
    for e in entries:
        if not e.url.startswith(base):
            continue
        if e.url.rstrip("/") == f"{BASE_URL}/docs/en":
            continue
        docs.append(e)
    return docs


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
    """Main function to sync all documentation."""
    args = parse_args()
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / OUTPUT_DIR

    return sync_docs(
        sitemap_url=SITEMAP_URL,
        output_dir=output_dir,
        required_files=REQUIRED_FILES,
        url_to_rel_path=url_to_rel_path,
        generate_index=generate_index,
        filter_entries=filter_sitemap_entries,
        postprocess_content=lambda content, dst_path, snapshot_dir: fix_relative_links(
            content, dst_path, snapshot_dir
        ),
        force=args.force,
        manifest_filename=MANIFEST_FILE,
        index_filename=INDEX_FILE,
        request_delay=REQUEST_DELAY,
        sanity_drop_ratio=SANITY_DROP_RATIO,
        clean_empty_dirs=True,
        found_label="English documentation pages",
    )


if __name__ == "__main__":
    exit(main() or 0)
