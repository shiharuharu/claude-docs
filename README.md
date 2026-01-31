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
│   │   ├── intro.md
│   │   ├── api/
│   │   ├── build-with-claude/
│   │   └── ...
│   └── claude-code/        # Claude Code CLI documentation
│       ├── index.md        # Claude Code docs index
│       ├── overview.md
│       ├── hooks.md
│       └── ...
├── scripts/
│   ├── fetch_all.py              # Fetch both doc sets
│   ├── fetch_platform_docs.py    # Fetch Platform docs
│   └── fetch_claude_code_docs.py # Fetch Claude Code docs
└── .github/workflows/
    └── sync-docs.yml       # Daily auto-sync
```

## Features

- **Daily Sync**: Automatically syncs with official documentation at 00:00 UTC
- **Sitemap-based**: Uses sitemap.xml for always up-to-date page discovery
- **Real Titles**: Extracts actual titles from markdown content
- **Relative Links**: All internal links converted to relative paths
- **Categorized Index**: Auto-generated index.md with logical grouping

## Manual Sync

```bash
# Fetch all documentation
python scripts/fetch_all.py

# Or fetch individually
python scripts/fetch_platform_docs.py
python scripts/fetch_claude_code_docs.py
```

## Known Issues

Some Kotlin SDK documentation files are not available as raw Markdown from the Platform server. These are automatically excluded.

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
