"""Set DEJAVU_API_KEY at OS level for HTTP-native MCP clients.

Three mechanisms per OS:
- macOS: launchctl setenv (GUI apps need this; shell export is invisible to them)
- Windows: setx (writes registry; new processes only)
- Linux: ~/.profile (sourced by display manager on login)

NOTE: VS Code uses its own `inputs` mechanism — skip env for that client.
"""
import os
import platform
import subprocess
from pathlib import Path


def set_env(api_key: str) -> None:
    """Set DEJAVU_API_KEY persistently across GUI launches."""
    system = platform.system()
    
    if system == "Darwin":
        subprocess.run(
            ["launchctl", "setenv", "DEJAVU_API_KEY", api_key],
            check=True,
        )
        print("✓ Set DEJAVU_API_KEY via launchctl")
        print("  Note: may require logout/relaunch to take effect in GUI apps")
    
    elif system == "Windows":
        subprocess.run(
            ["setx", "DEJAVU_API_KEY", api_key],
            check=True,
            shell=True,
        )
        print("✓ Set DEJAVU_API_KEY via setx (effective in new shells)")
    
    elif system == "Linux":
        profile = Path.home() / ".profile"
        marker = "# Dejavu API key"
        line = f'export DEJAVU_API_KEY="{api_key}"  {marker}'
        
        existing = profile.read_text() if profile.exists() else ""
        if marker in existing:
            lines = [l for l in existing.split("\n") if marker not in l]
            existing = "\n".join(lines)
        profile.write_text(existing.rstrip("\n") + f"\n{line}\n")
        print(f"✓ Added DEJAVU_API_KEY to {profile}")
    
    # Also set in current shell
    os.environ["DEJAVU_API_KEY"] = api_key


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        set_env(sys.argv[1])
    else:
        print("Usage: python os_env.py <api_key>")
        print(f"Current DEJAVU_API_KEY: {os.environ.get('DEJAVU_API_KEY', 'not set')}")
