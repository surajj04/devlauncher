import sys

CATEGORIES = ["Database", "Dev Server", "Web Server", "Docker", "Custom"]
MANAGED_KINDS = ("systemd", "systemd-user", "docker")
ACTIVE_STATES = ("starting", "running")

KIND_LABELS = {
    "command": "Command (npm, python, ...)",
    "systemd": "System service (systemd, asks for password)",
    "systemd-user": "User service (systemctl --user, no password)",
    "docker": "Docker container",
}

PY = "python" if sys.platform == "win32" else "python3"

# preset -> (name, kind, command, target, category, web port)
PRESETS = {
    "Custom command": ("", "command", "", "", "Custom", 0),
    "FastAPI (uvicorn)": ("FastAPI Server", "command", "uvicorn main:app --reload --port 8000", "", "Dev Server", 8000),
    "Node (npm run dev)": ("Node Dev Server", "command", "npm run dev", "", "Dev Server", 3000),
    "Python script": ("Python App", "command", f"{PY} app.py", "", "Dev Server", 0),
    "Docker Compose (up)": ("Docker Compose", "command", "docker compose up", "", "Docker", 0),
    "Docker Desktop": ("Docker Desktop", "systemd-user", "", "docker-desktop", "Docker", 0),
    "Docker Engine (system)": ("Docker Engine", "systemd", "", "docker", "Docker", 0),
    "Docker container": ("", "docker", "", "", "Docker", 0),
    "MySQL": ("MySQL", "systemd", "", "mysql", "Database", 0),
    "PostgreSQL": ("PostgreSQL", "systemd", "", "postgresql", "Database", 0),
    "Redis": ("Redis", "systemd", "", "redis-server", "Database", 0),
    "MongoDB": ("MongoDB", "systemd", "", "mongod", "Database", 0),
    "Nginx": ("Nginx", "systemd", "", "nginx", "Web Server", 80),
}
