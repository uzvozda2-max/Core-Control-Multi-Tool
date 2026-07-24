"""
network_scanner.py
Модуль сканування локальної підмережі користувача (ping sweep).
Призначений виключно для діагностики власної домашньої/робочої мережі:
визначає, які пристрої в діапазоні 1-254 відповідають на ping, і
вимірює приблизний час відгуку.
"""

import platform
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_local_subnet() -> str:
    """Визначає підмережу /24 поточного ПК, напр. '192.168.1.0/24'.
    Не покладається на зовнішні сервіси - лише локальний сокет."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Не надсилає реальних пакетів, лише визначає вихідний інтерфейс
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        finally:
            s.close()
        parts = local_ip.split(".")
        subnet = ".".join(parts[:3]) + ".0/24"
        return subnet, ".".join(parts[:3])
    except OSError:
        return "192.168.1.0/24", "192.168.1"


def _ping_once(ip: str, timeout_ms: int = 500):
    """Виконує один ICMP ping запит, крос-платформенно.
    Повертає (is_online: bool, latency_ms: float|None)."""
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    else:
        timeout_s = max(1, round(timeout_ms / 1000))
        cmd = ["ping", "-c", "1", "-W", str(timeout_s), ip]

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=(timeout_ms / 1000) + 1,
        )
        elapsed_ms = round((time.time() - start) * 1000, 1)
        is_online = result.returncode == 0
        return is_online, elapsed_ms if is_online else None
    except (subprocess.TimeoutExpired, OSError):
        return False, None


class NetworkScanner:
    """Асинхронний (потоковий) сканер локальної мережі, щоб не блокувати GUI."""

    def __init__(self, max_workers: int = 64):
        self.max_workers = max_workers
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def scan(self, subnet_prefix: str, progress_callback=None, result_callback=None):
        """Сканує IP 1-254 у заданій підмережі (напр. '192.168.1').
        Викликає progress_callback(done, total) під час прогресу та
        result_callback(ip, is_online, latency_ms) для кожної відповіді.
        Використовувати у власному потоці (threading.Thread), не в GUI-потоці."""
        self._cancelled = False
        ips = [f"{subnet_prefix}.{i}" for i in range(1, 255)]
        total = len(ips)
        done = 0
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(_ping_once, ip): ip for ip in ips}
            for future in as_completed(futures):
                if self._cancelled:
                    break
                ip = futures[future]
                try:
                    is_online, latency = future.result()
                except Exception:
                    is_online, latency = False, None

                done += 1
                if is_online and result_callback:
                    result_callback(ip, is_online, latency)
                if is_online:
                    results.append((ip, latency))
                if progress_callback:
                    progress_callback(done, total)

        results.sort(key=lambda r: tuple(int(p) for p in r[0].split(".")))
        return results