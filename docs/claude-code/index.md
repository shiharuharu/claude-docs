# Claude Code Documentation

> Claude Code CLI 工具官方文档镜像，包含 Hooks、MCP、Plugins、IDE 集成等完整参考。

This is a mirror of the [Claude Code documentation](https://code.claude.com/docs).

**Source**: [sitemap.xml](https://code.claude.com/docs/sitemap.xml)

---

## Getting Started

- [Claude Code overview](overview.md) - Learn about Claude Code, Anthropic's agentic coding tool that works in your terminal, IDE, desktop app, and browser to help you turn ideas into code faster than ever before.
- [Extend Claude Code](features-overview.md) - Understand when to use CLAUDE.md, Skills, subagents, hooks, MCP, and plugins.
- [Quickstart](quickstart.md) - Welcome to Claude Code!
- [Set up Claude Code](setup.md) - Install, authenticate, and start using Claude Code on your development machine.

## Core Features

- [Automate workflows with hooks](hooks-guide.md) - Run shell commands automatically when Claude Code edits files, finishes tasks, or needs input. Format code, send notifications, validate commands, and enforce project rules.
- [CLI reference](cli-reference.md) - Complete reference for Claude Code command-line interface, including commands and flags.
- [Claude Code settings](settings.md) - Configure Claude Code with global and project-level settings, and environment variables.
- [Common workflows](common-workflows.md) - Step-by-step guides for exploring codebases, fixing bugs, refactoring, testing, and other everyday tasks with Claude Code.
- [Connect Claude Code to tools via MCP](mcp.md) - Learn how to connect Claude Code to your tools with the Model Context Protocol.
- [Hooks reference](hooks.md) - Reference for Claude Code hook events, configuration schema, JSON input/output formats, exit codes, async hooks, prompt hooks, and MCP tool hooks.
- [Manage Claude's memory](memory.md) - Learn how to manage Claude Code's memory across sessions with different memory locations and best practices.

## IDE Integration

- [Claude Code on desktop](desktop.md) - Run Claude Code tasks locally or on secure cloud infrastructure with the Claude desktop app
- [Development containers](devcontainer.md) - Learn about the Claude Code development container for teams that need consistent, secure environments.
- [JetBrains IDEs](jetbrains.md) - Use Claude Code with JetBrains IDEs including IntelliJ, PyCharm, WebStorm, and more
- [Use Claude Code in VS Code](vs-code.md) - Install and configure the Claude Code extension for VS Code. Get AI coding assistance with inline diffs, @-mentions, plan review, and keyboard shortcuts.
- [Use Claude Code with Chrome (beta)](chrome.md) - Connect Claude Code to your Chrome browser to test web apps, debug with console logs, automate form filling, and extract data from web pages.

## CI/CD

- [Claude Code GitHub Actions](github-actions.md) - Learn about integrating Claude Code into your development workflow with Claude Code GitHub Actions
- [Claude Code GitLab CI/CD](gitlab-ci-cd.md) - Learn about integrating Claude Code into your development workflow with GitLab CI/CD
- [Run Claude Code programmatically](headless.md) - Use the Agent SDK to run Claude Code programmatically from the CLI, Python, or TypeScript.

## Cloud Providers

- [Claude Code on Amazon Bedrock](amazon-bedrock.md) - Learn about configuring Claude Code through Amazon Bedrock, including setup, IAM configuration, and troubleshooting.
- [Claude Code on Google Vertex AI](google-vertex-ai.md) - Learn about configuring Claude Code through Google Vertex AI, including setup, IAM configuration, and troubleshooting.
- [Claude Code on Microsoft Foundry](microsoft-foundry.md) - Learn about configuring Claude Code through Microsoft Foundry, including setup, configuration, and troubleshooting.

## Enterprise

- [Manage costs effectively](costs.md) - Track token usage, set team spend limits, and reduce Claude Code costs with context management, model selection, extended thinking settings, and preprocessing hooks.
- [Monitoring](monitoring-usage.md) - Learn how to enable and configure OpenTelemetry for Claude Code.
- [Track team usage with analytics](analytics.md) - View Claude Code usage metrics, track adoption, and measure engineering velocity in the analytics dashboard.

## Security & Privacy

- [Configure permissions](permissions.md) - Control what Claude Code can access and do with fine-grained permission rules, modes, and managed policies.
- [Data usage](data-usage.md) - Learn about Anthropic's data usage policies for Claude
- [Sandboxing](sandboxing.md) - Learn how Claude Code's sandboxed bash tool provides filesystem and network isolation for safer, more autonomous agent execution.
- [Security](security.md) - Learn about Claude Code's security safeguards and best practices for safe usage.

## Advanced

- [Best Practices for Claude Code](best-practices.md) - Tips and patterns for getting the most out of Claude Code, from configuring your environment to scaling across parallel sessions.
- [Checkpointing](checkpointing.md) - Automatically track and rewind Claude's edits to quickly recover from unwanted changes.

## Extensions

- [Create plugins](plugins.md) - Create custom plugins to extend Claude Code with skills, agents, hooks, and MCP servers.
- [Discover and install prebuilt plugins through marketplaces](discover-plugins.md) - Find and install plugins from marketplaces to extend Claude Code with new commands, agents, and capabilities.

## Other

- [Authentication](authentication.md) - Learn how to configure user authentication and credential management for Claude Code in your organization.
- [Claude Code in Slack](slack.md) - Delegate coding tasks directly from your Slack workspace
- [Claude Code on the web](claude-code-on-the-web.md) - Run Claude Code tasks asynchronously on secure cloud infrastructure
- [Create and distribute a plugin marketplace](plugin-marketplaces.md) - Build and host plugin marketplaces to distribute Claude Code extensions across teams and communities.
- [Create custom subagents](sub-agents.md) - Create and use specialized AI subagents in Claude Code for task-specific workflows and improved context management.
- [Customize keyboard shortcuts](keybindings.md) - Customize keyboard shortcuts in Claude Code with a keybindings configuration file.
- [Enterprise deployment overview](third-party-integrations.md) - Learn how Claude Code can integrate with various third-party services and infrastructure to meet enterprise deployment requirements.
- [Enterprise network configuration](network-config.md) - Configure Claude Code for enterprise environments with proxy servers, custom Certificate Authorities (CA), and mutual Transport Layer Security (mTLS) authentication.
- [Extend Claude with skills](skills.md) - Create, manage, and share skills to extend Claude's capabilities in Claude Code. Includes custom slash commands.
- [How Claude Code works](how-claude-code-works.md) - Understand the agentic loop, built-in tools, and how Claude Code interacts with your project.
- [Interactive mode](interactive-mode.md) - Complete reference for keyboard shortcuts, input modes, and interactive features in Claude Code sessions.
- [LLM gateway configuration](llm-gateway.md) - Learn how to configure Claude Code to work with LLM gateway solutions. Covers gateway requirements, authentication configuration, model selection, and provider-specific endpoint setup.
- [Legal and compliance](legal-and-compliance.md) - Legal agreements, compliance certifications, and security information for Claude Code.
- [Model configuration](model-config.md) - Learn about the Claude Code model configuration, including model aliases like `opusplan`
- [Optimize your terminal setup](terminal-config.md) - Claude Code works best when your terminal is properly configured. Follow these guidelines to optimize your experience.
- [Output styles](output-styles.md) - Adapt Claude Code for uses beyond software engineering
- [Plugins reference](plugins-reference.md) - Complete technical reference for Claude Code plugin system, including schemas, CLI commands, and component specifications.
- [Status line configuration](statusline.md) - Create a custom status line for Claude Code to display contextual information
- [Troubleshooting](troubleshooting.md) - Discover solutions to common issues with Claude Code installation and usage.
