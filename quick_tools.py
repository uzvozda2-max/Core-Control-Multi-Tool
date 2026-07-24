"""
quick_tools.py
Модуль запуску стандартних системних утиліт ОС (Windows / Linux).
Кожна функція повертає (success: bool, error_message: str|None).
"""

import platform
import shutil
import subprocess


def _is_windows() -> bool:
    return platform.system().lower() == "windows"


def _run(cmd, use_shell=False):
    try:
        subprocess.Popen(cmd, shell=use_shell)
        return True, None
    except (OSError, FileNotFoundError) as exc:
        return False, str(exc)


def _first_available(candidates):
    """Повертає перший бінарник зі списку, що є в PATH, або None."""
    for c in candidates:
        if shutil.which(c):
            return c
    return None


def open_task_manager():
    if _is_windows():
        return _run(["taskmgr"])
    binary = _first_available(["gnome-system-monitor", "ksysguard", "mate-system-monitor", "xfce4-taskmanager"])
    if binary:
        return _run([binary])
    # Фолбек: 'top' у терміналі
    return open_terminal("top")


def open_task_scheduler():
    if _is_windows():
        return _run(["control", "schedtasks"])
    # Графічні фронтенди для cron, якщо є, інакше редагувати crontab у терміналі
    binary = _first_available(["gnome-schedule", "kcron"])
    if binary:
        return _run([binary])
    return open_terminal("crontab -e")


def open_disk_management():
    if _is_windows():
        return _run(["diskmgmt.msc"], use_shell=True)
    binary = _first_available(["gnome-disks", "gparted", "kde-partitionmanager"])
    if binary:
        return _run([binary])
    return False, "gnome-disks/gparted not found"


def open_terminal(initial_command: str = None):
    if _is_windows():
        if initial_command:
            return _run(["powershell", "-NoExit", "-Command", initial_command])
        return _run(["powershell"])
    binary = _first_available([
        "x-terminal-emulator", "gnome-terminal", "konsole",
        "xfce4-terminal", "mate-terminal", "xterm",
    ])
    if not binary:
        return False, "No terminal emulator found"
    if initial_command:
        if binary == "gnome-terminal":
            return _run([binary, "--", "bash", "-c", f"{initial_command}; exec bash"])
        return _run([binary, "-e", f"bash -c '{initial_command}; exec bash'"])
    return _run([binary])