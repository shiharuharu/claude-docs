#!/usr/bin/env python3
"""
Shared library for syncing Claude documentation.

This module centralizes the core mechanics needed by both doc sync scripts:
- Robust downloads with retries/backoff
- Markdown validation and title/description extraction
- Sitemap parsing (loc + lastmod)
- Manifest read/write for incremental sync + sanity checks
- Atomic directory replacement via a temporary snapshot directory
"""

from __future__ import annotations

import json
import os
import random
import shutil
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; DocsDownloader/3.0)"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_request(
    url: str,
    *,
    user_agent: str = DEFAULT_USER_AGENT,
    cache_control: str = "no-cache",
    accept: str | None = None,
) -> urllib.request.Request:
    headers: dict[str, str] = {"User-Agent": user_agent, "Cache-Control": cache_control}
    if accept:
        headers["Accept"] = accept
    return urllib.request.Request(url, headers=headers)


def validate_markdown_content(content: str) -> bool:
    """Heuristic validation to reject HTML/error pages."""
    if not content or len(content.strip()) < 50:
        return False
    markdown_indicators = ["# ", "## ", "### ", "```", "- ", "* ", "1. ", "[", "**", "> "]
    lines = content.split("\n")[:50]
    indicator_count = sum(1 for line in lines for ind in markdown_indicators if ind in line)
    return indicator_count >= 3


def download_bytes(
    url: str,
    *,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    max_retry_delay: float = 30.0,
    user_agent: str = DEFAULT_USER_AGENT,
) -> bytes:
    """Download raw bytes with retry/backoff. Raises on final failure."""
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            req = create_request(url, user_agent=user_agent, accept="*/*")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            last_error = e
            if e.code == 429:
                wait_time = int(e.headers.get("Retry-After", "60") or "60")
                print(f"  Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            if e.code == 404:
                raise
            delay = min(retry_delay * (2**attempt), max_retry_delay)
            time.sleep(delay * random.uniform(0.5, 1.0))
        except urllib.error.URLError as e:
            last_error = e
            delay = min(retry_delay * (2**attempt), max_retry_delay)
            time.sleep(delay * random.uniform(0.5, 1.0))
        except Exception as e:
            last_error = e
            delay = min(retry_delay * (2**attempt), max_retry_delay)
            time.sleep(delay * random.uniform(0.5, 1.0))

    raise RuntimeError(f"Failed to download after {max_retries} attempts: {url}: {last_error}")


def download_content(
    url: str,
    *,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    max_retry_delay: float = 30.0,
    user_agent: str = DEFAULT_USER_AGENT,
    validate: Callable[[str], bool] = validate_markdown_content,
) -> str | None:
    """Download text content with retry/backoff; returns None for non-markdown/404/invalid."""
    for attempt in range(max_retries):
        try:
            req = create_request(url, user_agent=user_agent, accept="text/plain, text/markdown, */*")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode("utf-8")
                lowered = content.lstrip().lower()
                if lowered.startswith("<!doctype html") or lowered.startswith("<html"):
                    return None
                if not validate(content):
                    return None
                return content
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = int(e.headers.get("Retry-After", "60") or "60")
                print(f"  Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            if e.code == 404:
                return None
            if attempt == max_retries - 1:
                print(f"  HTTP Error {e.code}: {url}")
            delay = min(retry_delay * (2**attempt), max_retry_delay)
            time.sleep(delay * random.uniform(0.5, 1.0))
        except urllib.error.URLError as e:
            if attempt == max_retries - 1:
                print(f"  URL Error: {e.reason}")
            delay = min(retry_delay * (2**attempt), max_retry_delay)
            time.sleep(delay * random.uniform(0.5, 1.0))
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"  Error: {e}")
            delay = min(retry_delay * (2**attempt), max_retry_delay)
            time.sleep(delay * random.uniform(0.5, 1.0))
    return None


def extract_title_and_description(content: str) -> tuple[str | None, str | None]:
    """Extract the title from the first H1 and a short description line below it."""
    lines = content.split("\n")
    title: str | None = None
    description: str | None = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if next_line == "":
                    continue
                if next_line.startswith("---"):
                    break
                if next_line.startswith("## ") or next_line.startswith("# "):
                    break
                if next_line.startswith("> "):
                    description = next_line[2:].strip()
                else:
                    description = next_line
                break
            break

    return title, description


@dataclass(frozen=True)
class SitemapEntry:
    url: str
    lastmod: str | None = None


class SitemapParser:
    def __init__(self, *, user_agent: str = DEFAULT_USER_AGENT):
        self.user_agent = user_agent

    def fetch_and_parse(self, sitemap_url: str) -> list[SitemapEntry]:
        return self._fetch_and_parse_recursive(sitemap_url, seen=set())

    def _fetch_and_parse_recursive(self, sitemap_url: str, *, seen: set[str]) -> list[SitemapEntry]:
        if sitemap_url in seen:
            return []
        seen.add(sitemap_url)

        xml_bytes = download_bytes(sitemap_url, user_agent=self.user_agent)
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as e:
            raise RuntimeError(f"Invalid sitemap XML: {sitemap_url}: {e}") from e

        tag = self._strip_ns(root.tag)
        if tag == "sitemapindex":
            sitemap_locs: list[str] = []
            for sm in root.findall(".//{*}sitemap"):
                loc_elem = sm.find("{*}loc")
                if loc_elem is not None and loc_elem.text:
                    sitemap_locs.append(loc_elem.text.strip())
            if not sitemap_locs:
                raise RuntimeError(f"Sitemap index contains 0 child sitemaps: {sitemap_url}")
            combined: list[SitemapEntry] = []
            for loc in sitemap_locs:
                combined.extend(self._fetch_and_parse_recursive(loc, seen=seen))
            return self._dedupe(combined)

        if tag != "urlset":
            raise RuntimeError(f"Unsupported sitemap root element '{tag}' from {sitemap_url}")

        entries: list[SitemapEntry] = []
        for url_elem in root.findall(".//{*}url"):
            loc_elem = url_elem.find("{*}loc")
            if loc_elem is None or not loc_elem.text:
                continue
            loc = loc_elem.text.strip()
            lastmod_elem = url_elem.find("{*}lastmod")
            lastmod = lastmod_elem.text.strip() if (lastmod_elem is not None and lastmod_elem.text) else None
            entries.append(SitemapEntry(url=loc, lastmod=lastmod))
        return self._dedupe(entries)

    @staticmethod
    def _strip_ns(tag: str) -> str:
        return tag.split("}", 1)[-1] if "}" in tag else tag

    @staticmethod
    def _dedupe(entries: list[SitemapEntry]) -> list[SitemapEntry]:
        seen: set[str] = set()
        out: list[SitemapEntry] = []
        for e in entries:
            if e.url in seen:
                continue
            seen.add(e.url)
            out.append(e)
        return out


class Manifest:
    """A simple url->metadata store persisted as JSON."""

    VERSION = 1

    def __init__(self, path: Path, *, meta: dict | None = None, entries: dict[str, dict] | None = None):
        self.path = Path(path)
        self.meta: dict = meta or {}
        self.entries: dict[str, dict] = entries or {}

    @classmethod
    def load(cls, path: Path) -> "Manifest":
        path = Path(path)
        if not path.exists():
            return cls(path)

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise RuntimeError(f"Failed to read manifest: {path}: {e}") from e

        meta = data.get("meta") or {}
        entries = data.get("entries") or {}
        if isinstance(entries, list):
            entries = {e.get("url"): e for e in entries if isinstance(e, dict) and e.get("url")}
        if not isinstance(entries, dict):
            raise RuntimeError(f"Manifest entries must be an object: {path}")

        return cls(path, meta=meta, entries=entries)

    def get(self, url: str) -> dict | None:
        return self.entries.get(url)

    def set(self, entry: dict) -> None:
        url = entry.get("url")
        if not url:
            raise ValueError("Manifest entry missing 'url'")
        self.entries[url] = entry

    def to_dict(self) -> dict:
        return {"version": self.VERSION, "meta": self.meta, "entries": self.entries}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = Path(str(self.path) + ".__tmp__")
        tmp_path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(self.path)


class AtomicSync:
    """Build a complete snapshot in a temp dir, then swap it into place."""

    def __init__(self, target_dir: Path, *, tmp_dir: Path | None = None):
        self.target_dir = Path(target_dir)
        self.tmp_dir = Path(tmp_dir) if tmp_dir else self.target_dir.with_name(self.target_dir.name + ".__tmp__")
        self.backup_dir = self.target_dir.with_name(self.target_dir.name + ".__bak__")

    def prepare(self) -> Path:
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        return self.tmp_dir

    def commit(self) -> None:
        if not self.tmp_dir.exists():
            raise RuntimeError(f"Temp dir does not exist: {self.tmp_dir}")

        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir, ignore_errors=True)
            if self.backup_dir.exists():
                raise RuntimeError(f"Failed to remove existing backup dir: {self.backup_dir}")

        had_old = self.target_dir.exists()
        if had_old:
            self.target_dir.rename(self.backup_dir)

        try:
            self.tmp_dir.rename(self.target_dir)
        except Exception:
            # Best-effort rollback to avoid breaking the old snapshot.
            try:
                if self.target_dir.exists():
                    shutil.rmtree(self.target_dir)
            except Exception:
                pass
            if had_old and self.backup_dir.exists() and not self.target_dir.exists():
                try:
                    self.backup_dir.rename(self.target_dir)
                except Exception:
                    pass
            try:
                if self.tmp_dir.exists():
                    shutil.rmtree(self.tmp_dir)
            except Exception:
                pass
            raise

        if self.backup_dir.exists():
            try:
                shutil.rmtree(self.backup_dir)
            except Exception as e:
                # Snapshot is already in place; leftover backups are non-fatal and ignored via .gitignore.
                print(f"  Warning: failed to remove backup dir {self.backup_dir}: {e}")

    def cleanup(self) -> None:
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)


def ensure_dir_empty(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def clean_empty_directories(base_dir: Path) -> None:
    """Remove empty directories recursively (useful for nested snapshots)."""
    for dirpath, dirnames, filenames in os.walk(base_dir, topdown=False):
        if not dirnames and not filenames:
            os.rmdir(dirpath)


def sync_docs(
    *,
    sitemap_url: str,
    output_dir: Path,
    required_files: list[str],
    url_to_rel_path: Callable[[str], Path],
    generate_index: Callable[[list[tuple[str, str, str, str]], Path], str],
    filter_entries: Callable[[list[SitemapEntry]], list[SitemapEntry]] | None = None,
    postprocess_content: Callable[[str, Path, Path], str] | None = None,
    force: bool = False,
    manifest_filename: str = ".manifest.json",
    index_filename: str = "index.md",
    request_delay: float = 0.1,
    sanity_drop_ratio: float = 0.20,
    max_fail_ratio: float = 0.15,
    clean_empty_dirs: bool = False,
    found_label: str = "URLs",
) -> int:
    """Sync docs to a local mirror directory using a safe, atomic snapshot update."""
    output_dir = Path(output_dir)
    manifest_path = output_dir / manifest_filename
    atomic = AtomicSync(output_dir)

    try:
        old_manifest = Manifest.load(manifest_path)

        print(f"Fetching sitemap from {sitemap_url}...")
        sitemap_entries = SitemapParser().fetch_and_parse(sitemap_url)
        entries = filter_entries(sitemap_entries) if filter_entries else sitemap_entries
        print(f"Found {len(entries)} {found_label}")

        if len(entries) == 0:
            print("No documentation pages found!")
            return 1

        prev_url_count = old_manifest.meta.get("last_url_count")
        if isinstance(prev_url_count, str) and prev_url_count.isdigit():
            prev_url_count = int(prev_url_count)
        if isinstance(prev_url_count, int) and prev_url_count > 0:
            drop_ratio = (prev_url_count - len(entries)) / prev_url_count
            if drop_ratio > sanity_drop_ratio:
                print(
                    f"ERROR: Sitemap URL count dropped too much: prev={prev_url_count}, current={len(entries)} (drop={drop_ratio:.1%})."
                )
                return 1

        tmp_dir = atomic.prepare()
        now = utc_now_iso()

        success_count = 0
        fail_count = 0
        downloaded_count = 0
        reused_count = 0

        docs_info: list[tuple[str, str, str, str]] = []
        new_manifest = Manifest(
            tmp_dir / manifest_filename,
            meta={"last_sync_time": now, "last_url_count": len(entries)},
        )

        for i, entry in enumerate(entries, 1):
            url = entry.url
            rel_path = url_to_rel_path(url)
            dst_path = tmp_dir / rel_path
            filename = rel_path.name

            old_entry = None if force else old_manifest.get(url)
            need_download = force or old_entry is None
            if not need_download:
                old_lastmod = old_entry.get("lastmod")
                if entry.lastmod is None or old_lastmod is None or entry.lastmod != old_lastmod:
                    need_download = True
                else:
                    src_path = output_dir / rel_path
                    if not src_path.exists():
                        need_download = True

            print(f"[{i}/{len(entries)}] Downloading {filename}...", end=" ")

            title: str | None = None
            description: str | None = None
            entry_sync_time = now

            if need_download:
                md_url = url if url.endswith(".md") else url + ".md"
                content = download_content(md_url)
                if content is None:
                    print("✗")
                    fail_count += 1
                    continue

                title, description = extract_title_and_description(content)
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                processed = (
                    postprocess_content(content, dst_path, tmp_dir) if postprocess_content else content
                )
                dst_path.write_text(processed, encoding="utf-8")
                downloaded_count += 1
                print(f"✓ {title or ''}")
                if request_delay:
                    time.sleep(request_delay)
            else:
                src_path = output_dir / rel_path
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                title = (old_entry or {}).get("title") if old_entry else None
                description = (old_entry or {}).get("description") if old_entry else None
                entry_sync_time = (old_entry or {}).get("last_sync_time") or now
                reused_count += 1
                print(f"✓ {title or ''}")

            success_count += 1
            docs_info.append((url, title or "", description or "", str(dst_path)))
            new_manifest.set(
                {
                    "url": url,
                    "lastmod": entry.lastmod,
                    "local_path": rel_path.as_posix(),
                    "title": title or "",
                    "description": description or "",
                    "last_sync_time": entry_sync_time,
                }
            )

        print("\nDownload complete!")
        print(f"  Success: {success_count}")
        print(f"  Failed: {fail_count}")
        print(f"  Downloaded: {downloaded_count}")
        print(f"  Reused: {reused_count}")

        # Allow a certain ratio of failures (some pages may not have markdown versions)
        fail_ratio = fail_count / len(entries) if len(entries) > 0 else 0
        if fail_ratio > max_fail_ratio:
            print(f"ERROR: Too many failures ({fail_count}/{len(entries)} = {fail_ratio:.1%} > {max_fail_ratio:.0%}); keeping previous snapshot unchanged.")
            atomic.cleanup()
            return 1

        if success_count == 0:
            print("ERROR: No pages were successfully downloaded; keeping previous snapshot unchanged.")
            atomic.cleanup()
            return 1

        if clean_empty_dirs:
            print("\nCleaning up empty directories...")
            clean_empty_directories(tmp_dir)

        print("\nGenerating index file...")
        index_content = generate_index(docs_info, tmp_dir)
        index_path = tmp_dir / index_filename
        index_path.write_text(index_content, encoding="utf-8")

        new_manifest.save()

        missing_required = [p for p in required_files if not (tmp_dir / p).exists()]
        if missing_required:
            print(f"ERROR: Missing required files in snapshot: {missing_required}")
            atomic.cleanup()
            return 1
        if not index_path.exists():
            print(f"ERROR: Missing generated {index_filename} in snapshot.")
            atomic.cleanup()
            return 1

        atomic.commit()

        print("\nFinal results:")
        print(f"  Output directory: {output_dir}")
        print(f"  Index file: {output_dir / index_filename}")
        print(f"  Total files: {success_count}")

        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        try:
            atomic.cleanup()
        except Exception:
            pass
        return 1
