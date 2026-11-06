"""
Vaani Clinical (वाणी) — Intelligent Server Launcher
Automatically binds to port 8001 (or next available port), opens browser,
and runs FastAPI with live reload and graceful shutdown.
"""

import sys
import socket
import webbrowser
import time
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn


import urllib.request
import json


def is_vaani_running(port: int = 8001) -> bool:
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/health", headers={"User-Agent": "VaaniLauncher"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                return "Vaani Clinical" in data.get("service", "")
    except Exception:
        return False
    return False


def find_free_port(start_port: int = 8001, max_port: int = 8020) -> int:
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


def main():
    if is_vaani_running(8001):
        url = "http://127.0.0.1:8001"
        print("=" * 72)
        print("   VAANI CLINICAL -- REAL-TIME CLINICAL TELEMETRY WORKSTATION")
        print(f"   [INFO] Vaani Clinical is ALREADY active and healthy on {url}")
        print("   Opening workstation interface in your default browser...")
        print("=" * 72)
        webbrowser.open(url)
        print("\nPress Ctrl+C to close this launcher window (server stays active in background).")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return

    port = find_free_port(8001)
    url = f"http://127.0.0.1:{port}"

    print("=" * 72)
    print("   VAANI CLINICAL -- REAL-TIME CLINICAL TELEMETRY WORKSTATION")
    print(f"   Active Service URL: {url}")
    print("=" * 72)

    # Open browser after short delay
    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()
