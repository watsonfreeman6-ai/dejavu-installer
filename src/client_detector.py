"""Detect installed MCP clients on the user's machine."""
import os
from pathlib import Path
from typing import Dict

CLIENT_PATHS = {
    "claude": [
        Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
        Path(os.environ.get("APPDATA", "")) / "Claude/claude_desktop_config.json",
    ],
    "cursor": [
        Path.home() / ".cursor/mcp.json",
    ],
    "vscode": [
        Path.home() / ".vscode/mcp.json",
        Path.home() / "AppData/Roaming/Code/User/mcp.json",
    ],
    "windsurf": [
        Path.home() / ".codeium/windsurf/mcp_config.json",
    ],
    "continue": [
        Path.home() / ".continue/config.json",
    ],
    "hermes": [
        Path.home() / ".hermes/config.yaml",
    ],
}


def detect_clients() -> Dict[str, str]:
    """Return {client_name: config_file_path} for installed clients."""
    found = {}
    for client, paths in CLIENT_PATHS.items():
        for p in paths:
            if p.exists():
                found[client] = str(p)
                break
    return found


if __name__ == "__main__":
    import json
    print(json.dumps(detect_clients(), indent=2))
