import os
import subprocess

APP_FILE = "app.py"

def stop_app():
    """Stops the running app.py process."""
    print(f"Stopping {APP_FILE}...")

    if os.name == "nt":  # Windows
        subprocess.call('taskkill /F /IM python.exe', shell=True)
    else:  # Linux/macOS
        subprocess.call(f"pkill -f {APP_FILE}", shell=True)

    print(f"{APP_FILE} has been stopped successfully!")

if __name__ == "__main__":
    stop_app()
