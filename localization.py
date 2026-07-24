"""
localization.py
Централізований словник локалізації для CoreControl MultiTool.
Підтримувані мови: ua (Українська), en (English), ru (Русский).
"""

import re

LANGUAGES = ["ua", "en", "ru"]

STRINGS = {
    "app_title": {
        "ua": "CoreControl MultiTool",
        "en": "CoreControl MultiTool",
        "ru": "CoreControl MultiTool",
    },
    # Вкладки
    "tab_monitor": {"ua": "Монітор системи", "en": "System Monitor", "ru": "Монитор системы"},
    "tab_network": {"ua": "Сканер мережі", "en": "Network Scanner", "ru": "Сканер сети"},
    "tab_thermometer": {"ua": "Термометр", "en": "Thermometer", "ru": "Термометр"},
    "tab_tools": {"ua": "Швидкі утиліти", "en": "Quick Tools", "ru": "Быстрые утилиты"},
    "tab_settings": {"ua": "Налаштування", "en": "Settings", "ru": "Настройки"},

    # System Monitor
    "cpu_load": {"ua": "Завантаження CPU", "en": "CPU Load", "ru": "Загрузка CPU"},
    "cpu_temp": {"ua": "Температура CPU", "en": "CPU Temperature", "ru": "Температура CPU"},
    "temp_unavailable": {"ua": "Недоступно", "en": "Unavailable", "ru": "Недоступно"},
    "ram_usage": {"ua": "Оперативна пам'ять (RAM)", "en": "Memory (RAM)", "ru": "Оперативная память (RAM)"},
    "disks": {"ua": "Диски", "en": "Disks", "ru": "Диски"},
    "network_speed": {"ua": "Мережа", "en": "Network", "ru": "Сеть"},
    "download": {"ua": "Завантаження", "en": "Download", "ru": "Загрузка"},
    "upload": {"ua": "Віддача", "en": "Upload", "ru": "Отдача"},
    "alert_ram": {
        "ua": "УВАГА: використання RAM перевищує 90%!",
        "en": "WARNING: RAM usage exceeds 90%!",
        "ru": "ВНИМАНИЕ: использование RAM превышает 90%!",
    },
    "alert_temp": {
        "ua": "УВАГА: висока температура CPU!",
        "en": "WARNING: high CPU temperature!",
        "ru": "ВНИМАНИЕ: высокая температура CPU!",
    },

    # Thermometer
    "sensors_title": {"ua": "Усі температурні датчики", "en": "All Temperature Sensors", "ru": "Все датчики температуры"},
    "col_sensor": {"ua": "Датчик", "en": "Sensor", "ru": "Датчик"},
    "col_value": {"ua": "Значення", "en": "Value", "ru": "Значение"},
    "col_limit": {"ua": "Критично при", "en": "Critical at", "ru": "Критично при"},
    "no_sensors": {
        "ua": "Датчики температури не знайдено на цій системі (можливо, потрібні додаткові драйвери, напр. lm-sensors на Linux).",
        "en": "No temperature sensors found on this system (may require additional drivers, e.g. lm-sensors on Linux).",
        "ru": "Датчики температуры не найдены в этой системе (возможно, нужны дополнительные драйверы, напр. lm-sensors на Linux).",
    },
    "refresh_button": {"ua": "Оновити", "en": "Refresh", "ru": "Обновить"},

    # Дружні назви датчиків (маппінг сирих імен від psutil/nvidia-smi)
    "sensor_motherboard": {"ua": "Материнська плата", "en": "Motherboard", "ru": "Материнская плата"},
    "sensor_cpu_package": {"ua": "Процесор (Загальна)", "en": "CPU (Overall)", "ru": "Процессор (Общая)"},
    "sensor_cpu_core": {"ua": "Ядро", "en": "Core", "ru": "Ядро"},
    "sensor_nvme": {"ua": "SSD/NVMe диск", "en": "SSD/NVMe Drive", "ru": "SSD/NVMe диск"},
    "sensor_gpu": {"ua": "Відеокарта", "en": "GPU", "ru": "Видеокарта"},

    # Network Scanner
    "current_subnet": {"ua": "Поточна підмережа", "en": "Current subnet", "ru": "Текущая подсеть"},
    "scan_button": {"ua": "Сканувати мережу", "en": "Scan Network", "ru": "Сканировать сеть"},
    "scanning": {"ua": "Сканування...", "en": "Scanning...", "ru": "Сканирование..."},
    "scan_done": {"ua": "Сканування завершено", "en": "Scan complete", "ru": "Сканирование завершено"},
    "col_ip": {"ua": "IP-адреса", "en": "IP Address", "ru": "IP-адрес"},
    "col_status": {"ua": "Статус", "en": "Status", "ru": "Статус"},
    "col_ping": {"ua": "Пінг (мс)", "en": "Ping (ms)", "ru": "Пинг (мс)"},
    "status_online": {"ua": "Онлайн", "en": "Online", "ru": "Онлайн"},

    # Quick Tools
    "tool_taskmgr": {"ua": "Диспетчер завдань", "en": "Task Manager", "ru": "Диспетчер задач"},
    "tool_scheduler": {"ua": "Планувальник завдань", "en": "Task Scheduler", "ru": "Планировщик заданий"},
    "tool_diskmgmt": {"ua": "Керування дисками", "en": "Disk Management", "ru": "Управление дисками"},
    "tool_terminal": {"ua": "Термінал / Консоль", "en": "Terminal / Console", "ru": "Терминал / Консоль"},
    "tool_launch_failed": {
        "ua": "Не вдалося запустити утиліту",
        "en": "Failed to launch utility",
        "ru": "Не удалось запустить утилиту",
    },

    # Settings
    "language_label": {"ua": "Мова інтерфейсу", "en": "Interface Language", "ru": "Язык интерфейса"},
    "appearance_label": {"ua": "Тема оформлення", "en": "Appearance", "ru": "Тема оформления"},
    "about_label": {"ua": "Про програму", "en": "About", "ru": "О программе"},
    "about_text": {
        "ua": "CoreControl MultiTool — крос-платформений інструмент моніторингу та діагностики системи.",
        "en": "CoreControl MultiTool — a cross-platform system monitoring and diagnostics tool.",
        "ru": "CoreControl MultiTool — кроссплатформенный инструмент мониторинга и диагностики системы.",
    },
    "promo_banner": {
        "ua": "Також спробуйте MinerFinder!",
        "en": "Also try MinerFinder!",
        "ru": "Также попробуйте MinerFinder!",
    },
}


def t(key: str, lang: str) -> str:
    """Повертає перекладений рядок за ключем та мовою (з фолбеком на EN)."""
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("en", key))


# Патерни сирих назв датчиків, які видає psutil.sensors_temperatures()
# (залежать від платформи/чипсета) -> зрозумілі локалізовані назви.
_RE_PACKAGE = re.compile(r"^package\s*id\s*(\d+)$", re.IGNORECASE)
_RE_CORE = re.compile(r"^core\s*(\d+)$", re.IGNORECASE)
_RE_ACPITZ = re.compile(r"^acpitz\s*(\d*)$", re.IGNORECASE)


def translate_sensor_label(group: str, label: str, lang: str) -> str:
    """Перетворює технічну назву датчика (напр. 'Package id 0', 'Core 3',
    'acpitz 1') на зрозумілу локалізовану назву (напр. 'Процесор (Загальна)',
    'Ядро 3', 'Материнська плата 1').

    group -- назва чипа/групи датчиків від psutil (напр. 'coretemp', 'acpitz')
    label -- назва конкретного показника (напр. 'Package id 0', 'Core 0'),
             або вже згенерований фолбек виду '<group> <номер>', якщо у
             самого датчика немає власної мітки.
    """
    group = (group or "").strip()
    label = (label or "").strip()

    # Материнська плата / загальні ACPI термозони (плата, шасі тощо)
    m = _RE_ACPITZ.match(label) or _RE_ACPITZ.match(group)
    if m:
        base = t("sensor_motherboard", lang)
        idx = m.group(1)
        return f"{base} {idx}" if idx else base

    # Процесор — сумарний показник пакета
    m = _RE_PACKAGE.match(label)
    if m:
        idx = m.group(1)
        base = t("sensor_cpu_package", lang)
        return base if idx == "0" else f"{base} {idx}"

    # Процесор — окреме фізичне ядро
    m = _RE_CORE.match(label)
    if m:
        return f"{t('sensor_cpu_core', lang)} {m.group(1)}"

    # NVMe / SSD диски
    if "nvme" in group.lower() or "nvme" in label.lower():
        return f"{t('sensor_nvme', lang)} — {label}" if label else t("sensor_nvme", lang)

    # GPU (NVIDIA через nvidia-smi вже приходить із власною читабельною назвою)
    if group.lower() == "nvidia_gpu":
        return label

    # coretemp/k10temp без власної мітки -> трактуємо як загальний процесор
    if group.lower() in ("coretemp", "k10temp", "cpu_thermal") and not label:
        return t("sensor_cpu_package", lang)

    # Фолбек: повертаємо оригінальну назву як є
    return label or group