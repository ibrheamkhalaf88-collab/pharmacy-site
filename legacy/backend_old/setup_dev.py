"""ת הרץ את הפרויקט הזה לאחר תקינת התלויות."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
VENV_DIR = PROJECT_ROOT / "venv"
REQUIREMENTS = PROJECT_ROOT / "backend" / "requirements.txt"

def ensure_venv():
    if VENV_DIR.exists():
        return VENV_DIR / "Scripts" / "python.exe"
    print("⚡ creating virtualenv...")
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    return VENV_DIR / "Scripts" / "python.exe"

def install_deps(python_exe):
    print("📦 installing dependencies...")
    subprocess.run([str(python_exe), "-m", "pip", "install", "-r", str(REQUIREMENTS)], check=True)

def run():
    python_exe = ensure_venv()
    install_deps(python_exe)
    print("\n✅ dependencies installed. starting server...\n")
    subprocess.run([str(python_exe), "run.py"], cwd=str(PROJECT_ROOT))

if __name__ == "__main__":
    run()
