"""Finds apps that are already installed on this machine."""
import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class Detected:
    name: str
    kind: str                 # command | systemd | docker
    category: str
    target: str = ""
    command: str = ""
    detail: str = ""

    @property
    def key(self) -> tuple:
        return (self.kind, self.command if self.kind == "command" else self.target)


# (systemd unit, display name, category)
KNOWN_UNITS = [
    ("docker", "Docker Engine", "Docker"),
    ("mysql", "MySQL", "Database"),
    ("mysqld", "MySQL", "Database"),
    ("mariadb", "MariaDB", "Database"),
    ("postgresql", "PostgreSQL", "Database"),
    ("redis-server", "Redis", "Database"),
    ("redis", "Redis", "Database"),
    ("mongod", "MongoDB", "Database"),
    ("elasticsearch", "Elasticsearch", "Database"),
    ("memcached", "Memcached", "Database"),
    ("rabbitmq-server", "RabbitMQ", "Dev Server"),
    ("mosquitto", "Mosquitto (MQTT)", "Dev Server"),
    ("nginx", "Nginx", "Web Server"),
    ("apache2", "Apache", "Web Server"),
    ("httpd", "Apache", "Web Server"),
]

# user-level units (systemctl --user)
KNOWN_USER_UNITS = [
    ("docker-desktop", "Docker Desktop", "Docker"),
]

# (binary, display name, command, category) - for tools that run as a normal command
PATH_TOOLS = [
    ("redis-server", "Redis", "redis-server", "Database"),
    ("mongod", "MongoDB", "mongod", "Database"),
    ("ollama", "Ollama", "ollama serve", "Dev Server"),
    ("jupyter", "Jupyter Lab", "jupyter lab", "Dev Server"),
    ("nginx", "Nginx", 'nginx -g "daemon off;"', "Web Server"),
]


def _run(argv, timeout=5):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except (OSError, subprocess.TimeoutExpired):
        return -1, "", ""


def detect_systemd() -> list:
    if not shutil.which("systemctl"):
        return []
    _, out, _ = _run(["systemctl", "list-unit-files", "--type=service", "--no-legend", "--no-pager"])
    units = {line.split()[0].removesuffix(".service") for line in out.splitlines() if line.strip()}
    found, seen = [], set()
    for unit, name, category in KNOWN_UNITS:
        if unit in units and name not in seen:
            seen.add(name)
            found.append(Detected(name, "systemd", category, target=unit, detail=f"systemd unit: {unit}"))
    return found


def detect_systemd_user() -> list:
    if not shutil.which("systemctl"):
        return []
    _, out, _ = _run(["systemctl", "--user", "list-unit-files", "--type=service", "--no-legend", "--no-pager"])
    units = {line.split()[0].removesuffix(".service") for line in out.splitlines() if line.strip()}
    return [
        Detected(name, "systemd-user", category, target=unit, detail=f"user service: {unit}")
        for unit, name, category in KNOWN_USER_UNITS if unit in units
    ]


def detect_docker() -> tuple:
    if not shutil.which("docker"):
        return [], []
    code, out, err = _run(
        ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Image}}\t{{.State}}"], timeout=8
    )
    if code != 0:
        if "permission denied" in err.lower():
            note = ("Docker is installed but your user can't access it. Run: "
                    "sudo usermod -aG docker $USER  (then log out and back in).")
        else:
            note = ("Docker CLI found, but no Docker engine is reachable. Start Docker Desktop (or the engine) "
                    "from DevLauncher, run `docker context use desktop-linux` if needed, then detect again.")
        return [], [note]
    found = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0]:
            found.append(Detected(parts[0], "docker", "Docker", target=parts[0],
                                  detail=f"container · image: {parts[1]}"))
    return found, []


def detect_path_tools(skip_names: set) -> list:
    found = []
    for binary, name, command, category in PATH_TOOLS:
        if name not in skip_names and shutil.which(binary):
            found.append(Detected(name, "command", category, command=command,
                                  detail=f"found on PATH: {binary}"))
    return found


def detect_all() -> tuple:
    systemd = detect_systemd() + detect_systemd_user()
    containers, notes = detect_docker()
    tools = detect_path_tools({d.name for d in systemd})
    return systemd + tools + containers, notes
