# DevLauncher

DevLauncher gives you one place to start and stop development commands, systemd services, and existing Docker containers.

## Features

- **Command services** — Run shell commands such as `npm run dev` or `uvicorn main:app --reload`.
- **Virtual environment detection** — Automatically looks for `.venv`, `venv`, or `env` in the command's working directory. You can also provide a custom virtual environment path.
- **systemd services** — Manage installed services such as MySQL, PostgreSQL, Redis, Docker, or Nginx. Starting and stopping services uses `pkexec` for a graphical authentication prompt.
- **Docker containers** — Start or stop existing containers and follow their logs with `docker logs -f`.
- **Local configuration** — Service configuration is stored in `~/.devlauncher/services.json`.

## Requirements

- Python and pip
- Docker, for Docker container services
- systemd and `pkexec`, for systemd services

## Getting started

From the project directory, install the Python dependencies and launch the application:

```bash
pip install -r requirements.txt
python main.py
```

## Service types

| Type | What it does | Examples |
| --- | --- | --- |
| Command | Runs a shell command in its working directory; can use an automatically detected or custom virtual environment. | `npm run dev`, `uvicorn main:app --reload` |
| systemd | Starts or stops an installed system service through `pkexec`. | `mysql`, `postgresql`, `redis-server`, `docker`, `nginx` |
| Docker | Starts or stops an existing container and supports live container logs. | Existing Docker containers |

## Configuration

DevLauncher stores service configuration at:

```text
~/.devlauncher/services.json
```


