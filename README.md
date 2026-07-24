# Core-Control-Multi-Tool

A cross-platform desktop application for system monitoring, local network scanning, and quick access to system utilities. Built with Python + CustomTkinter, fully supported on Windows 10/11 and Linux (Mint/Ubuntu).
corecontrol_multitool/

      Project Structure

├── main.py              # Application entry point
├── gui.py               # GUI (CustomTkinter), 5 tabs, real-time updates
├── monitor.py           # CPU/RAM/Disks/Network polling via psutil
├── network_scanner.py   # Multi-threaded ping scanner for local subnet
├── quick_tools.py       # Launching system utilities (Win/Linux)
├── localization.py     # Translation dictionary (UA/EN/RU)
└── requirements.txt

     Running from Source
     
     pip install -r requirements.txt
     python main.py


Note for Linux users: Tkinter/CustomTkinter requires the system package python3-tk (e.g., sudo apt install python3-tk on Ubuntu/Mint). 
This is a system-level dependency of the GUI library rather than a Python package, so it cannot be installed via pip. 
It must be present on the system during development/testing (the final standalone binary does not require separate Tkinter installation by the end-user if built on the target OS).


   Building a Standalone Executable (PyInstaller)
    Windows (creates CoreControlMultiTool.exe)
    
    pip install -r requirements.txt
pyinstaller --onefile --noconsole --name CoreControlMultiTool ^
    --add-data "localization.py;." ^
    main.py

    Linux (creates CoreControlMultiTool binary)

  
    pip install -r requirements.txt
pyinstaller --onefile --noconsole --name CoreControlMultiTool \
    --add-data "localization.py:." \
    main.py


  The output executable will appear in the dist/ directory. It is completely standalone — the target machine does not need Python, psutil, or CustomTkinter installed.

Important: PyInstaller does not support cross-compilation. To obtain both .exe and Linux binary files, run the build command on Windows and Linux machines respectively (or use GitHub Actions CI/CD with an OS matrix).

Features
System Monitor — CPU utilization, RAM usage, storage space, network speeds (KB/s), and automatic alerts (e.g., RAM > 90%, high CPU usage) with highlighted indicators.

Thermometer — Comprehensive hardware temperature monitor covering CPU cores, motherboard, NVMe/SSD, and GPU (NVIDIA via nvidia-smi).

Network Scanner — Subnet auto-detection (/24), multi-threaded ping scanner for .1–.254 IP range, and an active devices table with latency metrics.

Quick Tools — One-click access to Task Manager, Task Scheduler, Disk Management, and Terminal. Automatically resolves system commands for Windows and Linux (including desktop environment fallbacks for GNOME, KDE, XFCE, MATE).

Settings — On-the-fly language switching (UA/EN/RU), UI theme toggling, and application info.




Technical Notes
Update Rate: System metrics are polled every 1.5 seconds (UPDATE_INTERVAL_MS in gui.py).

Asynchronous Execution: The network scanner runs in a dedicated threading.Thread to keep the UI responsive during subnet sweeps.

Hardware Temperature Limitations: Native Windows support for psutil.sensors_temperatures() is limited. If hardware sensors are unavailable, the application gracefully handles it by displaying "N/A" or fallback notices.
