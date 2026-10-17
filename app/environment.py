"""Builds the environment a service runs in (venv + PATH + env vars).

This is the fix for "uvicorn: not found": the launcher used to run commands with
its OWN PATH. Now each service gets its project's venv on PATH, and the
launcher's own venv is removed so it never leaks into your apps.
"""
import os
import sys
from pathlib import Path

from PySide6.QtCore import QProcessEnvironment

VENV_NAMES = (".venv", "venv", "env")


def bin_dir(venv: Path) -> Path:
    return venv / ("Scripts" if sys.platform == "win32" else "bin")


def _is_venv(path: Path) -> bool:
    exe = "python.exe" if sys.platform == "win32" else "python"
    return (bin_dir(path) / exe).exists()


def find_venv(working_dir: str, explicit: str = ""):
    if explicit:
        path = Path(explicit).expanduser()
        return path if _is_venv(path) else None
    if working_dir:
        base = Path(working_dir).expanduser()
        for name in VENV_NAMES:
            if _is_venv(base / name):
                return base / name
    return None


def _norm(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


def build_environment(service):
    env = QProcessEnvironment.systemEnvironment()
    sep = os.pathsep
    paths = [p for p in env.value("PATH").split(sep) if p]

    # DevLauncher itself runs inside a venv -> don't leak it into child apps
    if sys.prefix != sys.base_prefix:
        own_bin = _norm(str(bin_dir(Path(sys.prefix))))
        paths = [p for p in paths if _norm(p) != own_bin]
        env.remove("VIRTUAL_ENV")

    venv = find_venv(service.working_dir, service.venv)
    if venv:
        paths.insert(0, str(bin_dir(venv)))
        env.insert("VIRTUAL_ENV", str(venv))
        env.remove("PYTHONHOME")

    env.insert("PATH", sep.join(paths))
    env.insert("PYTHONUNBUFFERED", "1")  # python logs show up live, not in bursts
    for key, value in service.env.items():
        env.insert(key, value)
    return env, venv
