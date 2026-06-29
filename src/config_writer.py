"""Write Dejavu MCP config into detected client config files.

Key differences per client:
- VS Code: `servers` key (not `mcpServers`) + `inputs` array for secrets
- Hermes: YAML format in `mcp.servers`
- Claude Desktop: SKIPPED entirely (user does this in Connectors UI)
- Everyone else: `mcpServers` JSON with env var interpolation
"""
import json
import shutil
from pathlib import Path
from typing import Dict, Optional

DEJAVU_URL = "https://dejavu.keepingtrack.biz/mcp"

STDIO_CONFIG = {
    "command": "npx",
    "args": ["-y", "mcp-remote", DEJAVU_URL],
}

HTTP_CONFIG_TEMPLATE = {
    "url": DEJAVU_URL,
    "headers": {"Authorization": "Bearer ${DEJAVU_API_KEY}"},
}

VSCODE_CONFIG_TEMPLATE = {
    "type": "http",
    "url": DEJAVU_URL,
    "headers": {"Authorization": "Bearer ${input:dejavuApiKey}"},
}


def get_config(client: str, api_key: Optional[str] = None) -> dict:
    """Return the correct MCP server config block for this client."""
    if client == "claude":
        return {"note": "Open Claude Settings → Connectors → paste URL and API key"}
    
    if client == "vscode":
        return VSCODE_CONFIG_TEMPLATE.copy()
    
    if client in ("cursor", "windsurf", "hermes", "continue"):
        config = HTTP_CONFIG_TEMPLATE.copy()
        if api_key:
            config["headers"]["Authorization"] = f"Bearer {api_key}"
        return config
    
    config = STDIO_CONFIG.copy()
    if api_key:
        config["env"] = {"DEJAVU_API_KEY": api_key}
    return config


def write_hermes_config(config_path: str, api_key: Optional[str] = None) -> bool:
    """Write Dejavu MCP server into Hermes config.yaml."""
    import yaml
    path = Path(config_path)
    existing = {}
    if path.exists():
        existing = yaml.safe_load(path.read_text()) or {}
    
    mcp = existing.setdefault("mcp", {})
    servers = mcp.setdefault("servers", {})
    if "dejavu" in servers:
        return False
    
    shutil.copy2(path, path.with_suffix(".yaml.bak"))
    servers["dejavu"] = {
        "url": DEJAVU_URL,
        "headers": {"Authorization": f"Bearer {api_key}"} if api_key else {"Authorization": "Bearer ${DEJAVU_API_KEY}"},
    }
    path.write_text(yaml.dump(existing, default_flow_style=False, allow_unicode=True))
    return True


def write_vscode_config(config_path: str) -> bool:
    """Write VS Code mcp.json with `servers` + `inputs` for secrets."""
    path = Path(config_path)
    existing = {}
    if path.exists():
        existing = json.loads(path.read_text())
    
    if "dejavu" in existing.get("servers", {}):
        return False
    
    shutil.copy2(path, path.with_suffix(".json.bak"))
    
    existing.setdefault("servers", {})["dejavu"] = VSCODE_CONFIG_TEMPLATE
    
    # Add inputs if not present
    inputs = existing.setdefault("inputs", [])
    existing_input_ids = {i.get("id") for i in inputs}
    if "dejavuApiKey" not in existing_input_ids:
        inputs.append({
            "id": "dejavuApiKey",
            "type": "promptString",
            "password": True,
            "description": "Your Dejavu API key (dk_xxx)",
        })
    
    path.write_text(json.dumps(existing, indent=2))
    return True


def write_config(config_path: str, client: str, api_key: Optional[str] = None) -> bool:
    """Patch client config file with Dejavu entry. Idempotent. Backs up before writing."""
    path = Path(config_path)
    
    if client == "hermes":
        return write_hermes_config(config_path, api_key)
    if client == "vscode":
        return write_vscode_config(config_path)
    if client == "claude":
        return False  # User handles this in Connectors UI
    
    existing = {}
    if path.exists():
        existing = json.loads(path.read_text())
    
    servers = existing.get("mcpServers", {})
    if "dejavu" in servers:
        return False
    
    shutil.copy2(path, path.with_suffix(".json.bak"))
    servers["dejavu"] = get_config(client, api_key)
    existing["mcpServers"] = servers
    path.write_text(json.dumps(existing, indent=2))
    return True
