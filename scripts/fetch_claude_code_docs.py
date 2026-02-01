#!/usr/bin/env python3
"""
Download Claude Code documentation from code.claude.com sitemap.xml.

Features:
- Discovers documentation pages from sitemap.xml (always up-to-date)
- Incremental sync via sitemap lastmod + local manifest
- Atomic snapshot replacement (safe on failures)
- Downloads all English .md files (or only changed/new files)
- Flat directory structure (all files in docs/claude-code/)
- Fixes relative links within downloaded files
- Extracts real titles from markdown content
- Generates index.md with proper categorization

Usage:
    python scripts/fetch_claude_code_docs.py [--force]
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

BASE_URL = "https://code.claude.com"
SITEMAP_URL = f"{BASE_URL}/docs/sitemap.xml"
OUTPUT_DIR = "docs/claude-code"
INDEX_FILE = "index.md"
MANIFEST_FILE = ".manifest.json"
REQUEST_DELAY = 0.1
SANITY_DROP_RATIO = 0.20  # >20% drop is suspicious
REQUIRED_FILES = ["overview.md"]

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Claude Code documentation (safe + incremental).")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force a full re-download (ignore manifest lastmod and cached files).",
    )
    return parser.parse_args(argv)


def url_to_rel_path(url: str) -> Path:
    """Convert a docs URL to a relative path inside docs/claude-code/ (flat)."""
    parsed = urlparse(url)
    filename = parsed.path.rstrip("/").split("/")[-1]
    if not filename.endswith(".md"):
        filename += ".md"
    return Path(filename)


def url_to_local_path(url: str, output_dir: Path) -> Path:
    return output_dir / url_to_rel_path(url)


def fix_relative_links(content: str, output_dir: Path) -> str:
    """Fix links in markdown content to work with local file structure."""
    def replace_link(match):
        link_text = match.group(1)
        url = match.group(2)
        # Only process code.claude.com docs links
        if not url.startswith('https://code.claude.com/docs/'):
            return match.group(0)
        # Extract filename and make it relative
        filename = url.split('/')[-1]
        if not filename.endswith('.md'):
            filename += '.md'
        return f'[{link_text}]({filename})'
    pattern = r'\[([^\]]+)\]\((https://code\.claude\.com/docs/[^)]+)\)'
    return re.sub(pattern, replace_link, content)

def filter_sitemap_entries(entries: list[SitemapEntry]) -> list[SitemapEntry]:
    docs: list[SitemapEntry] = []
    for e in entries:
        if "/docs/en/" not in e.url:
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
        "# Claude Code Documentation",
        "",
        "> Claude Code CLI 工具官方文档镜像，包含 Hooks、MCP、Plugins、IDE 集成等完整参考。",
        "",
        "This is a mirror of the [Claude Code documentation](https://code.claude.com/docs).",
        "",
        "**Source**: [sitemap.xml](https://code.claude.com/docs/sitemap.xml)",
        "",
        "---",
        "",
    ]

    # Define categories based on topic
    category_mapping = {
        "Getting Started": ["overview", "quickstart", "setup", "features-overview"],
        "Core Features": ["memory", "hooks", "hooks-guide", "mcp", "settings", "cli-reference", "common-workflows"],
        "IDE Integration": ["vs-code", "jetbrains", "desktop", "chrome", "devcontainer"],
        "CI/CD": ["github-actions", "gitlab-ci-cd", "headless"],
        "Cloud Providers": ["amazon-bedrock", "google-vertex-ai", "microsoft-foundry"],
        "Enterprise": ["iam", "monitoring-usage", "analytics", "costs"],
        "Security & Privacy": ["security", "data-usage", "sandboxing", "permissions"],
        "Advanced": ["subagents", "multi-claude", "checkpointing", "best-practices"],
        "Extensions": ["plugins", "discover-plugins", "sdk"],
        "Other": ["troubleshooting", "claude-code-on-the-web"],
    }

    # Reverse mapping: filename -> category
    file_to_category = {}
    for category, files in category_mapping.items():
        for f in files:
            file_to_category[f] = category

    categories: dict[str, list[tuple[str, str, str]]] = {}
    for url, title, description, local_path in docs_info:
        filename = url.split('/')[-1]
        category = file_to_category.get(filename, "Other")
        if not title:
            title = filename.replace('-', ' ').title()
        rel_path = os.path.relpath(local_path, output_dir)
        if category not in categories:
            categories[category] = []
        categories[category].append((title, rel_path, description or ""))

    # Sort categories by predefined order
    category_order = list(category_mapping.keys())
    def sort_key(cat):
        try:
            return category_order.index(cat)
        except ValueError:
            return len(category_order)

    for category in sorted(categories.keys(), key=sort_key):
        if not categories[category]:
            continue
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
        postprocess_content=lambda content, _dst_path, snapshot_dir: fix_relative_links(content, snapshot_dir),
        force=args.force,
        manifest_filename=MANIFEST_FILE,
        index_filename=INDEX_FILE,
        request_delay=REQUEST_DELAY,
        sanity_drop_ratio=SANITY_DROP_RATIO,
        found_label="English documentation pages",
    )


if __name__ == "__main__":
    exit(main() or 0)
