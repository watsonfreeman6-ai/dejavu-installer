"""Device identity: random UUID, persisted to ~/.dejavu/device_id.

NOT hardware-derived. Avoids cloud VM machine-ID collisions (DigitalOcean droplets
cloned from same snapshot share SMBIOS UUID). Stable per install, no PII.
"""
import uuid
from pathlib import Path

DEJAVU_HOME = Path.home() / ".dejavu"
DEVICE_ID_PATH = DEJAVU_HOME / "device_id"


def get_device_id() -> str:
    """Return stable device ID. Generates one on first call."""
    if DEVICE_ID_PATH.exists():
        return DEVICE_ID_PATH.read_text().strip()
    
    DEJAVU_HOME.mkdir(parents=True, exist_ok=True)
    device_id = str(uuid.uuid4())
    DEVICE_ID_PATH.write_text(device_id + "\n")
    return device_id


if __name__ == "__main__":
    print(get_device_id())
