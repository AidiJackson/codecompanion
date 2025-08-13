import os
import socket
import time
import threading
import uvicorn
from contextlib import closing

LOCK_FILE = ".api5050.lock"


def _port_in_use(host: str, port: int) -> bool:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) == 0


def start_api_once():
    """
    Start FastAPI app 'api:app' on 0.0.0.0:5050 at most once.
    Uses:
      - quick port check
      - a lock file to prevent double-start across Streamlit reruns
    """
    host, port = "0.0.0.0", 5050

    # If already listening, do nothing
    if _port_in_use(host, port):
        return

    # Lock file guard
    if os.path.exists(LOCK_FILE):
        # Another thread/process is likely booting it
        # Wait up to 5s for it to be ready
        for _ in range(25):
            if _port_in_use(host, port):
                return
            time.sleep(0.2)
        # If still not up, remove stale lock and continue
        try:
            os.remove(LOCK_FILE)
        except Exception:
            pass

    # Create lock
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

    def _run():
        try:
            uvicorn.run("api:app", host=host, port=port, log_level="info")
        finally:
            # When uvicorn stops, remove lock
            try:
                os.remove(LOCK_FILE)
            except Exception:
                pass

    # Start in background daemon thread
    t = threading.Thread(target=_run, daemon=True)
    t.start()

    # Poll for readiness so UI can proceed
    for _ in range(50):
        if _port_in_use(host, port):
            return
        time.sleep(0.1)
