import uuid
from dataclasses import asdict, dataclass, field


@dataclass
class Service:
    name: str
    kind: str = "command"            # command | systemd | docker
    command: str = ""                # kind == command
    working_dir: str = ""            # kind == command
    venv: str = ""                   # kind == command; "" = auto-detect
    env: dict = field(default_factory=dict)
    target: str = ""                 # systemd unit / docker container name
    category: str = "Custom"
    port: int = 0                    # optional web port -> "Open" button
    auto_start: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Service":
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in allowed})

    @property
    def subtitle(self) -> str:
        if self.kind == "systemd":
            return f"systemd service · {self.target}"
        if self.kind == "systemd-user":
            return f"user service · {self.target}"
        if self.kind == "docker":
            return f"docker container · {self.target}"
        return self.command


def parse_env(text: str) -> dict:
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def format_env(env: dict) -> str:
    return "\n".join(f"{k}={v}" for k, v in env.items())
