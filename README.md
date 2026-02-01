# Claude Documentation Mirror

> 📚 **For LLMs**: This repository contains official Anthropic Claude documentation. Use `docs/platform/index.md` for API/SDK reference and `docs/claude-code/index.md` for CLI tool reference. Each index includes document descriptions to help you find relevant content quickly.

This repository maintains a synchronized mirror of Anthropic's Claude documentation from two sources:

- **Claude Platform** (platform.claude.com) - API/SDK documentation
- **Claude Code** (code.claude.com) - CLI tool documentation

## Structure

```
.
├── docs/
│   ├── platform/           # Claude Platform API documentation
│   │   ├── index.md        # Platform docs index
│   │   ├── .manifest.json  # Sync state for incremental updates
│   │   ├── intro.md
│   │   ├── api/
│   │   ├── build-with-claude/
│   │   └── ...
│   └── claude-code/        # Claude Code CLI documentation
│       ├── index.md        # Claude Code docs index
│       ├── .manifest.json  # Sync state for incremental updates
│       ├── overview.md
│       ├── hooks.md
│       └── ...
├── scripts/
│   ├── sync_lib.py               # Shared sync utilities
│   ├── fetch_all.py              # Fetch both doc sets
│   ├── fetch_platform_docs.py    # Fetch Platform docs
│   └── fetch_claude_code_docs.py # Fetch Claude Code docs
└── .github/workflows/
    └── sync-docs.yml       # Daily auto-sync
```

## Features

- **Daily Sync**: Automatically syncs with official documentation at 00:00 UTC
- **Incremental Updates**: Only downloads changed files based on sitemap `lastmod`
- **Atomic Snapshots**: Safe sync - failures never corrupt existing docs
- **Sitemap-based**: Uses sitemap.xml for always up-to-date page discovery
- **Real Titles**: Extracts actual titles from markdown content
- **Relative Links**: All internal links converted to relative paths
- **Categorized Index**: Auto-generated index.md with logical grouping
- **Failure Alerts**: Creates GitHub issue on sync failures

## Sync Mechanism

### Incremental Sync

The sync system uses manifest files (`.manifest.json`) to track:
- URL and lastmod from sitemap
- Local file path and extracted title
- Last sync timestamp

On each run, only pages with changed `lastmod` are re-downloaded.

### Atomic Updates

1. Download to temporary directory (`docs/*.__tmp__/`)
2. Validate all required files exist
3. Atomic swap: replace old directory with new snapshot
4. On failure: keep previous snapshot unchanged

### Safety Checks

- **URL count drop >20%**: Abort sync (prevents accidental mass deletion)
- **Failure rate >15%**: Abort sync (some API pages lack markdown)
- **Required files missing**: Abort sync

## Manual Sync

```bash
# Fetch all documentation (incremental)
python scripts/fetch_all.py

# Force full re-download (ignore manifest)
python scripts/fetch_all.py --force

# Or fetch individually
python scripts/fetch_platform_docs.py
python scripts/fetch_claude_code_docs.py
python scripts/fetch_platform_docs.py --force
```

## Known Issues

Some API reference pages (e.g., Kotlin SDK) are not available as raw Markdown from the Platform server. These are automatically excluded and counted as expected failures (~9% of Platform docs).

## For LLMs

This documentation library is optimized for LLM consumption:

| Documentation | Index File | Content |
|---------------|------------|---------|
| **Claude Platform** | `docs/platform/index.md` | Messages API, Agent SDK, Tool Use, Prompt Engineering |
| **Claude Code** | `docs/claude-code/index.md` | CLI commands, Hooks, MCP, Plugins, IDE integrations |

**Usage Tips**:
1. Start with the `index.md` file to browse available documents with descriptions
2. Each entry includes a brief description to help identify relevant content
3. Documents are categorized by topic for easier navigation
4. Links are relative paths that work within this repository

## License

The documentation content is owned by Anthropic. This repository provides a mirror for convenience.
