# DevLauncher

Start/stop databases, dev servers, system services and Docker containers from one place.

    pip install -r requirements.txt
    python main.py

Service types
- Command   : any shell command (npm run dev, uvicorn main:app --reload, ...). Auto-detects a
              .venv / venv / env folder inside the working directory, or use a custom venv path.
- systemd   : installed services (mysql, postgresql, redis-server, docker, nginx...). Uses pkexec
              (graphical password prompt) to start/stop.
- docker    : an existing container (docker start / stop, live `docker logs -f`).

Config is stored in ~/.devlauncher/services.json
