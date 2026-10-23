<h1 align="center">⚡ DevLauncher</h1>

<p align="center">
  <i>One place to start, stop, and watch all your dev services.</i>
</p>

<p align="center">
  <a href="#-features">Features</a> ·
  <a href="#-quick-start">Quick Start</a> ·
  <a href="#-service-types">Service Types</a> ·
  <a href="#-configuration">Configuration</a> ·
  <a href="#-troubleshooting">Troubleshooting</a>
</p>

---

> **DevLauncher** is a small desktop app that lets you manage every part of your
> local development setup from one window — **shell commands**, **systemd
> services**, and **existing Docker containers** — without juggling terminal
> tabs.

---

## ✦ Features

```
🚀  Command services      Run any shell command — npm run dev, uvicorn main:app, etc.
🐍  Venv detection        Finds .venv / venv / env automatically — no activate step
⚙️   systemd services      Start/stop MySQL, PostgreSQL, Redis, Docker, Nginx via pkexec
🐳  Docker containers      Control existing containers and stream docker logs -f
📄  Per-service logs       Each service gets its own log window (copy, clear, auto-scroll)
💾  Local config           Single JSON file — no database, no setup, no cloud
🌗  Dark UI                Clean, minimal, distraction-free interface
```

---

## ✦ Requirements

| Need | Why |
|---|---|
| **Python 3.10+** | To run the app |
| **pip** | To install dependencies |
| **Docker** *(optional)* | Only for Docker container services |
| **systemd + pkexec** *(optional)* | Only for systemd services (`sudo apt install policykit-1`) |

---

## ✦ Quick Start

```bash
# 1. Clone
git clone https://github.com/<your-username>/devlauncher.git
cd devlauncher

# 2. Install
pip install -r requirements.txt

# 3. Run
python main.py
```

That's it. The window opens and you can start adding services.

---

## ✦ Service Types

DevLauncher works with three kinds of services. Pick what fits your workflow.

### 🖥 Command

Runs any shell command in a working directory.

```
Command:        npm run dev
Working dir:    ~/projects/web
Venv:           .venv        (optional — auto-detected)
Stop command:   (optional)   for apps that daemonize
```

> Great for: Vite, Next.js, FastAPI, Flask, Rails, Celery, custom scripts.

---

### ⚙️ systemd

Manages installed system services through `pkexec` (graphical password prompt).

```
Service name:   mysql | postgresql | redis-server | docker | nginx
Action:         pkexec systemctl start <name>
                pkexec systemctl stop  <name>
```

> Status is read from `systemctl is-active <service>`.
> ⚠️ Needs a graphical session — `pkexec` won't prompt over plain SSH.

---

### 🐳 Docker

Controls **existing** containers (DevLauncher does not create new ones).

```
Container name: redis-dev | postgres-local | my-api
Action:         docker start <container>
                docker stop  <container>
Logs:           docker logs -f <container>
```

> Create the container once with `docker run -d --name <name> ...`,
> then register it in DevLauncher and manage it with one click.


## ✦ How It Works

**Command services** run in their own process group, so stopping a service
kills the entire tree — no orphaned `uvicorn` or `node` processes holding
ports in the background.

**Virtual environments** are detected automatically. If `.venv`, `venv`, or
`env` exists in the working directory, its `bin/` (or `Scripts/` on Windows)
is prepended to `PATH` and `VIRTUAL_ENV` is exported. This means
`uvicorn main:app` just works without any `source activate`.

**systemd services** are managed through `pkexec`, which gives a clean
graphical password prompt. Live status comes from `systemctl is-active`.

**Docker containers** are controlled via the standard `docker` CLI, and logs
stream in real time through `docker logs -f`.

---

## ✦ Project Structure

```
devlauncher/
├── main.py                     # entry point
├── requirements.txt
├── README.md
├── assets/
│   ├── icon.png
│   └── logo.jpg
├── app/
│   ├── styles.py               # Qt stylesheet
│   ├── core/                   # 🧠 business logic (no Qt imports)
│   │   ├── models.py
│   │   ├── storage.py
│   │   └── process_manager.py
│   └── ui/                     # 🖼 presentation only (no process logic)
│       ├── main_window.py
│       ├── sidebar.py
│       ├── service_card.py
│       ├── add_service_dialog.py
│       └── log_window.py
└── install-local.sh            # Linux installer (optional)
```

> **Rule of thumb:** `core/` decides, `ui/` shows. Keep that line clean and
> the app stays easy to extend.

---

## ✦ Troubleshooting

| Problem | Fix |
|---|---|
| `pkexec` prompts don't appear | Make sure you're in a graphical session |
| systemd service won't start | Check `systemctl status <service>` |
| Docker container won't start | Confirm it exists: `docker ps -a` |
| Command says "not found" | Set the venv field, or use the full binary path |
| Log window stays empty | Some apps buffer output — try `PYTHONUNBUFFERED=1` |
| Port already in use | `kill -9 $(lsof -t -i :PORT)` |

---

## ✦ Contributing

Pull requests are welcome. For bigger changes, open an issue first.

```bash
git clone https://github.com/<your-username>/devlauncher.git
cd devlauncher
pip install -r requirements.txt
python main.py
```

Guidelines:

- No Qt imports inside `core/`
- No process/filesystem logic inside `ui/`
- Test all three service types before submitting

---
