# Dejavu — AI Agent Skills Marketplace

**Install Dejavu on any MCP-compatible AI agent with zero friction.**

[![Add to Cursor](https://img.shields.io/badge/Add_to-Cursor-6C4DFF?style=for-the-badge)](https://dejavu.dev/connect)
[![Add to Claude](https://img.shields.io/badge/Add_to-Claude-D97757?style=for-the-badge)](https://dejavu.dev/connect)
[![Add to VS Code](https://img.shields.io/badge/Add_to-VS_Code-007ACC?style=for-the-badge)](https://dejavu.dev/connect)

> **One click from the [success page](https://dejavu.dev/connect) after subscribing ($6.67/mo).**

Or install from terminal:

```bash
curl -fsSL https://dejavu.dev/install.sh | sh
```

Or via Smithery:

```bash
npx @smithery/cli install dejavu
```

---

## What You Get

| Tool | Description | Auth |
|------|-------------|------|
| `skill_search` | Local FTS5 search, sub-millisecond | None |
| `skill_execute` | Fetch and run skills (content cached locally) | Session JWT |
| `skill_list` | Browse by category | None |
| `skill_get` | Full skill metadata | None |
| `skill_categories` | Available categories | None |
| `skill_submit` | Submit your own skills | Session JWT |
| `skill_rate` | Rate skills you've used | Session JWT |
| `skill_install` | Explicitly install a skill | Session JWT |
| `scan_local_skills` | Scan your machine for skill files | None |
| `savings_summary` | View your token savings | Session JWT |
| `subscription_status` | Check subscription + earnings | Session JWT |

---

## Supported MCP Clients

| Client | Install Method |
|--------|---------------|
| **Claude Desktop** | Settings → Connectors → paste URL + key |
| **Cursor** | One-click deep link from success page |
| **VS Code** | One-click deep link from success page (`servers` + `inputs`) |
| **Windsurf** | `curl \| sh` installer |
| **Hermes** | `curl \| sh` installer (auto-detects `~/.hermes/config.yaml`) |
| **Continue.dev** | `curl \| sh` installer |
| **Any stdio client** | `mcp-remote` bridge via `npx` |

---

## Manual Config (Any Client)

```json
{
  "mcpServers": {
    "dejavu": {
      "url": "https://dejavu.keepingtrack.biz/mcp",
      "headers": {
        "Authorization": "Bearer ${DEJAVU_API_KEY}"
      }
    }
  }
}
```

---

## Open Source

This installer repository is **MIT licensed**. The Dejavu MCP server and skill catalog are proprietary.

- **Installer:** [github.com/dejavu-app/install](https://github.com/dejavu-app/install) (MIT)
- **Service:** [dejavu.keepingtrack.biz](https://dejavu.keepingtrack.biz) (Proprietary)

---

## License

MIT — see [LICENSE](LICENSE)
