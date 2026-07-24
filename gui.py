"""
gui.py
Головний GUI модуль CoreControl MultiTool на CustomTkinter.
Темна тема, вкладковий інтерфейс, оновлення в реальному часі.
"""

import threading
import platform

import customtkinter as ctk

from localization import t, LANGUAGES, translate_sensor_label
from monitor import SystemMonitor
from network_scanner import NetworkScanner, get_local_subnet
import quick_tools

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLOR_OK = "#2ecc71"
COLOR_WARN = "#f1c40f"
COLOR_ALERT = "#e74c3c"
COLOR_MUTED = "#7f8c8d"

RAM_ALERT_THRESHOLD = 90
TEMP_ALERT_THRESHOLD = 85  # °C
UPDATE_INTERVAL_MS = 1500


def status_color(percent: float) -> str:
    if percent >= 90:
        return COLOR_ALERT
    if percent >= 70:
        return COLOR_WARN
    return COLOR_OK


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.lang = "ua"
        self.monitor = SystemMonitor()
        self.scanner = NetworkScanner()
        self._scan_thread = None
        self._alert_banner_visible = False

        self.title(t("app_title", self.lang))
        self.geometry("980x640")
        self.minsize(860, 560)

        self._build_layout()
        self._refresh_all_texts()
        self._start_monitor_loop()

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------
    def _build_layout(self):
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=12, pady=12)

        self.tab_keys = ["tab_monitor", "tab_thermometer", "tab_network", "tab_tools", "tab_settings"]
        self.tabs = {}
        for key in self.tab_keys:
            tab = self.tabview.add(t(key, self.lang))
            self.tabs[key] = tab

        self._build_monitor_tab(self.tabs["tab_monitor"])
        self._build_thermometer_tab(self.tabs["tab_thermometer"])
        self._build_network_tab(self.tabs["tab_network"])
        self._build_tools_tab(self.tabs["tab_tools"])
        self._build_settings_tab(self.tabs["tab_settings"])

        # Верхній банер сповіщень (прихований за замовчуванням)
        self.alert_banner = ctk.CTkLabel(
            self, text="", fg_color=COLOR_ALERT, text_color="white",
            corner_radius=6, height=28,
        )

    # ---------------- Monitor tab ----------------
    def _build_monitor_tab(self, tab):
        tab.grid_columnconfigure((0, 1), weight=1)

        self.lbl_cpu_title = ctk.CTkLabel(tab, font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_cpu_title.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
        self.bar_cpu = ctk.CTkProgressBar(tab, width=380)
        self.bar_cpu.grid(row=1, column=0, sticky="w", padx=16)
        self.lbl_cpu_value = ctk.CTkLabel(tab, text="0%")
        self.lbl_cpu_value.grid(row=1, column=0, sticky="e", padx=(0, 200))

        self.lbl_temp_title = ctk.CTkLabel(tab, font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_temp_title.grid(row=0, column=1, sticky="w", padx=16, pady=(16, 4))
        self.lbl_temp_value = ctk.CTkLabel(tab, text="--")
        self.lbl_temp_value.grid(row=1, column=1, sticky="w", padx=16)

        self.lbl_ram_title = ctk.CTkLabel(tab, font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_ram_title.grid(row=2, column=0, sticky="w", padx=16, pady=(20, 4))
        self.bar_ram = ctk.CTkProgressBar(tab, width=380)
        self.bar_ram.grid(row=3, column=0, sticky="w", padx=16)
        self.lbl_ram_value = ctk.CTkLabel(tab, text="0 / 0 GB")
        self.lbl_ram_value.grid(row=3, column=1, sticky="w", padx=16)

        self.lbl_net_title = ctk.CTkLabel(tab, font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_net_title.grid(row=4, column=0, sticky="w", padx=16, pady=(20, 4))
        self.lbl_net_down = ctk.CTkLabel(tab, text="↓ 0 KB/s")
        self.lbl_net_down.grid(row=5, column=0, sticky="w", padx=16)
        self.lbl_net_up = ctk.CTkLabel(tab, text="↑ 0 KB/s")
        self.lbl_net_up.grid(row=5, column=1, sticky="w", padx=16)

        self.lbl_disks_title = ctk.CTkLabel(tab, font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_disks_title.grid(row=6, column=0, sticky="w", padx=16, pady=(20, 4), columnspan=2)
        self.disks_frame = ctk.CTkScrollableFrame(tab, height=180)
        self.disks_frame.grid(row=7, column=0, columnspan=2, sticky="nsew", padx=16, pady=(0, 16))
        tab.grid_rowconfigure(7, weight=1)

    # ---------------- Thermometer tab ----------------
    def _build_thermometer_tab(self, tab):
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 8))

        self.lbl_sensors_title = ctk.CTkLabel(top, font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_sensors_title.pack(side="left")

        self.btn_refresh_sensors = ctk.CTkButton(top, width=110, command=self._render_thermometer_now)
        self.btn_refresh_sensors.pack(side="right")

        header = ctk.CTkFrame(tab, fg_color="transparent")
        header.pack(fill="x", padx=16)
        self.lbl_col_sensor = ctk.CTkLabel(header, width=260, anchor="w", font=ctk.CTkFont(weight="bold"))
        self.lbl_col_sensor.pack(side="left")
        self.lbl_col_value_th = ctk.CTkLabel(header, width=260, anchor="w", font=ctk.CTkFont(weight="bold"))
        self.lbl_col_value_th.pack(side="left")
        self.lbl_col_limit = ctk.CTkLabel(header, width=140, anchor="w", font=ctk.CTkFont(weight="bold"))
        self.lbl_col_limit.pack(side="left")

        self.sensors_frame = ctk.CTkScrollableFrame(tab)
        self.sensors_frame.pack(fill="both", expand=True, padx=16, pady=(4, 16))

        self.lbl_no_sensors = ctk.CTkLabel(self.sensors_frame, text_color=COLOR_MUTED, wraplength=760, justify="left")

    # ---------------- Network tab ----------------
    def _build_network_tab(self, tab):
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=16)

        self.lbl_subnet = ctk.CTkLabel(top, font=ctk.CTkFont(size=13))
        self.lbl_subnet.pack(side="left")

        self.btn_scan = ctk.CTkButton(top, command=self._on_scan_clicked)
        self.btn_scan.pack(side="right")

        self.scan_progress = ctk.CTkProgressBar(tab)
        self.scan_progress.set(0)
        self.scan_progress.pack(fill="x", padx=16, pady=(0, 8))

        header = ctk.CTkFrame(tab, fg_color="transparent")
        header.pack(fill="x", padx=16)
        self.lbl_col_ip = ctk.CTkLabel(header, width=200, anchor="w", font=ctk.CTkFont(weight="bold"))
        self.lbl_col_ip.pack(side="left")
        self.lbl_col_status = ctk.CTkLabel(header, width=140, anchor="w", font=ctk.CTkFont(weight="bold"))
        self.lbl_col_status.pack(side="left")
        self.lbl_col_ping = ctk.CTkLabel(header, width=140, anchor="w", font=ctk.CTkFont(weight="bold"))
        self.lbl_col_ping.pack(side="left")

        self.results_frame = ctk.CTkScrollableFrame(tab)
        self.results_frame.pack(fill="both", expand=True, padx=16, pady=(4, 16))

    # ---------------- Tools tab ----------------
    def _build_tools_tab(self, tab):
        tab.grid_columnconfigure((0, 1), weight=1)

        self.btn_taskmgr = ctk.CTkButton(tab, height=48, command=self._launch_taskmgr)
        self.btn_taskmgr.grid(row=0, column=0, sticky="ew", padx=16, pady=16)

        self.btn_scheduler = ctk.CTkButton(tab, height=48, command=self._launch_scheduler)
        self.btn_scheduler.grid(row=0, column=1, sticky="ew", padx=16, pady=16)

        self.btn_diskmgmt = ctk.CTkButton(tab, height=48, command=self._launch_diskmgmt)
        self.btn_diskmgmt.grid(row=1, column=0, sticky="ew", padx=16, pady=16)

        self.btn_terminal = ctk.CTkButton(tab, height=48, command=self._launch_terminal)
        self.btn_terminal.grid(row=1, column=1, sticky="ew", padx=16, pady=16)

        self.lbl_tools_status = ctk.CTkLabel(tab, text="", text_color=COLOR_ALERT)
        self.lbl_tools_status.grid(row=2, column=0, columnspan=2, pady=(8, 16))

    # ---------------- Settings tab ----------------
    def _build_settings_tab(self, tab):
        self.lbl_lang = ctk.CTkLabel(tab, font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_lang.pack(anchor="w", padx=16, pady=(16, 4))

        self.lang_var = ctk.StringVar(value=self.lang)
        lang_frame = ctk.CTkFrame(tab, fg_color="transparent")
        lang_frame.pack(anchor="w", padx=16)
        for code, label in (("ua", "Українська"), ("en", "English"), ("ru", "Русский")):
            ctk.CTkRadioButton(
                lang_frame, text=label, variable=self.lang_var, value=code,
                command=self._on_language_changed,
            ).pack(side="left", padx=(0, 16), pady=8)

        self.lbl_appearance = ctk.CTkLabel(tab, font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_appearance.pack(anchor="w", padx=16, pady=(20, 4))
        self.appearance_menu = ctk.CTkOptionMenu(
            tab, values=["Dark", "Light", "System"], command=self._on_appearance_changed,
        )
        self.appearance_menu.pack(anchor="w", padx=16)

        self.lbl_about_title = ctk.CTkLabel(tab, font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_about_title.pack(anchor="w", padx=16, pady=(24, 4))
        self.lbl_about_text = ctk.CTkLabel(tab, wraplength=700, justify="left")
        self.lbl_about_text.pack(anchor="w", padx=16)

        # Промо-банер у підвалі
        self.lbl_promo = ctk.CTkLabel(tab, text_color=COLOR_MUTED, font=ctk.CTkFont(size=11, slant="italic"))
        self.lbl_promo.pack(side="bottom", pady=12)

    # ------------------------------------------------------------------
    # Text refresh (on language switch)
    # ------------------------------------------------------------------
    def _refresh_all_texts(self):
        self.title(t("app_title", self.lang))
        for key in self.tab_keys:
            old_name = self._current_tab_name(key)
            new_name = t(key, self.lang)
            if old_name != new_name:
                self.tabview.rename(old_name, new_name)
        self._cached_tab_names = {key: t(key, self.lang) for key in self.tab_keys}

        self.lbl_cpu_title.configure(text=t("cpu_load", self.lang))
        self.lbl_temp_title.configure(text=t("cpu_temp", self.lang))
        self.lbl_ram_title.configure(text=t("ram_usage", self.lang))
        self.lbl_net_title.configure(text=t("network_speed", self.lang))
        self.lbl_disks_title.configure(text=t("disks", self.lang))

        self.lbl_sensors_title.configure(text=t("sensors_title", self.lang))
        self.btn_refresh_sensors.configure(text=t("refresh_button", self.lang))
        self.lbl_col_sensor.configure(text=t("col_sensor", self.lang))
        self.lbl_col_value_th.configure(text=t("col_value", self.lang))
        self.lbl_col_limit.configure(text=t("col_limit", self.lang))
        self._render_thermometer_now()

        self.btn_scan.configure(text=t("scan_button", self.lang))
        self.lbl_col_ip.configure(text=t("col_ip", self.lang))
        self.lbl_col_status.configure(text=t("col_status", self.lang))
        self.lbl_col_ping.configure(text=t("col_ping", self.lang))
        self._update_subnet_label()

        self.btn_taskmgr.configure(text=t("tool_taskmgr", self.lang))
        self.btn_scheduler.configure(text=t("tool_scheduler", self.lang))
        self.btn_diskmgmt.configure(text=t("tool_diskmgmt", self.lang))
        self.btn_terminal.configure(text=t("tool_terminal", self.lang))

        self.lbl_lang.configure(text=t("language_label", self.lang))
        self.lbl_appearance.configure(text=t("appearance_label", self.lang))
        self.lbl_about_title.configure(text=t("about_label", self.lang))
        self.lbl_about_text.configure(text=t("about_text", self.lang))
        self.lbl_promo.configure(text=t("promo_banner", self.lang))

    def _current_tab_name(self, key):
        return getattr(self, "_cached_tab_names", {}).get(key, t(key, "ua"))

    def _update_subnet_label(self):
        subnet_cidr, _ = get_local_subnet()
        self.lbl_subnet.configure(text=f"{t('current_subnet', self.lang)}: {subnet_cidr}")

    # ------------------------------------------------------------------
    # Language / appearance callbacks
    # ------------------------------------------------------------------
    def _on_language_changed(self):
        self.lang = self.lang_var.get()
        self._refresh_all_texts()

    def _on_appearance_changed(self, choice: str):
        ctk.set_appearance_mode(choice.lower())

    # ------------------------------------------------------------------
    # Monitor loop
    # ------------------------------------------------------------------
    def _start_monitor_loop(self):
        self._poll_monitor()

    def _poll_monitor(self):
        data = self.monitor.poll_all()
        self._render_monitor(data)
        self.after(UPDATE_INTERVAL_MS, self._poll_monitor)

    def _render_monitor(self, data):
        cpu = data["cpu_percent"]
        self.bar_cpu.set(cpu / 100)
        self.bar_cpu.configure(progress_color=status_color(cpu))
        self.lbl_cpu_value.configure(text=f"{cpu:.0f}%")

        temp = data["cpu_temp"]
        if temp is None:
            self.lbl_temp_value.configure(text=t("temp_unavailable", self.lang), text_color=COLOR_MUTED)
        else:
            color = COLOR_ALERT if temp >= TEMP_ALERT_THRESHOLD else (
                COLOR_WARN if temp >= TEMP_ALERT_THRESHOLD - 15 else COLOR_OK
            )
            self.lbl_temp_value.configure(text=f"{temp:.0f}°C", text_color=color)

        ram = data["ram"]
        self.bar_ram.set(ram["percent"] / 100)
        self.bar_ram.configure(progress_color=status_color(ram["percent"]))
        self.lbl_ram_value.configure(
            text=f"{ram['used_gb']} / {ram['total_gb']} GB ({ram['percent']}%)"
        )

        self.lbl_net_down.configure(text=f"↓ {t('download', self.lang)}: {data['net_down_kbps']} KB/s")
        self.lbl_net_up.configure(text=f"↑ {t('upload', self.lang)}: {data['net_up_kbps']} KB/s")

        self._render_disks(data["disks"])
        self._render_thermometer(data["all_temps"])
        self._evaluate_alerts(ram["percent"], temp)

    def _render_disks(self, disks):
        for child in self.disks_frame.winfo_children():
            child.destroy()
        for disk in disks:
            row = ctk.CTkFrame(self.disks_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            label = ctk.CTkLabel(row, text=f"{disk['device']} ({disk['mountpoint']})", width=220, anchor="w")
            label.pack(side="left")
            bar = ctk.CTkProgressBar(row, width=260)
            bar.set(disk["percent"] / 100)
            bar.configure(progress_color=status_color(disk["percent"]))
            bar.pack(side="left", padx=8)
            value = ctk.CTkLabel(row, text=f"{disk['used_gb']} / {disk['total_gb']} GB ({disk['percent']}%)")
            value.pack(side="left")

    def _render_thermometer_now(self):
        """Ручне негайне оновлення списку датчиків за кнопкою."""
        self._render_thermometer(self.monitor.get_all_temperatures())

    def _render_thermometer(self, sensors):
        for child in self.sensors_frame.winfo_children():
            child.destroy()

        if not sensors:
            self.lbl_no_sensors = ctk.CTkLabel(
                self.sensors_frame, text=t("no_sensors", self.lang),
                text_color=COLOR_MUTED, wraplength=760, justify="left",
            )
            self.lbl_no_sensors.pack(anchor="w", pady=8)
            return

        for sensor in sensors:
            current = sensor["current"]
            critical = sensor.get("critical")
            high = sensor.get("high")

            # Визначаємо колір: за critical/high від датчика, або дефолтні пороги
            if critical:
                ratio = current / critical
            elif high:
                ratio = current / (high * 1.15)
            else:
                ratio = current / 100

            if ratio >= 0.95:
                color = COLOR_ALERT
            elif ratio >= 0.75:
                color = COLOR_WARN
            else:
                color = COLOR_OK

            row = ctk.CTkFrame(self.sensors_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            group_label = translate_sensor_label(sensor["group"], sensor["label"], self.lang)
            ctk.CTkLabel(row, text=group_label, width=260, anchor="w").pack(side="left")

            value_frame = ctk.CTkFrame(row, fg_color="transparent", width=260)
            value_frame.pack(side="left")
            bar = ctk.CTkProgressBar(value_frame, width=160)
            bar.set(min(max(ratio, 0), 1))
            bar.configure(progress_color=color)
            bar.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(value_frame, text=f"{current:.0f}°C", text_color=color, width=60, anchor="w").pack(side="left")

            limit_text = f"{critical:.0f}°C" if critical else (f"{high:.0f}°C" if high else "--")
            ctk.CTkLabel(row, text=limit_text, width=140, anchor="w", text_color=COLOR_MUTED).pack(side="left")

    def _evaluate_alerts(self, ram_percent, temp):
        messages = []
        if ram_percent >= RAM_ALERT_THRESHOLD:
            messages.append(t("alert_ram", self.lang))
        if temp is not None and temp >= TEMP_ALERT_THRESHOLD:
            messages.append(t("alert_temp", self.lang))

        if messages:
            self.alert_banner.configure(text="  ⚠  " + "   |   ".join(messages))
            if not self._alert_banner_visible:
                self.alert_banner.pack(fill="x", side="top", before=self.tabview)
                self._alert_banner_visible = True
        elif self._alert_banner_visible:
            self.alert_banner.pack_forget()
            self._alert_banner_visible = False

    # ------------------------------------------------------------------
    # Network scan
    # ------------------------------------------------------------------
    def _on_scan_clicked(self):
        if self._scan_thread and self._scan_thread.is_alive():
            return
        for child in self.results_frame.winfo_children():
            child.destroy()
        self.scan_progress.set(0)
        self.btn_scan.configure(text=t("scanning", self.lang), state="disabled")

        _, subnet_prefix = get_local_subnet()
        self._scan_thread = threading.Thread(
            target=self._run_scan, args=(subnet_prefix,), daemon=True,
        )
        self._scan_thread.start()

    def _run_scan(self, subnet_prefix):
        def on_progress(done, total):
            self.after(0, lambda: self.scan_progress.set(done / total))

        def on_result(ip, is_online, latency):
            self.after(0, lambda: self._add_scan_result_row(ip, latency))

        self.scanner.scan(subnet_prefix, progress_callback=on_progress, result_callback=on_result)
        self.after(0, self._on_scan_finished)

    def _add_scan_result_row(self, ip, latency):
        row = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        row.pack(fill="x", pady=1)
        ctk.CTkLabel(row, text=ip, width=200, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=t("status_online", self.lang), width=140, anchor="w", text_color=COLOR_OK).pack(side="left")
        ping_text = f"{latency} ms" if latency is not None else "--"
        ctk.CTkLabel(row, text=ping_text, width=140, anchor="w").pack(side="left")

    def _on_scan_finished(self):
        self.btn_scan.configure(text=t("scan_button", self.lang), state="normal")

    # ------------------------------------------------------------------
    # Quick tools
    # ------------------------------------------------------------------
    def _launch_and_report(self, func):
        success, error = func()
        if not success:
            self.lbl_tools_status.configure(text=f"{t('tool_launch_failed', self.lang)}: {error}")
        else:
            self.lbl_tools_status.configure(text="")

    def _launch_taskmgr(self):
        self._launch_and_report(quick_tools.open_task_manager)

    def _launch_scheduler(self):
        self._launch_and_report(quick_tools.open_task_scheduler)

    def _launch_diskmgmt(self):
        self._launch_and_report(quick_tools.open_disk_management)

    def _launch_terminal(self):
        self._launch_and_report(lambda: quick_tools.open_terminal())