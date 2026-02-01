#!/usr/bin/env python3
"""
Fetch all Claude documentation (both Platform and Claude Code).

Usage:
    python scripts/fetch_all.py [--force]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync all Claude documentation sources.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force full sync for all sources (ignore manifests / lastmod).",
    )
    return parser.parse_args(argv)


def main() -> int:
    script_dir = Path(__file__).parent
    args = parse_args()
    extra_args = ["--force"] if args.force else []

    print("=" * 60)
    print("Fetching Claude Platform Documentation")
    print("=" * 60)
    result1 = subprocess.run(
        [sys.executable, script_dir / "fetch_platform_docs.py", *extra_args],
        cwd=script_dir.parent
    )

    print("\n" + "=" * 60)
    print("Fetching Claude Code Documentation")
    print("=" * 60)
    result2 = subprocess.run(
        [sys.executable, script_dir / "fetch_claude_code_docs.py", *extra_args],
        cwd=script_dir.parent
    )

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Platform docs: {'✓' if result1.returncode == 0 else '✗'}")
    print(f"Claude Code docs: {'✓' if result2.returncode == 0 else '✗'}")

    # Fail the overall run if any source failed. (Workflow will open an alert issue.)
    return 0 if (result1.returncode == 0 and result2.returncode == 0) else 1


if __name__ == "__main__":
    exit(main())
