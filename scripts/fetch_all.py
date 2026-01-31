#!/usr/bin/env python3
"""
Fetch all Claude documentation (both Platform and Claude Code).

Usage:
    python scripts/fetch_all.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    script_dir = Path(__file__).parent

    print("=" * 60)
    print("Fetching Claude Platform Documentation")
    print("=" * 60)
    result1 = subprocess.run(
        [sys.executable, script_dir / "fetch_platform_docs.py"],
        cwd=script_dir.parent
    )

    print("\n" + "=" * 60)
    print("Fetching Claude Code Documentation")
    print("=" * 60)
    result2 = subprocess.run(
        [sys.executable, script_dir / "fetch_claude_code_docs.py"],
        cwd=script_dir.parent
    )

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Platform docs: {'✓' if result1.returncode == 0 else '✗ (partial)'}")
    print(f"Claude Code docs: {'✓' if result2.returncode == 0 else '✗ (partial)'}")

    # Return success if at least one succeeded
    return 0 if result1.returncode == 0 or result2.returncode == 0 else 1


if __name__ == "__main__":
    exit(main())
