import json
from pathlib import Path

from app.models import Service

CONFIG_DIR = Path.home() / ".devlauncher"
CONFIG_FILE = CONFIG_DIR / "services.json"


def load_services() -> list:
    if not CONFIG_FILE.exists():
        return []
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return [Service.from_dict(item) for item in data]
    except (json.JSONDecodeError, OSError, TypeError):
        return []


def save_services(services: list) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = [s.to_dict() for s in services]
    CONFIG_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
