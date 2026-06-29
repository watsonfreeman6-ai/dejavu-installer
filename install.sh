#!/usr/bin/env bash
# Dejavu — AI Skills Marketplace Installer
# MIT Licensed. Installs the Dejavu MCP server config.
# The server and catalog are proprietary. This installer is open-source.
#
# Usage:
#   curl -fsSL https://dejavu.dev/install.sh | sh
#   or
#   bash install.sh
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}Dejavu — AI Skills Marketplace${NC}"
echo "----------------------------------------"

# ── API Key ──────────────────────────────────────────────
if [ -z "${DEJAVU_API_KEY:-}" ]; then
    read -r -p "Enter your Dejavu API key (dk_xxx): " DEJAVU_API_KEY
fi
if [ -z "$DEJAVU_API_KEY" ]; then
    echo -e "${RED}API key required. Get one at https://dejavu.dev/connect${NC}"
    exit 1
fi

# ── Install uv ───────────────────────────────────────────
if ! command -v uv &>/dev/null; then
    echo "Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo -e "${GREEN}✓${NC} uv ready"

# ── Create ~/.dejavu + device_id ─────────────────────────
mkdir -p ~/.dejavu

if [ ! -f ~/.dejavu/device_id ]; then
    python3 -c "
import uuid
from pathlib import Path
Path.home().joinpath('.dejavu', 'device_id').write_text(str(uuid.uuid4()) + '\n')
"
fi
echo -e "${GREEN}✓${NC} Device registered ($(cat ~/.dejavu/device_id | cut -c1-8)...)"

# ── Download catalog ─────────────────────────────────────
CATALOG_URL="https://github.com/dejavu-app/install/releases/latest/download/catalog.db"
echo "Downloading skill catalog..."
if curl -fsSL "$CATALOG_URL" -o ~/.dejavu/catalog.db 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Catalog downloaded"
else
    echo -e "${YELLOW}⚠${NC} Catalog not available yet — will be seeded on first use"
fi

# ── Store API key ────────────────────────────────────────
python3 -c "
import json
from pathlib import Path
config = Path.home() / '.dejavu' / 'config.json'
data = {}
if config.exists():
    data = json.loads(config.read_text())
data['api_key'] = '${DEJAVU_API_KEY}'
config.parent.mkdir(parents=True, exist_ok=True)
config.write_text(json.dumps(data, indent=2))
"
echo -e "${GREEN}✓${NC} API key saved to ~/.dejavu/config.json"

# ── Detect clients ───────────────────────────────────────
echo "Detecting MCP clients..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLIENTS=$(python3 -c "
import sys, json
sys.path.insert(0, '$SCRIPT_DIR/src')
from client_detector import detect_clients
print(json.dumps(detect_clients()))
" 2>/dev/null || echo "{}")

# ── Write configs ────────────────────────────────────────
CONFIGURED=0
echo "$CLIENTS" | python3 -c "
import json, sys
sys.path.insert(0, '$SCRIPT_DIR/src')
from config_writer import write_config
from os_env import set_env

clients = json.loads(sys.stdin.read())
configured = 0
for client, path in clients.items():
    if client == 'claude':
        print('ℹ  Claude Desktop: open Settings → Connectors → paste URL + key')
        continue
    try:
        if write_config(path, client):
            configured += 1
            print(f'✓ Configured {client}')
        else:
            print(f'  {client} already configured — skipped')
    except Exception as e:
        print(f'✗ Failed to configure {client}: {e}')

if configured > 0:
    try:
        set_env('\$DEJAVU_API_KEY')
    except Exception as e:
        print(f'⚠  Could not set OS env var: {e}')
elif len(clients) == 0 or (len(clients) == 1 and 'claude' in clients):
    print('No MCP clients detected.')
    print('')
    print('Add Dejavu manually:')
    print('  URL: https://dejavu.keepingtrack.biz/mcp')
    print('  Header: Authorization: Bearer <your-api-key>')
" 2>/dev/null || echo -e "${YELLOW}⚠${NC} Could not auto-configure clients. Add manually."

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Dejavu installed!${NC}"
echo ""
echo "Your AI agent now has access to:"
echo "  skill_search  — local FTS5, sub-millisecond, always free"
echo "  skill_execute — gated, content cached locally on first use"
echo "  skill_submit  — share your own skills"
echo "  skill_rate    — rate skills you've used"
echo ""
echo "Manage devices: https://dejavu.dev/dashboard"
