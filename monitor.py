"""
monitor.py
Модуль опитування апаратних показників системи (CPU, RAM, диски, мережа).
Використовує psutil, працює однаково на Windows та Linux.
"""

import shutil
import subprocess
import time
import psutil


class SystemMonitor:
    """Клас для опитування показників заліза з підтримкою кешування
    для розрахунку мережевої швидкості (дельта байтів / дельта часу)."""

    def __init__(self):
        self._last_net = psutil.net_io_counters()
        self._last_time = time.time()

    # ---------- CPU ----------
    @staticmethod
    def get_cpu_percent() -> float:
        return psutil.cpu_percent(interval=None)

    @staticmethod
    def get_cpu_temperature():
        """Повертає температуру CPU в °C, якщо доступна, інакше None.
        Датчики залежать від платформи: на Windows часто недоступні
        без додаткових драйверів, на Linux зазвичай є через lm-sensors."""
        try:
            temps = psutil.sensors_temperatures()
        except (AttributeError, NotImplementedError):
            return None
        if not temps:
            return None
        # Пріоритетні назви датчиків для CPU
        for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
            if key in temps and temps[key]:
                return temps[key][0].current
        # Фолбек: перший доступний датчик
        for entries in temps.values():
            if entries:
                return entries[0].current
        return None

    @staticmethod
    def get_all_temperatures():
        """Повертає список усіх доступних температурних датчиків системи:
        CPU-ядра, чипсет/материнська плата, NVMe/SSD диски, вентилятори
        з термо-прив'язкою тощо (через psutil.sensors_temperatures()),
        а також GPU (NVIDIA, якщо встановлено nvidia-smi).
        Кожен елемент: {group, label, current, high, critical}.
        На Windows psutil.sensors_temperatures() найчастіше повертає
        порожній результат без додаткових драйверів (OpenHardwareMonitor
        тощо) — це обмеження платформи, а не помилка коду."""
        sensors = []
        try:
            temps = psutil.sensors_temperatures()
        except (AttributeError, NotImplementedError):
            temps = {}

        for chip_name, entries in (temps or {}).items():
            for idx, entry in enumerate(entries):
                label = entry.label or f"{chip_name} {idx + 1}"
                sensors.append({
                    "group": chip_name,
                    "label": label,
                    "current": entry.current,
                    "high": entry.high,
                    "critical": entry.critical,
                })

        sensors.extend(SystemMonitor._get_nvidia_gpu_temps())
        return sensors

    @staticmethod
    def _get_nvidia_gpu_temps():
        """Температура GPU через nvidia-smi (якщо присутній у PATH).
        Працює однаково на Windows і Linux, якщо встановлені драйвери NVIDIA.
        Для AMD/Intel GPU окремих кросплатформених утиліт без додаткових
        залежностей немає, тому вони не опитуються тут."""
        results = []
        nvidia_smi = shutil.which("nvidia-smi")
        if not nvidia_smi:
            return results
        try:
            proc = subprocess.run(
                [nvidia_smi, "--query-gpu=name,temperature.gpu",
                 "--format=csv,noheader,nounits"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=2, text=True,
            )
            if proc.returncode != 0:
                return results
            for i, line in enumerate(proc.stdout.strip().splitlines()):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) != 2:
                    continue
                name, temp_str = parts
                results.append({
                    "group": "nvidia_gpu",
                    "label": f"GPU {i}: {name}",
                    "current": float(temp_str),
                    "high": 85.0,
                    "critical": 95.0,
                })
        except (subprocess.TimeoutExpired, OSError, ValueError):
            pass
        return results

   # ---------- RAM ----------
    @staticmethod
    def get_ram_info():
        vm = psutil.virtual_memory()
        # Рахуємо реально використану пам'ять так, як це робить Диспетчер задач Linux
        used_gb = (vm.total - vm.available) / (1024 ** 3)
        total_gb = vm.total / (1024 ** 3)
        return {
            "used_gb": round(used_gb, 2),
            "total_gb": round(total_gb, 2),
            "percent": vm.percent,
        }
    # ---------- Disks ----------
    @staticmethod
    def get_disks_info():
        disks = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except (PermissionError, OSError):
                continue
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "percent": usage.percent,
            })
        return disks

    # ---------- Network ----------
    def get_network_speed(self):
        """Повертає (download_kbps, upload_kbps) на основі дельти від
        попереднього виклику."""
        now_counters = psutil.net_io_counters()
        now_time = time.time()

        elapsed = max(now_time - self._last_time, 1e-6)
        down_bytes = now_counters.bytes_recv - self._last_net.bytes_recv
        up_bytes = now_counters.bytes_sent - self._last_net.bytes_sent

        down_kbps = max((down_bytes / elapsed) / 1024, 0)
        up_kbps = max((up_bytes / elapsed) / 1024, 0)

        self._last_net = now_counters
        self._last_time = now_time

        return round(down_kbps, 1), round(up_kbps, 1)

    def poll_all(self):
        """Повертає єдиний знімок усіх показників за один виклик."""
        down_kbps, up_kbps = self.get_network_speed()
        return {
            "cpu_percent": self.get_cpu_percent(),
            "cpu_temp": self.get_cpu_temperature(),
            "ram": self.get_ram_info(),
            "disks": self.get_disks_info(),
            "net_down_kbps": down_kbps,
            "net_up_kbps": up_kbps,
            "all_temps": self.get_all_temperatures(),
        }